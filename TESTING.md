# 🧪 테스트 가이드

## 백엔드 테스트

### 1. 서버 시작
```bash
cd backend
./start.sh
# 또는
uvicorn main:app --reload --host 0.0.0.0
```

### 2. API 테스트

브라우저에서 API 문서로 이동: http://localhost:8000/docs

또는 curl로 테스트:

```bash
# Health Check
curl http://localhost:8000/api/health

# 오늘의 메뉴
curl http://localhost:8000/api/menus/today

# 주간 메뉴
curl http://localhost:8000/api/menus/week

# 식당 목록
curl http://localhost:8000/api/restaurants
```

### 3. 예상 결과

```json
{
  "success": true,
  "date": "2026-02-10",
  "menus": [
    {
      "date": "2026-02-10",
      "restaurant": "학생식당",
      "meal_type": "lunch",
      "items": [
        {
          "name": "제육볶음",
          "price": 5000
        }
      ]
    }
  ]
}
```

## 모바일 앱 테스트

### 1. IP 주소 확인

```bash
# Linux/Mac
ifconfig | grep "inet " | grep -v 127.0.0.1

# Windows (PowerShell)
ipconfig | findstr IPv4
```

### 2. API 주소 설정

`mobile/src/api/menuAPI.ts` 파일 수정:

```typescript
const API_BASE_URL = 'http://192.168.0.10:8000';  // 자신의 IP로 변경
```

### 3. 앱 시작

```bash
cd mobile
./start.sh
# 또는
npm start
```

### 4. 앱 실행

- Android/iOS에 Expo Go 앱 설치
- QR 코드 스캔
- 앱 실행 확인

## 일반적인 문제 해결

### 백엔드

**문제**: 포트 8000이 이미 사용 중
```bash
# 포트 사용 프로세스 확인
lsof -i :8000

# 프로세스 종료
kill -9 <PID>
```

**문제**: 모듈을 찾을 수 없음
```bash
pip install -r requirements.txt
```

### 모바일

**문제**: API 연결 실패
- 백엔드 서버가 실행 중인지 확인
- API_BASE_URL이 올바른 IP인지 확인
- 방화벽 설정 확인
- PC와 모바일이 같은 네트워크인지 확인

**문제**: Metro bundler 에러
```bash
cd mobile
rm -rf node_modules
npm install --legacy-peer-deps
npm start -- --reset-cache
```

**문제**: TypeScript 에러
```bash
cd mobile
npx tsc --noEmit  # 타입 체크만 실행
```

## 크롤링 커스터마이징

현재는 샘플 데이터를 반환합니다. 실제 상명대학교 웹사이트에 맞게 수정하려면:

1. 상명대학교 학식 페이지 URL 찾기
2. `backend/crawler.py`의 `cafeteria_url` 변경
3. HTML 구조 분석
4. `_parse_menu()` 메서드 구현

```python
def _parse_menu(self, soup: BeautifulSoup, target_date: date) -> List[Menu]:
    menus = []
    
    # 실제 HTML 구조에 맞게 수정
    menu_sections = soup.find_all('div', class_='menu-section')
    
    for section in menu_sections:
        # 파싱 로직 구현
        pass
    
    return menus
```

## 성능 테스트

### API 성능 테스트
```bash
# Apache Bench
ab -n 1000 -c 10 http://localhost:8000/api/menus/today

# 또는 Python으로
pip install locust
locust -f tests/locustfile.py
```

## 데이터베이스 확인

현재는 인메모리 DB 사용. 실제 데이터를 확인하려면:

```python
# Python 대화형 쉘
cd backend
python

>>> from database import db
>>> print(len(db.menus))
>>> print(db.menus[0])
```
