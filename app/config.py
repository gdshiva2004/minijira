import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "agile_task_db")
TEST_DB_NAME = os.getenv("TEST_DB_NAME", "agile_task_test_db")
JWT_SECRET = os.getenv("JWT_SECRET", "")
JWT_EXPIRES_MINUTES = int(os.getenv("JWT_EXPIRES_MINUTES", "480"))
