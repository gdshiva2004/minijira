import re
from datetime import datetime, timezone

from bson import ObjectId
from flask import jsonify

ROLES = ["Developer", "QA", "Manager"]
PRIORITIES = ["Low", "Medium", "High"]
STATUSES = ["To Do", "In Progress", "Done"]

MAX_NAME = 100
MAX_TITLE = 200
MAX_DESCRIPTION = 2000
MAX_EMAIL = 254
MIN_PASSWORD = 8
MAX_PASSWORD = 128

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def error(message, code):
    return jsonify({"error": message}), code


def now():
    return datetime.now(timezone.utc)


def to_object_id(text):
    try:
        return ObjectId(text)
    except Exception:
        return None


def is_text(value):
    return isinstance(value, str) and value.strip() != ""


def clean_email(value):
    if not isinstance(value, str):
        return None
    email = value.strip().lower()
    if len(email) > MAX_EMAIL or not EMAIL_PATTERN.match(email):
        return None
    return email


def member_to_dict(member):
    return {
        "id": str(member["_id"]),
        "name": member["name"],
        "email": member.get("email"),
        "role": member["role"],
    }


def task_to_dict(task):
    assignee = task.get("assignee_id")
    changed_by = task.get("status_changed_by")
    changed_at = task.get("status_changed_at")
    history = []
    for h in task.get("status_history", []):
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
