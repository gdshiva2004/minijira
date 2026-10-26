from flask import current_app
from pymongo import MongoClient

from .config import MONGO_URI, DB_NAME, TEST_DB_NAME


def connect(app, testing=False):
    """Connect to MongoDB. Tests use a different database name."""
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000, tz_aware=True)
    app.client = client
    app.db = client[TEST_DB_NAME if testing else DB_NAME]


def get_db():
    return current_app.db
