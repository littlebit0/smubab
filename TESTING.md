# Testing

## Backend

Start the local backend:

```powershell
cd backend
..\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

Check the API:

```powershell
curl http://127.0.0.1:8000/api/health
curl http://127.0.0.1:8000/api/menus/today
curl http://127.0.0.1:8000/api/menus/week
curl http://127.0.0.1:8000/api/restaurants
```

API docs:

- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/redoc`

## Web

```powershell
cd web
npm run build
```

For local development:

```powershell
cd web
npm run dev
```

## Mobile

For a physical phone, set the API URL to the computer's LAN IP:

```powershell
$env:EXPO_PUBLIC_API_BASE_URL="http://192.168.0.10:8000"
cd mobile
npm start
```

For local web/emulator-only checks, the default `http://127.0.0.1:8000` can be used.

## Menu Refresh

```powershell
curl -X POST http://127.0.0.1:8000/api/menus/refresh
curl http://127.0.0.1:8000/api/menus/week
```
