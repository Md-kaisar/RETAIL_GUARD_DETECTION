from fastapi import APIRouter, HTTPException, Depends, status
from datetime import datetime
import uuid
from database import get_db
from models.schemas import UserCreate, UserOut, Token, LoginRequest, UserRole
from services.auth import hash_password, verify_password, create_access_token, get_current_user
from services.audit import log_action

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=201)
async def register(payload: UserCreate):
    db = get_db()
    existing = await db.users.find_one({"email": payload.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = {
        "id": str(uuid.uuid4()),
        "name": payload.name,
        "email": payload.email,
        "password_hash": hash_password(payload.password),
        "role": payload.role.value,
        "is_active": True,
        "created_at": datetime.utcnow(),
    }
    await db.users.insert_one(user)
    await log_action(user["id"], "USER_REGISTERED", {"email": payload.email, "role": payload.role.value})
    return UserOut(**user)


@router.post("/login", response_model=Token)
async def login(payload: LoginRequest):
    db = get_db()
    user = await db.users.find_one({"email": payload.email})
    if not user or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.get("is_active", True):
        raise HTTPException(status_code=400, detail="Account disabled")

    token = create_access_token({"sub": user["id"], "role": user["role"]})
    await log_action(user["id"], "USER_LOGIN", {"email": user["email"]})
    return Token(
        access_token=token,
        token_type="bearer",
        user=UserOut(**user),
    )


@router.get("/me", response_model=UserOut)
async def me(current_user=Depends(get_current_user)):
    return UserOut(**current_user)
