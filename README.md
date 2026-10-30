# Agile Task Orchestration API (Mini-Jira)

Flask + PyMongo REST API for team members, tasks, ownership and progress. JSON only.

## Setup (Windows PowerShell)
```powershell
python -m venv venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python run.py
```
MongoDB must be running. Set `MONGO_URI` in `.env` (local or Atlas). Never commit `.env`.

## Run the tests
Tests use the separate `TEST_DB_NAME` database and call the real app with `requests`.
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
| GET | `/tasks`, `/tasks?status=` | | 200 | 400 |
| GET | `/tasks/<id>` | | 200 | 400, 404 |
| PUT | `/tasks/<id>/assignee` | `{assignee_id}` or `null` | 200 | 400, 404 |
| PATCH | `/tasks/<id>/status` (header `X-Member-Id`) | `{status}` | 200 | 400, 401, 403, 404, 409 |

Roles: Developer, QA, Manager. Priorities: Low, Medium, High. Statuses: To Do, In Progress, Done.
Errors are `{"error": "message"}`: 400 bad input, 401 unknown actor, 403 not QA, 404 not found, 409 rule broken.

## Frontend (React + Vite)
Start the API first, then in a second terminal:
```powershell
cd frontend
npm install
npm run dev
```
Open http://localhost:5173. The dev server proxies `/api` to the Flask API on port 5000.
Choose a member under "Acting as" before changing a task status.

## Design note
- A task stores its owner as `assignee_id`, which is `null` when unassigned. Assigning a member that does not exist returns 404 and changes nothing.
- Assignment and status changes are separate endpoints, because their rules and errors differ.
- A task without an assignee cannot move to In Progress or Done. Only a QA member can mark a task Done, and only from In Progress.
- Each status change stores who made it and when (`status_changed_by`, `status_changed_at`, `status_history`).
- The acting member is identified by the `X-Member-Id` header and the role is read from the database. This identifies the caller but does not authenticate them, so anyone who knows a QA member's id can use it. Real security needs login and signed tokens.
