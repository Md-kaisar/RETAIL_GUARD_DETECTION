from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import List, Optional
from datetime import datetime
import uuid
import json
import csv
import io
import logging

from database import get_db
from models.schemas import (
    TransactionOut, TransactionSummary, TransactionStatus, AlertType, AlertStatus
)
from services.auth import get_current_user, require_analyst_or_above
from services.audit import log_action
from services.notifications import send_alert_email
from ml.detector import get_detector
from config import settings

router = APIRouter(prefix="/transactions", tags=["transactions"])
logger = logging.getLogger(__name__)


def _build_txn_doc(raw: dict) -> dict:
    """Normalize a raw dict to a transaction document."""
    txn_id = raw.get("id") or str(uuid.uuid4())
    amount = float(raw.get("amount", 0))
    ts_raw = raw.get("timestamp")
    if isinstance(ts_raw, str):
        try:
            timestamp = datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
        except Exception:
            timestamp = datetime.utcnow()
    elif isinstance(ts_raw, datetime):
        timestamp = ts_raw
    else:
        timestamp = datetime.utcnow()

    features = raw.get("features", {}) or {}
    # Auto-populate features from top-level fields if missing
    if not features.get("hour_of_day"):
        features["hour_of_day"] = timestamp.hour
    if not features.get("day_of_week"):
        features["day_of_week"] = timestamp.weekday()

    return {
        "id": txn_id,
        "timestamp": timestamp,
        "amount": amount,
        "merchant_id": str(raw.get("merchant_id", "UNKNOWN")),
        "merchant_name": raw.get("merchant_name", raw.get("merchant_id", "Unknown")),
        "merchant_category": raw.get("merchant_category", "Other"),
        "user_id": str(raw.get("user_id", "UNKNOWN")),
        "location": raw.get("location", ""),
        "features": features,
        "risk_score": None,
        "status": TransactionStatus.pending.value,
        "created_at": datetime.utcnow(),
    }


async def _score_and_flag(txn_doc: dict, db, user_id: str):
    detector = get_detector()
    try:
        score = detector.score_transaction(txn_doc)
        txn_doc["risk_score"] = score
        if score >= settings.FRAUD_THRESHOLD:
            txn_doc["status"] = TransactionStatus.flagged.value
            # Create alert
            alert = {
                "id": str(uuid.uuid4()),
                "transaction_id": txn_doc["id"],
                "triggered_at": datetime.utcnow(),
                "type": AlertType.fraud.value,
                "status": AlertStatus.new.value,
                "risk_score": score,
                "amount": txn_doc["amount"],
                "merchant_name": txn_doc.get("merchant_name", ""),
                "user_id": txn_doc["user_id"],
            }
            await db.alerts.insert_one(alert)
            # Fire-and-forget email
            import asyncio
            asyncio.create_task(send_alert_email(
                txn_doc["id"], txn_doc["amount"], score,
                txn_doc.get("merchant_name", txn_doc["merchant_id"])
            ))
        else:
            txn_doc["status"] = TransactionStatus.cleared.value
    except Exception as e:
        logger.error(f"Scoring failed for {txn_doc['id']}: {e}")
        txn_doc["status"] = TransactionStatus.unscored.value
        txn_doc["risk_score"] = None
    return txn_doc


@router.post("/upload", summary="Upload CSV or JSON transaction file")
async def upload_transactions(
    file: UploadFile = File(...),
    current_user=Depends(require_analyst_or_above),
):
    db = get_db()
    content = await file.read()

    transactions = []
    if file.filename.endswith(".json"):
        try:
            data = json.loads(content)
            if isinstance(data, list):
                transactions = data
            elif isinstance(data, dict):
                transactions = data.get("transactions", [data])
        except json.JSONDecodeError:
            raise HTTPException(400, "Invalid JSON file")
    elif file.filename.endswith(".csv"):
        try:
            reader = csv.DictReader(io.StringIO(content.decode("utf-8")))
            transactions = list(reader)
        except Exception:
            raise HTTPException(400, "Invalid CSV file")
    else:
        raise HTTPException(400, "Only .csv and .json files are supported")

    if not transactions:
        raise HTTPException(400, "No transactions found in file")

    processed, flagged, errors = 0, 0, 0
    docs = []

    for raw in transactions:
        try:
            txn_doc = _build_txn_doc(raw if isinstance(raw, dict) else dict(raw))
            txn_doc = await _score_and_flag(txn_doc, db, current_user["id"])
            if txn_doc["status"] == TransactionStatus.flagged.value:
                flagged += 1
            docs.append(txn_doc)
            processed += 1
        except Exception as e:
            logger.error(f"Error processing transaction: {e}")
            errors += 1

    if docs:
        await db.transactions.insert_many(docs, ordered=False)

    await log_action(current_user["id"], "TRANSACTIONS_UPLOADED", {
        "filename": file.filename,
        "total": len(transactions),
        "processed": processed,
        "flagged": flagged,
        "errors": errors,
    })

    return {
        "message": f"Processed {processed} transactions",
        "total": len(transactions),
        "processed": processed,
        "flagged": flagged,
        "errors": errors,
    }


@router.get("", response_model=List[TransactionOut])
async def list_transactions(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status: Optional[str] = None,
    min_score: Optional[float] = None,
    max_score: Optional[float] = None,
    user_id: Optional[str] = None,
    current_user=Depends(get_current_user),
):
    db = get_db()
    query = {}
    if status:
        query["status"] = status
    if min_score is not None:
        query.setdefault("risk_score", {})["$gte"] = min_score
    if max_score is not None:
        query.setdefault("risk_score", {})["$lte"] = max_score
    if user_id:
        query["user_id"] = user_id

    cursor = db.transactions.find(query).sort("timestamp", -1).skip(skip).limit(limit)
    txns = await cursor.to_list(length=limit)
    return [TransactionOut(**t) for t in txns]


@router.get("/summary", response_model=TransactionSummary)
async def transaction_summary(current_user=Depends(get_current_user)):
    db = get_db()
    pipeline = [
        {"$group": {
            "_id": "$status",
            "count": {"$sum": 1},
            "total_score": {"$sum": {"$ifNull": ["$risk_score", 0]}},
            "scored_count": {"$sum": {"$cond": [{"$ne": ["$risk_score", None]}, 1, 0]}},
        }}
    ]
    results = await db.transactions.aggregate(pipeline).to_list(length=20)
    counts = {r["_id"]: r["count"] for r in results}
    total_scored = sum(r["scored_count"] for r in results)
    total_score = sum(r["total_score"] for r in results)

    return TransactionSummary(
        total=sum(counts.values()),
        flagged=counts.get("flagged", 0),
        cleared=counts.get("cleared", 0),
        fraud=counts.get("fraud", 0),
        pending=counts.get("pending", 0),
        unscored=counts.get("unscored", 0),
        avg_risk_score=round(total_score / max(total_scored, 1), 4),
    )


@router.get("/{txn_id}", response_model=TransactionOut)
async def get_transaction(txn_id: str, current_user=Depends(get_current_user)):
    db = get_db()
    txn = await db.transactions.find_one({"id": txn_id})
    if not txn:
        raise HTTPException(404, "Transaction not found")
    return TransactionOut(**txn)


@router.patch("/{txn_id}/status")
async def update_transaction_status(
    txn_id: str,
    status: TransactionStatus,
    current_user=Depends(get_current_user),
):
    db = get_db()
    result = await db.transactions.update_one(
        {"id": txn_id}, {"$set": {"status": status.value}}
    )
    if result.matched_count == 0:
        raise HTTPException(404, "Transaction not found")
    await log_action(current_user["id"], "TRANSACTION_STATUS_UPDATED", {
        "transaction_id": txn_id, "new_status": status.value
    })
    return {"message": "Status updated"}
