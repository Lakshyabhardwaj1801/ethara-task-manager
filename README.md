# Ethara Task Manager

A full-stack **Team Task Manager** built for Ethara AI's Round 1 assessment.

**Live Demo:** `<your-railway-url>`  
**Demo Video:** `<your-loom-link>`  
**GitHub:** `<your-repo-url>`

---

## Tech Stack

| Layer     | Technology                        |
|-----------|-----------------------------------|
| Backend   | Python 3.11 + FastAPI             |
| Database  | PostgreSQL (Railway managed)      |
| ORM       | SQLAlchemy 2.0 + Alembic          |
| Auth      | JWT (python-jose) + bcrypt        |
| Frontend  | HTML + Vanilla JS + Tailwind CDN  |
| Deploy    | Railway                           |

---

## Features

- **Authentication** — Signup / Login with JWT tokens, bcrypt password hashing
- **Role-Based Access Control** — Admin and Member roles with distinct permissions
- **Project Management** — Create, view, delete projects (Admin only for create/delete)
- **Task Management** — Create tasks, assign to members, track status (Todo / In Progress / Done / Overdue)
- **Team Management** — Add/remove members per project
- **Dashboard** — Stats overview: total tasks, in progress, completed, overdue, progress bar
- **Auto Overdue Detection** — Tasks past due date auto-marked as Overdue
- **API Docs** — Swagger UI at `/docs`, ReDoc at `/redoc`

---

## RBAC Summary

| Action                    | Admin | Member           |
|---------------------------|-------|------------------|
| Create / Delete Project   | ✅    | ❌               |
| Add / Remove Members      | ✅    | ❌               |
| Create Tasks              | ✅    | ✅               |
| Edit Any Task             | ✅    | ❌               |
| Update Own Assigned Task  | ✅    | ✅ (status only) |
| Delete Tasks              | ✅    | ❌               |
| View Projects / Tasks     | ✅    | ✅ (own only)    |

---

## Local Setup

### Prerequisites
- Python 3.10+
- PostgreSQL running locally

### Steps

```bash
# 1. Clone
git clone <your-repo-url>
cd ethara-task-manager

# 2. Install dependencies
pip install -r backend/requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env with your PostgreSQL credentials

# 4. Run
python run.py
```

App runs at: `http://localhost:8000`  
API Docs at: `http://localhost:8000/docs`

---

## Railway Deployment

1. Push code to GitHub
2. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub
3. Add a **PostgreSQL** service to the project
4. In your app service → Variables, add:
   - `DATABASE_URL` → copy from PostgreSQL service (already set automatically if linked)
   - `JWT_SECRET` → any long random string
5. Railway auto-detects the `Procfile` and runs `python run.py`
6. Your app is live at the Railway-provided URL

---

## API Endpoints

| Method | Endpoint                              | Auth     | Role   |
|--------|---------------------------------------|----------|--------|
| POST   | /api/auth/signup                      | No       | —      |
| POST   | /api/auth/login                       | No       | —      |
| GET    | /api/auth/me                          | Yes      | Any    |
| GET    | /api/projects                         | Yes      | Any    |
| POST   | /api/projects                         | Yes      | Admin  |
| DELETE | /api/projects/{id}                    | Yes      | Admin  |
| GET    | /api/projects/{id}/members            | Yes      | Any    |
| POST   | /api/projects/{id}/members            | Yes      | Admin  |
| DELETE | /api/projects/{id}/members/{user_id}  | Yes      | Admin  |
| GET    | /api/projects/{id}/tasks              | Yes      | Any    |
| POST   | /api/projects/{id}/tasks              | Yes      | Any    |
| PATCH  | /api/tasks/{id}                       | Yes      | Any*   |
| DELETE | /api/tasks/{id}                       | Yes      | Admin  |
| GET    | /api/dashboard                        | Yes      | Any    |
| GET    | /api/users                            | Yes      | Any    |

*Members can only update status of tasks assigned to them.

---

## Project Structure

```
ethara-task-manager/
├── backend/
│   ├── __init__.py
│   ├── main.py          # FastAPI app + CORS + static files
│   ├── database.py      # SQLAlchemy engine + session
│   ├── models.py        # DB models (User, Project, Task, ProjectMember)
│   ├── schemas.py       # Pydantic request/response schemas
│   ├── auth.py          # JWT creation, verification, dependencies
│   └── routers/
│       ├── auth.py      # /api/auth/*
│       ├── projects.py  # /api/projects/*
│       ├── tasks.py     # /api/tasks/* + /api/projects/:id/tasks
│       ├── dashboard.py # /api/dashboard
│       └── users.py     # /api/users
├── frontend/
│   └── index.html       # Single-page app (HTML + Tailwind + Vanilla JS)
├── run.py               # Uvicorn entrypoint
├── Procfile             # Railway deploy command
├── .env.example         # Environment variable template
└── README.md
```
