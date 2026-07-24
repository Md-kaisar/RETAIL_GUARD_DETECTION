from motor.motor_asyncio import AsyncIOMotorClient
from config import settings

client = None
db = None

async def connect_db():
    global client, db

    client = AsyncIOMotorClient(settings.MONGO_URL)
    db = client[settings.DB_NAME]

    # Create indexes
    await db.users.create_index("email", unique=True)
    await db.transactions.create_index("id", unique=True)
    await db.transactions.create_index([("timestamp", -1)])
    await db.transactions.create_index("risk_score")
    await db.cases.create_index("id", unique=True)
    await db.alerts.create_index("id", unique=True)
    await db.audit_logs.create_index([("timestamp", -1)])

    print("✅ Connected to MongoDB")

async def close_db():
    global client
    if client:
        client.close()

def get_db():
    return db
