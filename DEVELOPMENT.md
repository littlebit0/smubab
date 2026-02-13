# 개발 가이드

## 시작하기

### 1. 백엔드 서버 실행

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

백엔드 서버가 `http://localhost:8000`에서 실행됩니다.

API 문서는 `http://localhost:8000/docs`에서 확인할 수 있습니다.

### 2. 모바일 앱 실행

새 터미널에서:

```bash
cd mobile
npm install
npm start
```

Expo Go 앱에서 QR 코드를 스캔하여 앱을 실행합니다.

**중요**: 모바일 앱에서 백엔드 API에 접근하려면:

1. 자신의 로컬 IP 주소를 확인합니다:
   ```bash
   # Linux/Mac
   ifconfig | grep inet
   
   # Windows
   ipconfig
   ```

2. `mobile/src/api/menuAPI.ts` 파일에서 API 주소를 로컬 IP로 변경합니다:
   ```typescript
   const API_BASE_URL = 'http://192.168.0.10:8000';  // 자신의 IP로 변경
   ```

## 메뉴 데이터

백엔드는 외부 수집 기능 없이 내부 기본 메뉴 데이터를 생성하여 제공합니다.

- 서버 시작 시 해당 주(월~금) 메뉴를 자동 생성합니다.
- `POST /api/menus/refresh` 호출 시 기본 메뉴를 재생성합니다.

## 데이터베이스 변경

현재는 인메모리 데이터베이스를 사용합니다. 프로덕션 환경에서는 SQLite나 PostgreSQL을 사용하세요.

### SQLite 사용 예시

`backend/database.py`를 SQLAlchemy를 사용하도록 변경:

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./smubab.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
```

## 알림 테스트

모바일 앱의 알림 기능을 테스트하려면:

1. 실제 기기에서 테스트 (시뮬레이터는 알림 제한이 있을 수 있음)
2. 앱 설정에서 알림 권한 허용
3. 설정 화면에서 원하는 알림 활성화
4. 테스트를 위해 시간을 가까운 미래로 설정

## 배포

### 백엔드 배포

- AWS EC2, Heroku, DigitalOcean 등의 클라우드 서비스 사용
- Gunicorn 또는 Uvicorn으로 프로덕션 서버 실행
- Nginx를 리버스 프록시로 사용
- HTTPS 설정 (Let's Encrypt)

### 모바일 앱 배포

```bash
# Android
eas build --platform android

# iOS
eas build --platform ios
```

Expo Application Services (EAS)를 사용하여 빌드하고 앱 스토어에 배포할 수 있습니다.

## 문제 해결

### 백엔드 연결 안 됨

- 방화벽 확인
- 백엔드 서버가 `0.0.0.0`으로 실행 중인지 확인
- 모바일 기기와 PC가 같은 네트워크에 있는지 확인

### 메뉴 데이터가 비어 보일 때

- 백엔드 서버 재시작 후 `POST /api/menus/refresh` 호출
- `GET /api/menus/week` 응답 확인

## 추가 개선 사항

- [ ] 사용자 리뷰/평점 기능
- [ ] 좋아하는 메뉴 저장
- [ ] 식당 혼잡도 정보
- [ ] 영양 정보 표시
- [ ] 다크 모드 지원
- [ ] 다국어 지원
