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

## 크롤링 커스터마이징

상명대학교 실제 학식 웹사이트에 맞게 크롤링 로직을 수정해야 합니다.

1. 상명대학교 학식 페이지 URL 확인
2. `backend/crawler.py`의 `SMUCafeteriaCrawler` 클래스 수정:
   - `cafeteria_url` 변수를 실제 URL로 변경
   - `_parse_menu()` 메서드 구현

### 크롤링 예시

```python
def _parse_menu(self, soup: BeautifulSoup, target_date: date) -> List[Menu]:
    menus = []
    
    # 예시: HTML 구조에 맞게 파싱
    menu_sections = soup.find_all('div', class_='menu-card')
    
    for section in menu_sections:
        restaurant_name = section.find('h3', class_='restaurant').text.strip()
        
        # 식사 타입 결정
        meal_type = self._determine_meal_type(
            section.find('span', class_='time').text
        )
        
        # 메뉴 아이템 파싱
        items = []
        for item in section.find_all('li', class_='menu-item'):
            name = item.find('span', class_='name').text.strip()
            price_text = item.find('span', class_='price').text
            price = int(price_text.replace(',', '').replace('원', ''))
            
            items.append(MenuItem(name=name, price=price))
        
        menus.append(Menu(
            date=target_date,
            restaurant=Restaurant(restaurant_name),
            meal_type=meal_type,
            items=items
        ))
    
    return menus
```

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

### 크롤링 실패

- 웹사이트 구조 변경 확인
- User-Agent 헤더 확인
- 필요시 Selenium으로 변경

## 추가 개선 사항

- [ ] 사용자 리뷰/평점 기능
- [ ] 좋아하는 메뉴 저장
- [ ] 식당 혼잡도 정보
- [ ] 영양 정보 표시
- [ ] 다크 모드 지원
- [ ] 다국어 지원
