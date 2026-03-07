import os
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017/utkal_uday")

# Async client for FastAPI
async_client = AsyncIOMotorClient(MONGODB_URL)
async_db = async_client.get_default_database()

# Sync client for scripts
sync_client = MongoClient(MONGODB_URL)
sync_db = sync_client.get_default_database()

# Collections
questions_collection = async_db["questions"]
quizzes_collection = async_db["quizzes"]
student_attempts_collection = async_db["student_attempts"]
content_versions_collection = async_db["content_versions"]

# Sync collections
sync_questions = sync_db["questions"]
sync_quizzes = sync_db["quizzes"]
