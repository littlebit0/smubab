# Netlify 배포 가이드

## 1. 프론트엔드 배포 (Netlify)

### Netlify 사이트 생성
1. [Netlify](https://app.netlify.com/) 로그인
2. "Add new site" → "Import an existing project" 선택
3. GitHub 저장소 연결: `littlebit0/smubab`
4. 빌드 설정은 자동으로 `netlify.toml`에서 읽어옴

### 환경 변수 설정
Netlify 사이트 설정에서:
- Site settings → Environment variables
- `VITE_API_URL` = 백엔드 API URL (예: `https://smubab-api.onrender.com`)

### 자동 배포
- `main` 브랜치에 push하면 자동으로 배포됩니다.

## 2. 백엔드 배포 (추천: Render/Railway/Fly.io)

### Render.com 사용 예시
1. [Render](https://render.com/) 로그인
2. "New Web Service" 선택
3. GitHub 저장소 연결
4. 설정:
   - **Name**: smubab-api
   - **Root Directory**: `backend`
    - **Build Command**: `apt-get update && apt-get install -y tesseract-ocr tesseract-ocr-kor && pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type**: Free

5. 배포 후 URL을 Netlify 환경 변수(`VITE_API_URL`)에 설정

### Railway.app 사용 예시
1. [Railway](https://railway.app/) 로그인
2. "New Project" → "Deploy from GitHub repo"
3. 저장소 선택 후 자동 감지
4. Root directory를 `backend`로 설정
5. 환경 변수 설정 (필요시)

### Fly.io 사용 예시
```bash
# Fly CLI 설치 후
cd backend
fly auth login
fly launch
fly deploy
```

## 3. CORS 설정

백엔드의 `main.py`에서 CORS 설정 확인:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://your-netlify-site.netlify.app",  # Netlify URL
        "http://localhost:3000"  # 개발용
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 4. 배포 확인

1. Netlify 사이트 방문
2. 브라우저 개발자 도구 (F12) 확인
3. Network 탭에서 API 호출 확인
4. 메뉴가 정상적으로 표시되는지 확인

## 문제 해결

### "Failed to load menus" 오류
- Netlify 환경 변수에 `VITE_API_URL`이 설정되어 있는지 확인
- 백엔드 API가 정상 작동하는지 확인 (브라우저에서 직접 접속)
- CORS 설정이 올바른지 확인

### 페이지 새로고침 시 404 오류
- `netlify.toml`의 redirects 설정이 있는지 확인
- SPA 라우팅을 위해 모든 경로를 `index.html`로 리다이렉트 필요

### 이미지나 에셋이 로드되지 않음
- Vite 빌드가 정상적으로 완료되었는지 확인
- `dist` 폴더가 제대로 생성되었는지 확인
