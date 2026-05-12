# Netlify + Local Backend

The frontend remains deployed on Netlify. The backend is not deployed remotely; it runs on the local computer at `http://127.0.0.1:8000`.

## 1. Run Backend Locally

```powershell
cd backend
..\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

If the virtual environment does not exist yet:

```powershell
python -m venv ..\.venv
..\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 2. Netlify Frontend

`netlify.toml` keeps the existing Netlify build and sets:

```env
VITE_API_URL=http://127.0.0.1:8000
VITE_PUSH_API_URL=http://127.0.0.1:8000
```

When the Netlify site is opened on the same computer, browser requests go directly to the local backend.

## 3. Verify

```powershell
curl http://127.0.0.1:8000/api/health
curl http://127.0.0.1:8000/api/menus/today
```
