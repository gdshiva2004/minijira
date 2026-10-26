"""Constants and small helper functions used by the routes."""
from datetime import datetime, timezone

from bson import ObjectId

ROLES = ["Developer", "QA", "Manager"]
PRIORITIES = ["Low", "Medium", "High"]
STATUSES = ["To Do", "In Progress", "Done"]


def now():
    return datetime.now(timezone.utc)


def to_object_id(text):
    """Turn a string into an ObjectId, or return None if it is not valid."""
    try:
        return ObjectId(text)
    except Exception:
        return None


def is_text(value):
    return isinstance(value, str) and value.strip() != ""


def member_to_dict(member):
    return {"id": str(member["_id"]), "name": member["name"], "role": member["role"]}


def task_to_dict(task):
    assignee = task["assignee_id"]
    changed_by = task["status_changed_by"]
    changed_at = task["status_changed_at"]
    history = []
    for h in task["status_history"]:
        history.append({
            "from": h["from"],
            "to": h["to"],
            "changed_by": str(h["changed_by"]),
            "changed_at": h["changed_at"].isoformat(),
        })
    return {
        "id": str(task["_id"]),
        "title": task["title"],
        "description": task["description"],
        "priority": task["priority"],
        "status": task["status"],
        "assignee_id": str(assignee) if assignee else None,
        "status_changed_by": str(changed_by) if changed_by else None,
        "status_changed_at": changed_at.isoformat() if changed_at else None,
        "status_history": history,
    }
