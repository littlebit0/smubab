# SMU-Bab Backend API

FastAPI backend for SMU-Bab. It is configured to run locally with SQLite.

## Install

```powershell
python -m venv ..\.venv
..\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Run

```powershell
..\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

Or on Windows:

```powershell
.\start-backend.bat
```

## URLs

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`
- Health: `http://127.0.0.1:8000/api/health`

## Data

Menus and web push subscriptions are stored in local SQLite. The default database file is `backend/smubab.db`; override it with `MENU_DB_PATH`.
