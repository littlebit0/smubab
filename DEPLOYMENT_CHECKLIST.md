# SMU-Bab Deployment Checklist

## Backend VM

1. Pull the latest repository on the VM.
2. Install backend dependencies.
3. Create or update `backend/.env` on the VM.
4. Restart the backend process.

Required backend environment:

```env
MENU_DB_PATH=./smubab.db
MENU_UPDATE_INTERVAL_SECONDS=21600
MENU_WEEKEND_UPDATE_INTERVAL_SECONDS=3600
VAPID_PUBLIC_KEY=your-public-key
VAPID_PRIVATE_KEY=your-private-key
VAPID_CLAIMS_SUB=mailto:admin@smubab.app
```

Generate VAPID keys:

```bash
npx web-push generate-vapid-keys
```

Useful checks:

```bash
curl http://127.0.0.1:8000/api/health
curl http://127.0.0.1:8000/api/menus/today
curl http://127.0.0.1:8000/api/push/status
curl http://127.0.0.1:8000/api/push/public-key
```

Expected cache behavior:

- Menus are stored in SQLite, so normal reads do not crawl the university site.
- Weekday polling defaults to every 6 hours.
- Weekend polling defaults to every 1 hour so the next weekly menu can be picked up after it is posted.
- Web push subscriptions are stored in the same SQLite database and survive backend restarts.

## Netlify

Set these environment variables in Netlify:

```env
BACKEND_API_URL=https://your-backend-host
VITE_API_URL=https://your-backend-host
VITE_PUSH_API_URL=https://your-backend-host
```

Then redeploy the web app.

## Push Verification

1. Open the deployed web app over HTTPS.
2. On iOS Safari, add the site to Home Screen before enabling push.
3. Enable menu update notifications in the app.
4. Check the backend:

```bash
curl http://127.0.0.1:8000/api/push/status
```

5. Send a test push:

```bash
curl -X POST http://127.0.0.1:8000/api/push/test
```

If `subscriptionCount` is `0`, the backend is ready but no browser has subscribed yet.

## Flutter Native Push

The current Flutter app reads the menu API directly. Native Android/iOS push requires Firebase Cloud Messaging and cannot be completed without Firebase project files:

- `android/app/google-services.json`
- `ios/Runner/GoogleService-Info.plist`

After those are available, add `firebase_core` and `firebase_messaging`, initialize Firebase, and connect device tokens to the backend.
