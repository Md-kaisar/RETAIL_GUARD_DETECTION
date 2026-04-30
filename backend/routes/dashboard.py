from fastapi import APIRouter, Depends, Query
from typing import List
from datetime import datetime, timedelta
from database import get_db
from models.schemas import DashboardStats, AuditLogOut, AlertOut
from services.auth import get_current_user, require_admin

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard(current_user=Depends(get_current_user)):
    db = get_db()
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    total_transactions = await db.transactions.count_documents({})
    flagged_today = await db.transactions.count_documents({
        "status": "flagged",
        "timestamp": {"$gte": today_start},
    })
    active_cases = await db.cases.count_documents({"status": {"$in": ["open", "in_progress"]}})
    new_alerts = await db.alerts.count_documents({"status": "new"})

    # Fraud rate & total fraud amount
    fraud_cursor = db.transactions.aggregate([
        {"$group": {
            "_id": None,
            "total": {"$sum": 1},
            "fraud_count": {"$sum": {"$cond": [{"$eq": ["$status", "flagged"]}, 1, 0]}},
            "fraud_amount": {"$sum": {"$cond": [{"$eq": ["$status", "flagged"]}, "$amount", 0]}},
            "scored_count": {"$sum": {"$cond": [{"$ne": ["$risk_score", None]}, 1, 0]}},
            "total_score": {"$sum": {"$ifNull": ["$risk_score", 0]}},
        }}
    ])
    agg = await fraud_cursor.to_list(length=1)
    agg = agg[0] if agg else {}
    total = agg.get("total", 1) or 1
    fraud_rate = agg.get("fraud_count", 0) / total
    total_fraud_amount = agg.get("fraud_amount", 0)
    scored = agg.get("scored_count", 1) or 1
    avg_risk = agg.get("total_score", 0) / scored

    # Transactions by day (last 14 days)
    pipeline_days = [
        {"$match": {"timestamp": {"$gte": now - timedelta(days=14)}}},
        {"$group": {
            "_id": {
                "year": {"$year": "$timestamp"},
                "month": {"$month": "$timestamp"},
                "day": {"$dayOfMonth": "$timestamp"},
            },
            "count": {"$sum": 1},
            "flagged": {"$sum": {"$cond": [{"$eq": ["$status", "flagged"]}, 1, 0]}},
        }},
        {"$sort": {"_id.year": 1, "_id.month": 1, "_id.day": 1}},
    ]
    days_data = await db.transactions.aggregate(pipeline_days).to_list(length=14)
    transactions_by_day = [
        {
            "date": f"{d['_id']['year']}-{d['_id']['month']:02d}-{d['_id']['day']:02d}",
            "count": d["count"],
            "flagged": d["flagged"],
        }
        for d in days_data
    ]

    # Risk distribution buckets
    buckets = [
        ("Low (0–0.3)", 0, 0.3),
        ("Medium (0.3–0.6)", 0.3, 0.6),
        ("High (0.6–0.8)", 0.6, 0.8),
        ("Critical (0.8–1)", 0.8, 1.01),
    ]
    risk_distribution = []
    for label, lo, hi in buckets:
        count = await db.transactions.count_documents({
            "risk_score": {"$gte": lo, "$lt": hi}
        })
        risk_distribution.append({"label": label, "count": count})

    # Top merchants by flagged transactions
    merchant_pipeline = [
        {"$match": {"status": "flagged"}},
        {"$group": {"_id": "$merchant_name", "count": {"$sum": 1}, "total_amount": {"$sum": "$amount"}}},
        {"$sort": {"count": -1}},
        {"$limit": 5},
    ]
    top_merchants = [
        {"name": m["_id"] or "Unknown", "count": m["count"], "total_amount": m["total_amount"]}
        for m in await db.transactions.aggregate(merchant_pipeline).to_list(length=5)
    ]

    # Recent alerts
    recent_alerts_raw = await db.alerts.find({}).sort("triggered_at", -1).limit(5).to_list(length=5)
    recent_alerts = [AlertOut(**a) for a in recent_alerts_raw]

    return DashboardStats(
        total_transactions=total_transactions,
        flagged_today=flagged_today,
        active_cases=active_cases,
        new_alerts=new_alerts,
        fraud_rate=round(fraud_rate, 4),
        total_fraud_amount=round(total_fraud_amount, 2),
        avg_risk_score=round(avg_risk, 4),
        transactions_by_day=transactions_by_day,
        risk_distribution=risk_distribution,
        top_merchants=top_merchants,
        recent_alerts=recent_alerts,
    )


@router.get("/audit-logs", response_model=List[AuditLogOut])
async def list_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user=Depends(require_admin),
):
    db = get_db()
    cursor = db.audit_logs.find({}).sort("timestamp", -1).skip(skip).limit(limit)
    logs = await cursor.to_list(length=limit)
    result = []
    for log in logs:
        user = await db.users.find_one({"id": log.get("user_id", "")})
        log["user_name"] = user["name"] if user else "Unknown"
        result.append(AuditLogOut(**log))
    return result
