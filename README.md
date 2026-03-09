# SMU-Bab (상명대학교 학식 앱)

상명대학교의 식당 메뉴를 확인할 수 있는 모바일 애플리케이션입니다.

## 주요 기능

- 📅 오늘/이번주 메뉴 보기
- 🍽️ 식당별 메뉴 구분
- 💰 가격 정보 제공
- 🔔 알림 기능

## 프로젝트 구조

```
smubab/
├── backend/          # FastAPI 백엔드 서버 (메뉴 API)
├── mobile/           # React Native 모바일 앱
├── web/              # React 웹 애플리케이션
└── README.md
```

## 기술 스택

### 백엔드
- Python 3.11+
- FastAPI
- Pydantic
- SQLite / PostgreSQL

### 모바일
- React Native
- TypeScript
- React Navigation
- Axios

### 웹
- React 18
- TypeScript
- Vite
- Axios

## 시작하기

### 백엔드 실행
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### 모바일 앱 실행
```bash
cd mobile
npm install
npm start
```

### 웹 앱 실행
```bash
cd web
npm install
npm run dev
```

웹 앱: http://localhost:3000

## 개발 상태

✅ 백엔드 API 완료
✅ 웹 애플리케이션 완료
✅ 백엔드 기본 메뉴 API 제공
✅ 식당/식사유형별 메뉴 조회
🚧 모바일 앱 개발 예정

## 배포

### 프론트엔드 (Netlify)
[![Netlify Status](https://api.netlify.com/api/v1/badges/your-site-id/deploy-status)](https://app.netlify.com/sites/your-site-name/deploys)

프론트엔드는 Netlify에 배포됩니다. 자세한 배포 가이드는 [DEPLOYMENT.md](DEPLOYMENT.md)를 참조하세요.

### 백엔드 (Azure VM)
백엔드는 Azure VM에서 24/7 운영 중입니다.

**서버 정보:**
- URL: http://20.196.128.122:8000
- Python 3.14+
- FastAPI + Uvicorn
- 포트: 8000

**Netlify 환경 변수:**
```
BACKEND_API_URL=http://20.196.128.122:8000
```

## 라이센스

MIT License