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
- `BACKEND_API_URL` = 백엔드 API URL (예: `http://20.196.128.122:8000`)

### 자동 배포
- `main` 브랜치에 push하면 자동으로 배포됩니다.

## 2. 백엔드 배포 (Azure VM)

### Azure VM 설정
백엔드는 Azure Windows Server에서 24/7 운영 중입니다.

**서버 정보:**
- **URL**: http://20.196.128.122:8000
- **VM**: Windows Server 2025 (Azure Korea Central)
- **Python**: 3.14+
- **서버**: FastAPI + Uvicorn

### 수동 배포 (VM에서)
```bash
cd C:\Users\littlebit\.openclaw\workspace\smubab\backend
git pull origin main
pip install -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

### 자동 시작 설정
VM 재부팅 시 자동으로 서버가 시작되도록 설정:
```bash
# start-backend.bat 실행
C:\Users\littlebit\.openclaw\workspace\smubab\backend\start-backend.bat
```

### 환경 변수 (선택)
- **웹 푸시 알림용**:
  - `VAPID_PUBLIC_KEY`: VAPID 공개키
  - `VAPID_PRIVATE_KEY`: VAPID 비공개키
  - `VAPID_CLAIMS_SUB`: `mailto:your-email@example.com`
- **천안캠 OCR용**:
  - `OCR_SPACE_API_KEY`: [OCR.space](https://ocr.space/ocrapi)에서 무료 발급

### Netlify 환경 변수 설정
Netlify에서 백엔드 URL 설정:
```
BACKEND_API_URL=http://20.196.128.122:8000
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
- Netlify 환경 변수에 `BACKEND_API_URL`이 설정되어 있는지 확인
- 백엔드 API가 정상 작동하는지 확인: http://20.196.128.122:8000/api/health
- CORS 설정이 올바른지 확인

### 페이지 새로고침 시 404 오류
- `netlify.toml`의 redirects 설정이 있는지 확인
- SPA 라우팅을 위해 모든 경로를 `index.html`로 리다이렉트 필요

### 이미지나 에셋이 로드되지 않음
- Vite 빌드가 정상적으로 완료되었는지 확인
- `dist` 폴더가 제대로 생성되었는지 확인
