from flask import Blueprint, g, jsonify, request
from pymongo.errors import DuplicateKeyError

from .auth import check_credentials, create_token, hash_password, login_required
from .database import get_db
from .services import (
    ROLES, PRIORITIES, STATUSES,
    MAX_NAME, MAX_TITLE, MAX_DESCRIPTION, MIN_PASSWORD, MAX_PASSWORD,
    error, now, to_object_id, is_text, clean_email, member_to_dict, task_to_dict,
)

api = Blueprint("api", __name__)


def get_json():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return None
    return data


def find_task(task_id):
    oid = to_object_id(task_id)
    if oid is None:
        return None, error("Invalid task id", 400)
    task = get_db().tasks.find_one({"_id": oid})
    if task is None:
        return None, error("Task not found", 404)
    return task, None


@api.get("/health")
def health():
    return jsonify({"status": "ok"})


@api.get("/health/db")
def health_db():
    try:
        get_db().client.admin.command("ping")
        return jsonify({"status": "ok", "database": "connected"})
    except Exception:
        return error("Database not reachable", 503)


@api.post("/auth/signup")
def signup():
    data = get_json()
    if data is None:
        return error("Send a JSON object", 400)
    if not is_text(data.get("name")):
        return error("name is required", 400)
    if len(data["name"].strip()) > MAX_NAME:
        return error("name must be at most %d characters" % MAX_NAME, 400)
    email = clean_email(data.get("email"))
    if email is None:
        return error("A valid email is required", 400)
    password = data.get("password")
    if not isinstance(password, str) or len(password) < MIN_PASSWORD:
        return error("password must be at least %d characters" % MIN_PASSWORD, 400)
    if len(password) > MAX_PASSWORD:
        return error("password must be at most %d characters" % MAX_PASSWORD, 400)
    if data.get("role") not in ROLES:
        return error("role must be one of: Developer, QA, Manager", 400)

    members = get_db().members
    members.create_index(
        "email", unique=True, partialFilterExpression={"email": {"$type": "string"}}
    )
    if members.find_one({"email": email}) is not None:
        return error("Email is already registered", 409)

    member = {
        "name": data["name"].strip(),
        "email": email,
        "role": data["role"],
        "password_hash": hash_password(password),
    }
    try:
        member["_id"] = members.insert_one(member).inserted_id
    except DuplicateKeyError:
        return error("Email is already registered", 409)
    return jsonify({"token": create_token(member["_id"]), "member": member_to_dict(member)}), 201


@api.post("/auth/login")
def login():
    data = get_json()
    if data is None:
        return error("Send a JSON object", 400)
    email = clean_email(data.get("email"))
    password = data.get("password")
    if email is None or not isinstance(password, str) or password == "":
        return error("email and password are required", 400)

    member = get_db().members.find_one({"email": email})
    if not check_credentials(member, password):
        return error("Invalid email or password", 401)
    return jsonify({"token": create_token(member["_id"]), "member": member_to_dict(member)})


@api.get("/auth/me")
@login_required
def me():
    return jsonify(member_to_dict(g.member))


@api.get("/members")
@login_required
def list_members():
    members = [member_to_dict(m) for m in get_db().members.find().sort("_id", 1)]
    return jsonify(members)


@api.post("/tasks")
@login_required
def create_task():
    data = get_json()
    if data is None:
        return error("Send a JSON object", 400)
    if not is_text(data.get("title")):
        return error("title is required", 400)
    if len(data["title"].strip()) > MAX_TITLE:
        return error("title must be at most %d characters" % MAX_TITLE, 400)
    if not is_text(data.get("description")):
        return error("description is required", 400)
    if len(data["description"].strip()) > MAX_DESCRIPTION:
        return error("description must be at most %d characters" % MAX_DESCRIPTION, 400)
    if data.get("priority") not in PRIORITIES:
        return error("priority must be one of: Low, Medium, High", 400)

    task = {
        "title": data["title"].strip(),
        "description": data["description"].strip(),
        "priority": data["priority"],
        "status": "To Do",
        "assignee_id": None,
        "status_changed_by": None,
        "status_changed_at": None,
        "status_history": [],
    }
    task["_id"] = get_db().tasks.insert_one(task).inserted_id
    return jsonify(task_to_dict(task)), 201


@api.get("/tasks")
@login_required
def list_tasks():
    status = request.args.get("status")
    query = {}
    if status is not None:
        if status not in STATUSES:
            return error("status must be one of: To Do, In Progress, Done", 400)
        query["status"] = status
    tasks = [task_to_dict(t) for t in get_db().tasks.find(query).sort("_id", 1)]
    return jsonify(tasks)


@api.get("/tasks/<task_id>")
@login_required
def get_task(task_id):
    task, err = find_task(task_id)
    if err:
        return err
    return jsonify(task_to_dict(task))


@api.put("/tasks/<task_id>/assignee")
@login_required
def set_assignee(task_id):
    task, err = find_task(task_id)
    if err:
        return err

    data = get_json()
    if data is None or "assignee_id" not in data:
        return error("Send JSON with assignee_id (use null to unassign)", 400)

    if data["assignee_id"] is None:
        new_assignee = None
    else:
        member_id = to_object_id(data["assignee_id"])
        if member_id is None:
            return error("Invalid member id", 400)
        if get_db().members.find_one({"_id": member_id}) is None:
            return error("Member not found", 404)
        new_assignee = member_id

    get_db().tasks.update_one({"_id": task["_id"]}, {"$set": {"assignee_id": new_assignee}})
    task["assignee_id"] = new_assignee
    return jsonify(task_to_dict(task))


@api.patch("/tasks/<task_id>/status")
@login_required
def change_status(task_id):
    task, err = find_task(task_id)
    if err:
        return err

    data = get_json()
    if data is None or data.get("status") not in STATUSES:
        return error("status must be one of: To Do, In Progress, Done", 400)
    new_status = data["status"]
    actor = g.member

    if new_status == "Done" and actor["role"] != "QA":
        return error("Only a QA member can mark a task as Done", 403)

    old_status = task["status"]
    if new_status == old_status:
        return error("Task is already " + old_status, 409)

    if new_status in ("In Progress", "Done") and task.get("assignee_id") is None:
        return error("A task without an assignee cannot move to " + new_status, 409)

    if new_status == "Done" and old_status != "In Progress":
        return error("Only an In Progress task can be marked as Done", 409)

    time = now()
    history_entry = {
        "from": old_status,
        "to": new_status,
        "changed_by": actor["_id"],
        "changed_at": time,
    }
    result = get_db().tasks.update_one(
        {"_id": task["_id"], "status": old_status, "assignee_id": task.get("assignee_id")},
        {
            "$set": {
                "status": new_status,
                "status_changed_by": actor["_id"],
                "status_changed_at": time,
            },
            "$push": {"status_history": history_entry},
        },
    )
    if result.matched_count == 0:
        return error("Task was changed by someone else, please try again", 409)
    task = get_db().tasks.find_one({"_id": task["_id"]})
    return jsonify(task_to_dict(task))
