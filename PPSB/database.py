from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_URI, DB_NAME
import logging


client: Optional[AsyncIOMotorClient] = None
db = None

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def init_db() -> None:
    global client, db
    try:
        client = AsyncIOMotorClient(MONGO_URI)
        db = client[DB_NAME]
        await client.admin.command('ping')
        logger.info(f"Connected to MongoDB with URL: {MONGO_URI} and DB Name: {DB_NAME}")
        await db["users"].create_index("user_id", unique=True)
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise

async def close_db_connection() -> None:
    global client
    if client:
        logger.info("Closing MongoDB connection...")
        client.close()
        logger.info("MongoDB connection closed.")

def get_db():
    if db is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return db