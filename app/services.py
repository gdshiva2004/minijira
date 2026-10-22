from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId

from .database import get_db
from .errors import ApiError

ROLES = ("Developer", "QA", "Manager")
PRIORITIES = ("Low", "Medium", "High")
STATUSES = ("To Do", "In Progress", "Done")

MAX_NAME = 100
MAX_TITLE = 200
MAX_DESCRIPTION = 2000


def _now():
    return datetime.now(timezone.utc)


def parse_object_id(value, label="id"):
    if not isinstance(value, str):
        raise ApiError(f"Invalid {label}", 400)
    try:
        return ObjectId(value)
    except (InvalidId, TypeError):
        raise ApiError(f"Invalid {label}", 400)


def _require_json_object(data):
    if not isinstance(data, dict):
        raise ApiError("Request body must be a JSON object", 400)


def _clean_text(data, field, max_len):
    value = data.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ApiError(f"'{field}' is required and must be a non-empty string", 400)
    value = value.strip()
    if len(value) > max_len:
        raise ApiError(f"'{field}' must be at most {max_len} characters", 400)
    return value


def serialize_member(doc):
    return {
        "id": str(doc["_id"]),
        "name": doc["name"],
        "role": doc["role"],
        "created_at": doc["created_at"].isoformat(),
    }


def serialize_task(doc):
    assignee = doc.get("assignee_id")
    return {
        "id": str(doc["_id"]),
        "title": doc["title"],
        "description": doc["description"],
        "priority": doc["priority"],
        "status": doc["status"],
        "assignee_id": str(assignee) if assignee else None,
        "created_at": doc["created_at"].isoformat(),
        "updated_at": doc["updated_at"].isoformat(),
    }


def create_member(data):
    _require_json_object(data)
    name = _clean_text(data, "name", MAX_NAME)
    role = data.get("role")
    if role not in ROLES:
        raise ApiError(f"'role' must be one of: {', '.join(ROLES)}", 400)
    doc = {"name": name, "role": role, "created_at": _now()}
    doc["_id"] = get_db().members.insert_one(doc).inserted_id
    return serialize_member(doc)


def list_members():
    return [serialize_member(d) for d in get_db().members.find().sort("created_at", 1)]


def get_member_or_404(member_id):
    doc = get_db().members.find_one({"_id": parse_object_id(member_id, "member id")})
    if doc is None:
        raise ApiError("Member not found", 404)
    return doc

def create_task(data):
    _require_json_object(data)
    title = _clean_text(data, "title", MAX_TITLE)
    description = _clean_text(data, "description", MAX_DESCRIPTION)
    priority = data.get("priority")
    if priority not in PRIORITIES:
        raise ApiError(f"'priority' must be one of: {', '.join(PRIORITIES)}", 400)
    now = _now()
    doc = {
        "title": title,
        "description": description,
        "priority": priority,
        "status": "To Do",  
        "assignee_id": None,
        "created_at": now,
        "updated_at": now,
    }
    doc["_id"] = get_db().tasks.insert_one(doc).inserted_id
    return serialize_task(doc)


def list_tasks(status=None):
    query = {}
    if status is not None:
        if status not in STATUSES:
            raise ApiError(f"'status' must be one of: {', '.join(STATUSES)}", 400)
        query["status"] = status
    return [serialize_task(d) for d in get_db().tasks.find(query).sort("created_at", 1)]


def get_task_or_404(task_id):
    doc = get_db().tasks.find_one({"_id": parse_object_id(task_id, "task id")})
    if doc is None:
        raise ApiError("Task not found", 404)
    return doc


def get_task(task_id):
    return serialize_task(get_task_or_404(task_id))


def set_assignee(task_id, data):
    """Assign, reassign or unassign. Body: {"assignee_id": "<id>" | null}."""
    _require_json_object(data)
    if "assignee_id" not in data:
        raise ApiError("'assignee_id' is required (use null to unassign)", 400)

    task = get_task_or_404(task_id)
    raw = data["assignee_id"]

    if raw is None:
        new_assignee = None
    else:
        new_assignee = get_member_or_404(raw)["_id"]  # 400 bad id, 404 missing

    get_db().tasks.update_one(
        {"_id": task["_id"]},
        {"$set": {"assignee_id": new_assignee, "updated_at": _now()}},
    )
    return get_task(task_id)
