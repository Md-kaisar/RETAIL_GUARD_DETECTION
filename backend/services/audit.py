from datetime import datetime
from typing import Dict, Any
import uuid
from database import get_db


async def log_action(user_id: str, action: str, details: Dict[str, Any] = None):
    db = get_db()
    await db.audit_logs.insert_one({
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "action": action,
        "timestamp": datetime.utcnow(),
        "details": details or {},
    })
