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
