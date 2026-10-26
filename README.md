# Agile Task Orchestration API (Mini-Jira)

Flask + PyMongo REST API for team members, tasks, ownership and progress.
Status: Days 1-5 (members, tasks, discovery, ownership). Progress tracking and QA sign-off come in Days 6-7.

## Setup (Windows PowerShell)
```powershell
python -m venv venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python run.py
```
MongoDB must be running on `localhost:27017` (or set `MONGO_URI` in `.env`).
The app runs at http://127.0.0.1:5000.

## Run tests
Tests use a separate database (`TEST_DB_NAME`) and start their own server.
```powershell
python -m unittest discover -s tests -v
```

## Endpoints (so far)
| Method | Path | Success | Errors |
|---|---|---|---|
| GET | `/health` | 200 | |
| GET | `/health/db` | 200 | 503 |
| POST | `/members` `{name, role}` | 201 | 400 |
| GET | `/members` | 200 | |
| POST | `/tasks` `{title, description, priority}` | 201 | 400 |
| GET | `/tasks?status=To Do\|In Progress\|Done` | 200 | 400 |
| GET | `/tasks/<id>` | 200 | 400, 404 |
| PUT | `/tasks/<id>/assignee` `{assignee_id: "<id>"\|null}` | 200 | 400, 404 |

Roles: Developer, QA, Manager. Priorities: Low, Medium, High. Statuses: To Do, In Progress, Done.
Errors are always `{"error": "message"}`.

## Design decisions (so far)
- Tasks store the owner as `assignee_id` (ObjectId), `null` when unassigned.
- Assigning a nonexistent member returns 404 and changes nothing.
- Assignment (`PUT /tasks/<id>/assignee`) and status changes (Day 6) are separate operations.
- Business logic lives in `app/services.py`; routes stay thin.
- Never commit `.env`; use `.env.example`.
# Agile Task Orchestration API (Mini-Jira)

Simple Flask + PyMongo REST API for team members, tasks, ownership and progress.
Status: Days 1-8 (setup, members, tasks, discovery, ownership, status rules, QA sign-off, tests).

## Setup (PowerShell)
```powershell
python -m venv venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python run.py
```
MongoDB must be running on `localhost:27017`. Never commit `.env`.

## Run tests
Tests use a separate database (`TEST_DB_NAME`), so your real data is safe.
```powershell
python -m unittest discover -s tests -v
```

## Endpoints
| Method | Path | Body | Success | Errors |
|---|---|---|---|---|
| GET | `/health`, `/health/db` | | 200 | 503 |
| POST | `/members` | `{name, role}` | 201 | 400 |
| GET | `/members` | | 200 | |
| POST | `/tasks` | `{title, description, priority}` | 201 | 400 |
| GET | `/tasks` or `/tasks?status=In Progress` | | 200 | 400 |
| GET | `/tasks/<id>` | | 200 | 400, 404 |
| PUT | `/tasks/<id>/assignee` | `{assignee_id}` (null = unassign) | 200 | 400, 404 |
| PATCH | `/tasks/<id>/status` + header `X-Member-Id` | `{status}` | 200 | 400, 401, 403, 404, 409 |

Roles: Developer, QA, Manager. Priorities: Low, Medium, High. Statuses: To Do, In Progress, Done.
Errors look like `{"error": "message"}`.

| Code | Meaning |
|---|---|
| 400 | bad input (missing field, bad value, bad id) |
| 401 | `X-Member-Id` header missing or unknown |
| 403 | only QA can mark Done |
| 404 | task or member not found |
| 409 | rule broken: no assignee, task not In Progress, same status |

## Status change rules
1. A task with no assignee cannot move to In Progress or Done.
2. Only a QA member can mark a task Done.
3. Done can only come from In Progress.
4. Every change records who did it and when (`status_changed_by`, `status_changed_at`, `status_history`).

Example:
```powershell
Invoke-RestMethod -Method Patch -Uri http://127.0.0.1:5000/tasks/<task id>/status `
  -Headers @{ "X-Member-Id" = "<qa member id>" } `
  -ContentType "application/json" -Body '{"status":"Done"}'
```

## How the API knows who you are
You send your member id in the `X-Member-Id` header. This only **identifies** you, it does not
**prove** it is you. Anyone who knows a QA member's id can pretend to be them, so this is not
secure authentication. A real system would use login and signed tokens (JWT). See `DESIGN_DECISIONS.md`.

## Files
- `app/routes.py` - endpoints and rules
- `app/services.py` - constants and small helper functions
- `app/database.py`, `app/config.py` - MongoDB connection and settings
- `tests/` - `test_members.py`, `test_tasks.py`, `test_business_rules.py`, shared `base.py`
