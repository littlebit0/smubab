# Crawler 업데이트 가이드

## 🔧 실제 상명대학교 웹사이트 크롤링 구현하기

### 1. 웹사이트 구조 분석

```bash
# 웹사이트 HTML 구조 확인
curl -s "https://www.smu.ac.kr/kor/life/restaurantView.do" | head -100
```

브라우저 개발자 도구로 HTML 구조를 분석하여:
- 메뉴 테이블/리스트의 클래스명
- 식당명 위치
- 메뉴 아이템 구조
- 가격 정보 위치

### 2. 서울캠퍼스 크롤링 구현

`crawler.py`의 `_crawl_seoul_campus()` 메서드에서:

```python
def _crawl_seoul_campus(self, target_date: date) -> List[Menu]:
    menus = []
    response = requests.get(self.seoul_url, headers=self.headers, timeout=10)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # 예시: 메뉴 테이블 찾기
    menu_table = soup.find('table', class_='식단표_클래스명')
    if not menu_table:
        return menus
    
    # 요일별로 파싱
    rows = menu_table.find_all('tr')
    for row in rows:
        cells = row.find_all('td')
        # 날짜, 식사타입, 메뉴 추출
        # ...
    
    return menus
```

### 3. 천안캠퍼스 이미지 기반 크롤링

게시판에서 최신 게시물의 이미지를 다운로드하고 OCR 처리:

```python
def _crawl_cheonan_faculty(self, target_date: date) -> List[Menu]:
    menus = []
    response = requests.get(self.cheonan_faculty_url, headers=self.headers, timeout=10)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # 게시글 목록에서 최신 글 찾기
    post_link = soup.find('a', class_='게시글_링크_클래스')
    if not post_link:
        return menus
    
    # 게시글 상세 페이지로 이동
    post_url = self.base_url + post_link['href']
    post_response = requests.get(post_url, headers=self.headers, timeout=10)
    post_soup = BeautifulSoup(post_response.content, 'html.parser')
    
    # 이미지 URL 추출
    image_urls = self._extract_image_urls(post_soup)
    
    # 각 이미지에서 텍스트 추출
    for img_url in image_urls:
        text = self._extract_text_from_image(img_url)
        if text:
            menu = self._parse_menu_text(text, target_date, Restaurant.CHEONAN_FACULTY)
            if menu:
                menus.append(menu)
    
    return menus
```

### 4. OCR 설정 (Tesseract)

Tesseract OCR이 설치되어 있어야 합니다:

```bash
# 설치 스크립트 실행
cd backend
./install_tesseract.sh

# 또는 수동 설치
# Ubuntu/Debian
sudo apt-get install tesseract-ocr tesseract-ocr-kor

# Mac
brew install tesseract tesseract-lang

# Windows
# https://github.com/UB-Mannheim/tesseract/wiki 참조
```

### 5. 테스트

```python
# 크롤러 테스트
from crawler import SMUCafeteriaCrawler
from datetime import date

crawler = SMUCafeteriaCrawler()

# 오늘 메뉴 크롤링
menus = crawler.crawl_daily_menu(date.today())
print(f"Crawled {len(menus)} menus")
for menu in menus:
    print(f"{menu.restaurant} - {menu.meal_type}")
    for item in menu.items:
        print(f"  {item.name}: {item.price}원")
```

### 6. 주의사항

- **robots.txt 확인**: 크롤링이 허용되는지 확인
- **요청 간격**: 너무 빈번한 요청으로 서버에 부담 주지 않기
- **에러 처리**: 웹사이트 구조 변경 시 대비
- **한국어 OCR**: Tesseract 한국어 데이터 필수

### 7. 디버깅

```python
# HTML 구조 확인
import requests
from bs4 import BeautifulSoup

url = "https://www.smu.ac.kr/kor/life/restaurantView.do"
response = requests.get(url)
soup = BeautifulSoup(response.content, 'html.parser')

# 모든 테이블 출력
tables = soup.find_all('table')
print(f"Found {len(tables)} tables")

# 클래스가 있는 div 출력
divs = soup.find_all('div', class_=True)
for div in divs[:10]:
    print(div.get('class'))
```

### 8. 추가 기능 아이디어

- 메뉴 변경 알림
- 인기 메뉴 통계
- 메뉴 평점 시스템
- 영양 정보 추가
- 메뉴 검색 기능
