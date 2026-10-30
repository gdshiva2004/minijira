# Agile Task Orchestration API (Mini-Jira)

Flask + PyMongo REST API with JWT login, plus a React frontend. JSON only.

## Backend setup (Windows PowerShell)
```powershell
python -m venv venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python -c "import secrets; print(secrets.token_hex(32))"
```
Open `.env` and fill it in. Put the long random text printed above after `JWT_SECRET=`, and your database address after `MONGO_URI=` (local MongoDB or Atlas). Real values go only in `.env`, which is git-ignored. Never put them in `.env.example`.

```powershell
python run.py
```
The API starts on http://127.0.0.1:5000 and refuses to start if `JWT_SECRET` is missing or shorter than 32 characters.

## Run the tests
Tests use the separate `TEST_DB_NAME` database and call the real app with `requests`.
```powershell
python -m unittest discover -s tests -v
```

## Frontend
```powershell
cd frontend
npm install
npm run dev
```
Open http://localhost:5173 and sign up. The dev server proxies `/api` to the Flask API.

## Endpoints
Send `Authorization: Bearer <token>` on every endpoint except health, signup and login.

| Method | Path | Body | Success | Errors |
|---|---|---|---|---|
| GET | `/health`, `/health/db` | | 200 | 503 |
| POST | `/auth/signup` | `{name, email, password, role}` | 201 | 400, 409 |
| POST | `/auth/login` | `{email, password}` | 200 | 400, 401 |
| GET | `/auth/me` | | 200 | 401 |
| GET | `/members` | | 200 | 401 |
| POST | `/tasks` | `{title, description, priority}` | 201 | 400, 401 |
| GET | `/tasks`, `/tasks?status=` | | 200 | 400, 401 |
| GET | `/tasks/<id>` | | 200 | 400, 401, 404 |
| PUT | `/tasks/<id>/assignee` | `{assignee_id}` or `null` | 200 | 400, 401, 404 |
| PATCH | `/tasks/<id>/status` | `{status}` | 200 | 400, 401, 403, 404, 409 |

Signup and login return `{"token": "...", "member": {...}}`.
Roles: Developer, QA, Manager. Priorities: Low, Medium, High. Statuses: To Do, In Progress, Done. Passwords: 8 to 128 characters.
Errors are `{"error": "message"}`: 400 bad input, 401 not logged in or bad credentials, 403 not QA, 404 not found, 409 conflict (duplicate email or rule broken).

## Design note
- Team members are the user accounts. Signing up creates a member with a role, so the team directory and the logins are one collection.
- A task stores its owner as `assignee_id`, which is `null` when unassigned. Assigning a member that does not exist returns 404 and changes nothing.
- Assignment and status changes are separate endpoints, because their rules and errors differ.
- A task without an assignee cannot move to In Progress or Done. Only a QA member can mark a task Done, and only from In Progress.
- The person making a change comes from the verified JWT, never from a request field. The member is loaded from the database on every request, so the QA rule uses the stored role. Each status change stores who made it and when (`status_changed_by`, `status_changed_at`, `status_history`).
- Passwords are hashed with PBKDF2-SHA256 and never returned. Login gives the same error for a wrong password and an unknown email. Tokens are HS256, signed with `JWT_SECRET`, and expire after `JWT_EXPIRES_MINUTES` (default 480).
- Roles are chosen at signup and trusted as given. A production system would let only an administrator assign the QA role.
