# SMU-Bab Flutter

Native Flutter client for SMU-Bab. It calls the backend API directly and renders today's menus and weekly menus without a WebView.

## Local run

```powershell
..\.tools\flutter\bin\flutter.bat pub get
..\.tools\flutter\bin\flutter.bat run -d web-server --web-hostname 127.0.0.1 --web-port 5000 --dart-define=API_BASE_URL=http://127.0.0.1:8000
```

For an Android emulator, use:

```powershell
..\.tools\flutter\bin\flutter.bat run --dart-define=API_BASE_URL=http://10.0.2.2:8000
```

## Release examples

```powershell
..\.tools\flutter\bin\flutter.bat build appbundle --release --dart-define=API_BASE_URL=http://127.0.0.1:8000
..\.tools\flutter\bin\flutter.bat build ipa --release --dart-define=API_BASE_URL=http://127.0.0.1:8000
```
