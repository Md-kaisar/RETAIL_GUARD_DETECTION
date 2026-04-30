from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import uuid


# ── Enums ──────────────────────────────────────────────────────────────────────

class UserRole(str, Enum):
    admin = "admin"
    analyst = "analyst"
    investigator = "investigator"


class TransactionStatus(str, Enum):
    pending = "pending"
    flagged = "flagged"
    cleared = "cleared"
    fraud = "fraud"
    unscored = "unscored"


class CaseStatus(str, Enum):
    open = "open"
    in_progress = "in_progress"
    resolved = "resolved"
    closed = "closed"


class AlertType(str, Enum):
    fraud = "FRAUD"
    suspicious = "SUSPICIOUS"
    anomaly = "ANOMALY"


class AlertStatus(str, Enum):
    new = "new"
    acknowledged = "acknowledged"
    resolved = "resolved"


# ── User ───────────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: UserRole = UserRole.analyst


class UserUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class UserOut(BaseModel):
    id: str
    name: str
    email: str
    role: UserRole
    is_active: bool
    created_at: datetime


class UserInDB(UserOut):
    password_hash: str


# ── Auth ───────────────────────────────────────────────────────────────────────

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserOut


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


# ── Transaction ────────────────────────────────────────────────────────────────

class TransactionFeatures(BaseModel):
    amount: float
    merchant_category: Optional[str] = None
    hour_of_day: Optional[int] = None
    day_of_week: Optional[int] = None
    customer_age_days: Optional[int] = None
    num_txn_last_24h: Optional[int] = None
    avg_txn_amount_30d: Optional[float] = None
    distance_from_home: Optional[float] = None
    is_online: Optional[bool] = None
    is_foreign: Optional[bool] = None


class TransactionIn(BaseModel):
    id: Optional[str] = None
    timestamp: Optional[datetime] = None
    amount: float
    merchant_id: str
    user_id: str
    merchant_name: Optional[str] = None
    merchant_category: Optional[str] = None
    location: Optional[str] = None
    features: Optional[Dict[str, Any]] = {}


class TransactionOut(BaseModel):
    id: str
    timestamp: datetime
    amount: float
    merchant_id: str
    merchant_name: Optional[str] = None
    merchant_category: Optional[str] = None
    user_id: str
    location: Optional[str] = None
    features: Dict[str, Any]
    risk_score: Optional[float] = None
    status: TransactionStatus
    created_at: datetime


class TransactionSummary(BaseModel):
    total: int
    flagged: int
    cleared: int
    fraud: int
    pending: int
    unscored: int
    avg_risk_score: float


# ── Case ───────────────────────────────────────────────────────────────────────

class CaseComment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    author_id: str
    author_name: str
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class CaseCreate(BaseModel):
    title: str
    transaction_ids: List[str]
    assigned_to: Optional[str] = None
    description: Optional[str] = None


class CaseUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[CaseStatus] = None
    assigned_to: Optional[str] = None
    description: Optional[str] = None


class CaseAddComment(BaseModel):
    content: str


class CaseOut(BaseModel):
    id: str
    title: str
    transaction_ids: List[str]
    assigned_to: Optional[str] = None
    assigned_to_name: Optional[str] = None
    status: CaseStatus
    description: Optional[str] = None
    comments: List[CaseComment]
    created_by: str
    created_by_name: str
    created_at: datetime
    updated_at: datetime


# ── Alert ──────────────────────────────────────────────────────────────────────

class AlertOut(BaseModel):
    id: str
    transaction_id: str
    triggered_at: datetime
    type: AlertType
    status: AlertStatus
    risk_score: Optional[float] = None
    amount: Optional[float] = None
    merchant_name: Optional[str] = None
    user_id: Optional[str] = None


class AlertUpdate(BaseModel):
    status: AlertStatus


# ── AuditLog ───────────────────────────────────────────────────────────────────

class AuditLogOut(BaseModel):
    id: str
    user_id: str
    user_name: Optional[str] = None
    action: str
    timestamp: datetime
    details: Dict[str, Any]


# ── Dashboard ──────────────────────────────────────────────────────────────────

class DashboardStats(BaseModel):
    total_transactions: int
    flagged_today: int
    active_cases: int
    new_alerts: int
    fraud_rate: float
    total_fraud_amount: float
    avg_risk_score: float
    transactions_by_day: List[Dict[str, Any]]
    risk_distribution: List[Dict[str, Any]]
    top_merchants: List[Dict[str, Any]]
    recent_alerts: List[AlertOut]
