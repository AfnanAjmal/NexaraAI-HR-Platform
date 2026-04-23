from motor.motor_asyncio import AsyncIOMotorClient
from backend.config import MONGODB_URI, DB_NAME

# -------------------
# 1. Connection
# -------------------
client = AsyncIOMotorClient(MONGODB_URI)
db     = client[DB_NAME]

# -------------------
# 2. Collections
# -------------------
candidates_col = db["candidates"]
interviews_col = db["interviews"]
