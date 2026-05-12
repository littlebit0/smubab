# SMU-Bab

상명대학교 식당 메뉴를 보여주는 웹/모바일 프로젝트입니다.

현재 구조는 명확하게 분리되어 있습니다.

- 프론트엔드: Netlify 정적 사이트로 유지
- 백엔드: 원격 서버 없이 로컬 컴퓨터에서만 실행
- 데이터 저장: 로컬 SQLite 파일
- Render/Docker/PostgreSQL 배포 구성: 제거됨

## 프로젝트 구조

```text
smubab/
├─ backend/          # FastAPI 로컬 백엔드
├─ web/              # React + Vite Netlify 프론트엔드
├─ mobile/           # React Native / Expo 클라이언트
└─ mobile_flutter/   # Flutter 클라이언트
```

## 백엔드 실행

Windows PowerShell 기준:

```powershell
cd backend
python -m venv ..\.venv
..\.venv\Scripts\python.exe -m pip install -r requirements.txt
..\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

확인 주소:

- API 문서: `http://127.0.0.1:8000/docs`
- Health check: `http://127.0.0.1:8000/api/health`
- 오늘 메뉴: `http://127.0.0.1:8000/api/menus/today`

## Netlify 프론트엔드

Netlify는 프론트엔드 정적 호스팅만 담당합니다. 배포된 웹앱은 기본적으로 사용자의 로컬 백엔드에 직접 요청합니다.

```env
VITE_API_URL=http://127.0.0.1:8000
VITE_PUSH_API_URL=http://127.0.0.1:8000
```

중요: Netlify 사이트를 열어도 같은 컴퓨터에서 로컬 백엔드가 실행 중이어야 메뉴가 표시됩니다. 다른 컴퓨터나 휴대폰에서 접속하려면 백엔드를 `0.0.0.0` 또는 LAN IP로 열고, 프론트엔드 API 주소도 해당 IP로 빌드해야 합니다.

## 웹 로컬 개발

```powershell
cd web
npm install
npm run dev
```

## 모바일

기본 API 주소는 `http://127.0.0.1:8000`입니다. 실제 휴대폰에서 테스트할 때는 휴대폰이 바라보는 `127.0.0.1`이 휴대폰 자기 자신이므로, 컴퓨터의 LAN IP를 사용해야 합니다.

Expo 예시:

```powershell
$env:EXPO_PUBLIC_API_BASE_URL="http://192.168.0.10:8000"
cd mobile
npm start
```

Flutter 예시:

```powershell
cd mobile_flutter
..\.tools\flutter\bin\flutter.bat run -d web-server --web-hostname 127.0.0.1 --web-port 5000 --dart-define=API_BASE_URL=http://127.0.0.1:8000
```

## 메뉴 수집 방식

- 서울캠퍼스 메뉴는 상명대학교 식당 페이지의 텍스트 정보를 수집합니다.
- 천안캠퍼스 메뉴는 게시물/이미지 기반 자료를 수집한 뒤 OCR로 텍스트를 추출합니다.
- 수집된 메뉴와 푸시 구독 정보는 `backend/smubab.db` SQLite 파일에 저장됩니다.
- 평일에는 현재 주 메뉴를 캐시하고, 주말에는 다음 주 게시물 여부를 주기적으로 확인하도록 구성되어 있습니다.

## 현재 상태

자세한 진행 상태는 [STATUS.md](STATUS.md)를 확인하세요.
