from flask import Blueprint, jsonify, request
from pymongo.errors import PyMongoError

from . import services
from .database import get_db
from .errors import ApiError

api = Blueprint("api", __name__)


def _json_body():
    data = request.get_json(silent=True)
    if data is None:
        raise ApiError("Request body must be valid JSON", 400)
    return data


# ---------- health ----------
@api.get("/health")
def health():
    return jsonify({"status": "ok"}), 200


@api.get("/health/db")
def health_db():
    try:
        get_db().client.admin.command("ping")
        return jsonify({"status": "ok", "database": "connected"}), 200
    except PyMongoError:
        return jsonify({"status": "error", "database": "unreachable"}), 503


@api.post("/members")
def create_member():
    return jsonify(services.create_member(_json_body())), 201


@api.get("/members")
def list_members():
    return jsonify(services.list_members()), 200


@api.post("/tasks")
def create_task():
    return jsonify(services.create_task(_json_body())), 201


@api.get("/tasks")
def list_tasks():
    return jsonify(services.list_tasks(request.args.get("status"))), 200


@api.get("/tasks/<task_id>")
def get_task(task_id):
    return jsonify(services.get_task(task_id)), 200


@api.put("/tasks/<task_id>/assignee")
def set_assignee(task_id):
    return jsonify(services.set_assignee(task_id, _json_body())), 200
