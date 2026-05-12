# SMU-Bab Deployment Checklist

## Local Backend

The backend is no longer deployed to a remote hosting service. Run it on the local computer:

```powershell
cd backend
python -m venv ..\.venv
..\.venv\Scripts\python.exe -m pip install -r requirements.txt
..\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

Required backend environment:

```env
MENU_DB_PATH=./smubab.db
MENU_UPDATE_INTERVAL_SECONDS=21600
MENU_WEEKEND_UPDATE_INTERVAL_SECONDS=3600
VAPID_PUBLIC_KEY=your-public-key
VAPID_PRIVATE_KEY=your-private-key
VAPID_CLAIMS_SUB=mailto:admin@smubab.app
```

Useful checks:

```powershell
curl http://127.0.0.1:8000/api/health
curl http://127.0.0.1:8000/api/menus/today
curl http://127.0.0.1:8000/api/push/status
curl http://127.0.0.1:8000/api/push/public-key
```

## Netlify

Keep the web frontend on Netlify. The built frontend calls the backend running on the user's local computer:

```env
VITE_API_URL=http://127.0.0.1:8000
VITE_PUSH_API_URL=http://127.0.0.1:8000
```

These values are also set in `netlify.toml`. Netlify Functions were removed; the deployed web app calls the local backend directly.

## Push Verification

1. Start the local backend.
2. Open the Netlify web app from the same computer.
3. Enable menu update notifications in the app.
4. Check the backend:

```powershell
curl http://127.0.0.1:8000/api/push/status
```

5. Send a test push:

```powershell
curl -X POST http://127.0.0.1:8000/api/push/test
```
