# SMU-Bab Backend API

상명대학교 학식 정보를 제공하는 FastAPI 백엔드 서버입니다.

## 기능

- 상명대학교 학식 웹사이트 크롤링
- RESTful API 제공
- 자동 메뉴 업데이트 (매일 오전 6시)
- 식당별, 날짜별 메뉴 조회

## 설치

```bash
pip install -r requirements.txt
```

## 실행

```bash
# 개발 모드
uvicorn main:app --reload

# 프로덕션 모드
uvicorn main:app --host 0.0.0.0 --port 8000
```

## API 엔드포인트

### 메뉴 조회

- `GET /api/menus/today` - 오늘의 메뉴
- `GET /api/menus/date/{date}` - 특정 날짜의 메뉴
- `GET /api/menus/week` - 주간 메뉴
- `GET /api/menus/restaurant/{restaurant}` - 식당별 메뉴

### 기타

- `GET /api/restaurants` - 식당 목록
- `POST /api/menus/refresh` - 메뉴 강제 갱신
- `GET /api/health` - 헬스 체크

## API 문서

서버 실행 후 다음 URL에서 자동 생성된 API 문서를 확인할 수 있습니다:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 크롤링 커스터마이징

`crawler.py`의 `SMUCafeteriaCrawler` 클래스를 수정하여 실제 상명대학교 웹사이트 구조에 맞게 크롤링 로직을 구현하세요.

현재는 샘플 데이터를 반환하도록 되어 있습니다.

## 데이터베이스

현재는 인메모리 데이터베이스를 사용합니다. 프로덕션 환경에서는 SQLite나 PostgreSQL로 교체하는 것을 권장합니다.
