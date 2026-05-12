# Development

## Backend

Run the backend on the local computer:

```powershell
cd backend
python -m venv ..\.venv
..\.venv\Scripts\python.exe -m pip install -r requirements.txt
..\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

The API is available at `http://127.0.0.1:8000`.

## Web

```powershell
cd web
npm install
npm run dev
```

The Vite dev server proxies `/api` to `http://localhost:8000`.

## Netlify

Netlify remains the frontend host. The deployed web app is configured to call the local backend at `http://127.0.0.1:8000`.

## Mobile

For Expo on a physical phone, the phone cannot use the computer's `127.0.0.1`. Set `EXPO_PUBLIC_API_BASE_URL` to the computer's LAN IP:

```powershell
$env:EXPO_PUBLIC_API_BASE_URL="http://192.168.0.10:8000"
cd mobile
npm start
```
