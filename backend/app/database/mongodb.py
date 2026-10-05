import os
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings

class MongoDB:
    client: AsyncIOMotorClient = None
    db = None

db_instance = MongoDB()

async def connect_to_mongo():
    try:
        db_instance.client = AsyncIOMotorClient(settings.MONGODB_URI, serverSelectionTimeoutMS=1500)
        await db_instance.client.admin.command("ping")
        db_instance.db = db_instance.client.get_database("agentic_flow")
        print("Connected to MongoDB.")
    except Exception as e:
        db_instance.client = None
        db_instance.db = None
        print(f"Could not connect to MongoDB ({e}). Using in-memory workspace store.")

async def close_mongo_connection():
    if db_instance.client:
        db_instance.client.close()
        print("Closed MongoDB connection.")

def get_database():
    return db_instance.db
