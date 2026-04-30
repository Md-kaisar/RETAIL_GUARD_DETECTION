"""
Seed the database with demo users and synthetic transactions.
Run: python seed.py
"""
import asyncio
import uuid
import random
import numpy as np
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext

MONGO_URL = "mongodb://localhost:27017"
DB_NAME = "retailguard"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

MERCHANTS = [
    ("M001", "Amazon", "E-commerce"),
    ("M002", "Walmart", "Retail"),
    ("M003", "Shell", "Gas Station"),
    ("M004", "McDonald's", "Fast Food"),
    ("M005", "Apple Store", "Electronics"),
    ("M006", "Unknown Merchant", "Other"),
    ("M007", "Alibaba", "E-commerce"),
    ("M008", "PayPal Transfer", "Finance"),
    ("M009", "Best Buy", "Electronics"),
    ("M010", "Starbucks", "Coffee"),
]

USERS = [
    {"name": "Admin User", "email": "admin@retailguard.io", "password": "Admin@123", "role": "admin"},
    {"name": "Alice Analyst", "email": "analyst@retailguard.io", "password": "Analyst@123", "role": "analyst"},
    {"name": "Ivan Investigator", "email": "investigator@retailguard.io", "password": "Invest@123", "role": "investigator"},
]


def utcnow():
    """Return timezone-aware UTC datetime (avoids deprecation warning)."""
    return datetime.now(timezone.utc)


async def seed():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]

    # Clear existing data
    await db.users.drop()
    await db.transactions.drop()
    await db.cases.drop()
    await db.alerts.drop()
    await db.audit_logs.drop()

    # Create indexes
    await db.users.create_index("email", unique=True)
    await db.transactions.create_index("id", unique=True)
    await db.cases.create_index("id", unique=True)
    await db.alerts.create_index("id", unique=True)

    # Seed users
    user_ids = {}
    for u in USERS:
        uid = str(uuid.uuid4())
        user_ids[u["email"]] = uid
        await db.users.insert_one({
            "id": uid,
            "name": u["name"],
            "email": u["email"],
            "password_hash": pwd_context.hash(u["password"]),
            "role": u["role"],
            "is_active": True,
            "created_at": utcnow(),
        })
    print(f"✅ Created {len(USERS)} users")

    # Seed transactions
    now = utcnow()
    transactions = []
    alerts = []
    THRESHOLD = 0.7

    # Import detector
    import sys
    sys.path.insert(0, ".")
    from ml.detector import get_detector
    detector = get_detector()

    for i in range(300):
        mid, mname, mcat = random.choice(MERCHANTS)
        ts = now - timedelta(hours=random.randint(0, 336))
        amount = round(np.random.lognormal(4.5, 1.2), 2)  # Fixed: was random.lognormal

        # Make ~12% look fraudulent
        is_fraud = random.random() < 0.12
        features = {
            "hour_of_day": ts.hour if not is_fraud else random.choice([0, 1, 2, 3, 23]),
            "day_of_week": ts.weekday(),
            "customer_age_days": random.randint(1, 10) if is_fraud else random.randint(60, 1800),
            "num_txn_last_24h": random.randint(8, 20) if is_fraud else random.randint(0, 4),
            "avg_txn_amount_30d": round(amount * random.uniform(0.1, 0.3) if is_fraud else amount * random.uniform(0.7, 1.3), 2),
            "distance_from_home": round(random.uniform(300, 3000) if is_fraud else random.uniform(0, 50), 2),
            "is_online": True if is_fraud else random.random() < 0.3,
            "is_foreign": True if is_fraud else random.random() < 0.05,
        }
        if is_fraud:
            amount = round(np.random.lognormal(6.5, 1.0), 2)  # Fixed: was random.lognormal

        txn = {
            "id": str(uuid.uuid4()),
            "timestamp": ts,
            "amount": amount,
            "merchant_id": mid,
            "merchant_name": mname,
            "merchant_category": mcat,
            "user_id": f"CUST{random.randint(1000, 9999)}",
            "location": random.choice(["New York", "London", "Mumbai", "Tokyo", "Unknown"]),
            "features": features,
            "created_at": utcnow(),
        }

        score = detector.score_transaction(txn)
        txn["risk_score"] = score
        if score >= THRESHOLD:
            txn["status"] = "flagged"
            alert = {
                "id": str(uuid.uuid4()),
                "transaction_id": txn["id"],
                "triggered_at": ts,
                "type": "FRAUD",
                "status": random.choice(["new", "acknowledged"]),
                "risk_score": score,
                "amount": amount,
                "merchant_name": mname,
                "user_id": txn["user_id"],
            }
            alerts.append(alert)
        else:
            txn["status"] = "cleared"

        transactions.append(txn)

    await db.transactions.insert_many(transactions)
    if alerts:
        await db.alerts.insert_many(alerts)

    # Seed a case
    flagged_ids = [t["id"] for t in transactions if t["status"] == "flagged"][:3]
    if flagged_ids:
        await db.cases.insert_one({
            "id": str(uuid.uuid4()),
            "title": "Suspicious Batch — High-value online fraud cluster",
            "transaction_ids": flagged_ids,
            "assigned_to": user_ids["investigator@retailguard.io"],
            "status": "in_progress",
            "description": "Multiple high-value transactions flagged from same IP range.",
            "comments": [
                {
                    "id": str(uuid.uuid4()),
                    "author_id": user_ids["analyst@retailguard.io"],
                    "author_name": "Alice Analyst",
                    "content": "Initial review: all from new accounts, foreign IPs.",
                    "created_at": utcnow(),
                }
            ],
            "created_by": user_ids["analyst@retailguard.io"],
            "created_at": utcnow(),
            "updated_at": utcnow(),
        })

    print(f"✅ Seeded {len(transactions)} transactions, {len(alerts)} alerts")
    print("\n📋 Demo credentials:")
    for u in USERS:
        print(f"   {u['role']:15s} → {u['email']} / {u['password']}")
    client.close()


if __name__ == "__main__":
    asyncio.run(seed())