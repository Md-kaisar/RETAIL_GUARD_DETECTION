from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from database import get_db
from models.schemas import AlertOut, AlertUpdate, AlertStatus
from services.auth import get_current_user
from services.audit import log_action

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=List[AlertOut])
async def list_alerts(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status: Optional[str] = None,
    current_user=Depends(get_current_user),
):
    db = get_db()
    query = {}
    if status:
        query["status"] = status
    cursor = db.alerts.find(query).sort("triggered_at", -1).skip(skip).limit(limit)
    alerts = await cursor.to_list(length=limit)
    return [AlertOut(**a) for a in alerts]


@router.get("/count")
async def alert_count(current_user=Depends(get_current_user)):
    db = get_db()
    total = await db.alerts.count_documents({})
    new = await db.alerts.count_documents({"status": AlertStatus.new.value})
    return {"total": total, "new": new}


@router.get("/{alert_id}", response_model=AlertOut)
async def get_alert(alert_id: str, current_user=Depends(get_current_user)):
    db = get_db()
    alert = await db.alerts.find_one({"id": alert_id})
    if not alert:
        raise HTTPException(404, "Alert not found")
    return AlertOut(**alert)


@router.patch("/{alert_id}", response_model=AlertOut)
async def update_alert(alert_id: str, payload: AlertUpdate, current_user=Depends(get_current_user)):
    db = get_db()
    result = await db.alerts.update_one(
        {"id": alert_id}, {"$set": {"status": payload.status.value}}
    )
    if result.matched_count == 0:
        raise HTTPException(404, "Alert not found")
    alert = await db.alerts.find_one({"id": alert_id})
    await log_action(current_user["id"], "ALERT_UPDATED", {
        "alert_id": alert_id, "status": payload.status.value
    })
    return AlertOut(**alert)
