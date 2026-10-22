import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    DB_NAME = os.getenv("DB_NAME", "agile_task_db")
    TESTING = False


class TestConfig(Config):

    DB_NAME = os.getenv("TEST_DB_NAME", "agile_task_test_db")
    TESTING = True
