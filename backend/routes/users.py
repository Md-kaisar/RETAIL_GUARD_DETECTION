from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List
from database import get_db
from models.schemas import UserOut, UserUpdate
from services.auth import get_current_user, require_admin
from services.audit import log_action

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=List[UserOut])
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user=Depends(require_admin),
):
    db = get_db()
    cursor = db.users.find({}).skip(skip).limit(limit)
    users = await cursor.to_list(length=limit)
    return [UserOut(**u) for u in users]


@router.get("/{user_id}", response_model=UserOut)
async def get_user(user_id: str, current_user=Depends(get_current_user)):
    if current_user["id"] != user_id and current_user["role"] != "admin":
        raise HTTPException(403, "Access denied")
    db = get_db()
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(404, "User not found")
    return UserOut(**user)


@router.patch("/{user_id}", response_model=UserOut)
async def update_user(user_id: str, payload: UserUpdate, current_user=Depends(require_admin)):
    db = get_db()
    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    if "role" in updates:
        updates["role"] = updates["role"].value
    result = await db.users.update_one({"id": user_id}, {"$set": updates})
    if result.matched_count == 0:
        raise HTTPException(404, "User not found")
    user = await db.users.find_one({"id": user_id})
    await log_action(current_user["id"], "USER_UPDATED", {"target_user_id": user_id})
    return UserOut(**user)


@router.delete("/{user_id}")
async def deactivate_user(user_id: str, current_user=Depends(require_admin)):
    if current_user["id"] == user_id:
        raise HTTPException(400, "Cannot deactivate yourself")
    db = get_db()
    result = await db.users.update_one({"id": user_id}, {"$set": {"is_active": False}})
    if result.matched_count == 0:
        raise HTTPException(404, "User not found")
    await log_action(current_user["id"], "USER_DEACTIVATED", {"target_user_id": user_id})
    return {"message": "User deactivated"}
