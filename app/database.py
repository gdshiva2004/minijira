from flask import current_app
from pymongo import MongoClient


def init_db(app):
    client = MongoClient(app.config["MONGO_URI"], serverSelectionTimeoutMS=3000)
    app.extensions["mongo_client"] = client
    app.extensions["mongo_db"] = client[app.config["DB_NAME"]]


def get_db():
    return current_app.extensions["mongo_db"]
