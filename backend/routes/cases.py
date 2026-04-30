from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from datetime import datetime
import uuid

from database import get_db
from models.schemas import CaseCreate, CaseUpdate, CaseAddComment, CaseOut, CaseComment, CaseStatus
from services.auth import get_current_user
from services.audit import log_action

router = APIRouter(prefix="/cases", tags=["cases"])


async def _enrich_case(case: dict, db) -> dict:
    if case.get("assigned_to"):
        u = await db.users.find_one({"id": case["assigned_to"]})
        case["assigned_to_name"] = u["name"] if u else "Unknown"
    else:
        case["assigned_to_name"] = None
    creator = await db.users.find_one({"id": case.get("created_by", "")})
    case["created_by_name"] = creator["name"] if creator else "Unknown"
    return case


@router.post("", response_model=CaseOut, status_code=201)
async def create_case(payload: CaseCreate, current_user=Depends(get_current_user)):
    db = get_db()
    case = {
        "id": str(uuid.uuid4()),
        "title": payload.title,
        "transaction_ids": payload.transaction_ids,
        "assigned_to": payload.assigned_to,
        "status": CaseStatus.open.value,
        "description": payload.description,
        "comments": [],
        "created_by": current_user["id"],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }
    await db.cases.insert_one(case)
    await log_action(current_user["id"], "CASE_CREATED", {
        "case_id": case["id"], "title": payload.title
    })
    return CaseOut(**await _enrich_case(case, db))


@router.get("", response_model=List[CaseOut])
async def list_cases(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[str] = None,
    assigned_to: Optional[str] = None,
    current_user=Depends(get_current_user),
):
    db = get_db()
    query = {}
    if status:
        query["status"] = status
    if assigned_to:
        query["assigned_to"] = assigned_to

    cursor = db.cases.find(query).sort("created_at", -1).skip(skip).limit(limit)
    cases = await cursor.to_list(length=limit)
    result = []
    for c in cases:
        result.append(CaseOut(**await _enrich_case(c, db)))
    return result


@router.get("/{case_id}", response_model=CaseOut)
async def get_case(case_id: str, current_user=Depends(get_current_user)):
    db = get_db()
    case = await db.cases.find_one({"id": case_id})
    if not case:
        raise HTTPException(404, "Case not found")
    return CaseOut(**await _enrich_case(case, db))


@router.patch("/{case_id}", response_model=CaseOut)
async def update_case(case_id: str, payload: CaseUpdate, current_user=Depends(get_current_user)):
    db = get_db()
    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(400, "No updates provided")
    if "status" in updates:
        updates["status"] = updates["status"].value
    updates["updated_at"] = datetime.utcnow()
    result = await db.cases.update_one({"id": case_id}, {"$set": updates})
    if result.matched_count == 0:
        raise HTTPException(404, "Case not found")
    case = await db.cases.find_one({"id": case_id})
    await log_action(current_user["id"], "CASE_UPDATED", {"case_id": case_id, "updates": list(updates.keys())})
    return CaseOut(**await _enrich_case(case, db))


@router.post("/{case_id}/comments", response_model=CaseOut)
async def add_comment(case_id: str, payload: CaseAddComment, current_user=Depends(get_current_user)):
    db = get_db()
    comment = CaseComment(
        author_id=current_user["id"],
        author_name=current_user["name"],
        content=payload.content,
    )
    result = await db.cases.update_one(
        {"id": case_id},
        {
            "$push": {"comments": comment.model_dump()},
            "$set": {"updated_at": datetime.utcnow()},
        },
    )
    if result.matched_count == 0:
        raise HTTPException(404, "Case not found")
    case = await db.cases.find_one({"id": case_id})
    await log_action(current_user["id"], "CASE_COMMENT_ADDED", {"case_id": case_id})
    return CaseOut(**await _enrich_case(case, db))


@router.delete("/{case_id}")
async def delete_case(case_id: str, current_user=Depends(get_current_user)):
    db = get_db()
    result = await db.cases.delete_one({"id": case_id})
    if result.deleted_count == 0:
        raise HTTPException(404, "Case not found")
    await log_action(current_user["id"], "CASE_DELETED", {"case_id": case_id})
    return {"message": "Case deleted"}
