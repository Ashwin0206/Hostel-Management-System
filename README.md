# HOSTELOS

**One intelligent platform to run the entire hostel.** A low-cost hostel operations prototype with distinct Student, Warden, Staff Manager and Admin portals.

## Stack

- Frontend: React, Vite, plain CSS, Lucide icons and Recharts
- Backend: FastAPI, SQLAlchemy, SQLite, JWT authentication

## Quick start

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
Copy-Item ..\.env.example .env
python -m app.seed
uvicorn app.main:app --reload --port 8000
```

In another terminal:

```powershell
cd frontend
npm.cmd install
npm.cmd run dev
```

Open the displayed Vite URL. The frontend proxies `/api` to port 8000.

## Demo accounts

| Role | Email | Password |
| --- | --- | --- |
| Student | student1@demo.hostelos | Demo@123 |
| Student | student2@demo.hostelos | Demo@123 |
| Student | student3@demo.hostelos | Demo@123 |
| Boys Warden | boys.warden@demo.hostelos | Demo@123 |
| Girls Warden | girls.warden@demo.hostelos | Demo@123 |
| Staff Manager | staff@demo.hostelos | Demo@123 |
| Admin | admin@demo.hostelos | Demo@123 |

## Environment

Copy `.env.example` to `backend/.env` before development. `GROQ_API_KEY` is optional: complaint analysis falls back to deterministic keyword classification when it is unavailable. `DEMO_ATTENDANCE_MODE=true` permits seeded/demo requests; production checks `HOSTEL_NETWORK_PREFIX` against the request IP.

Network verification confirms that a device is accessing the application through an authorized network. It cannot mathematically prove a particular person is physically inside the hostel.

## Architecture

The REST API enforces JWT authentication and role restrictions on the server. SQLite stores users, rooms, attendance, requests, complaints, hospital visits, notices, notifications and operational data. The React client uses a top navigation bar, persisted appearance preference, responsive content cards, and role-specific routes.

## Sample Hostel Dataset / reset

The fixed seed creates 40 rooms across Floors 1–4 (101–110, 201–210, 301–310, 401–410), with exactly four fictional residents in every room: **160 students total**. It is deterministic and stored in SQLite; the application never reseeds on normal startup.

To explicitly reset the demo database, run:

```powershell
cd backend
python -m app.seed
```

## Prototype notes

The staff manager assigns physical workers in the system; workers do not have accounts. No payments or fee modules are included. For deployment, run behind TLS, set a strong `JWT_SECRET`, configure trusted proxy/IP forwarding, use a managed database and replace demo-only network behaviour.
