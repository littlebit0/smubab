import requests
from bs4 import BeautifulSoup
from datetime import date, datetime, timedelta
from typing import List, Dict, Optional
import logging
import re
from io import BytesIO
from PIL import Image
import pytesseract
import time

from models import Menu, MenuItem, MealType, Restaurant

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SMUCafeteriaCrawler:
    """상명대학교 학식 크롤러"""
    
    def __init__(self):
        self.base_url = "https://www.smu.ac.kr"
        self.seoul_url = f"{self.base_url}/kor/life/restaurantView.do"
        self.cheonan_faculty_url = f"{self.base_url}/kor/life/restaurantView3.do"
        self.cheonan_student_url = f"{self.base_url}/kor/life/restaurantView4.do"
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        # 크롤링 설정
        self.max_retries = 3
        self.timeout = 20
        self.retry_delay = 2
    
    def crawl_daily_menu(self, target_date: date = None) -> List[Menu]:
        """특정 날짜의 식단 정보를 크롤링합니다."""
        if target_date is None:
            target_date = date.today()
        
        menus = []
        
        try:
            # 서울캠퍼스 메뉴 크롤링
            logger.info(f"Crawling Seoul campus menu for {target_date}")
            seoul_menus = self._crawl_seoul_campus(target_date)
            menus.extend(seoul_menus)
            
            # 천안캠퍼스 메뉴 크롤링 (현재 게시판 형식이라 임시로 샘플 데이터 사용)
            logger.info(f"Adding Cheonan sample menus for {target_date}")
            cheonan_menus = self._get_cheonan_sample_menus(target_date)
            menus.extend(cheonan_menus)
            
            logger.info(f"Total {len(menus)} menus crawled for {target_date}")
            
            # 메뉴가 없으면 샘플 데이터 반환
            if not menus:
                logger.warning("No menus found, returning sample data")
                return self._get_sample_menu(target_date)
            
            return menus
            
        except Exception as e:
            logger.error(f"Error crawling menu: {e}")
            return self._get_sample_menu(target_date)
    
    def crawl_weekly_menu(self, target_date: date = None) -> List[Menu]:
        """주간 식단 정보를 크롤링합니다 (해당 주의 월~금)."""
        if target_date is None:
            target_date = date.today()
        
        # 해당 날짜가 속한 주의 월요일 계산
        weekday = target_date.weekday()  # 0=월요일, 6=일요일
        monday = target_date - timedelta(days=weekday)
        friday = monday + timedelta(days=4)
        
        logger.info(f"Crawling weekly menu: {monday} ~ {friday}")
        
        # 서울캠퍼스는 주간 테이블이므로 한 번만 크롤링
        # crawl_daily_menu가 이미 해당 주의 모든 메뉴를 반환함
        all_menus = self.crawl_daily_menu(target_date)
        
        # 월~금 메뉴만 필터링 및 중복 제거
        seen = set()
        weekly_menus = []
        for menu in all_menus:
            # 월~금만 포함 (주말 제외)
            if monday <= menu.date <= friday:
                key = (menu.date, menu.restaurant, menu.meal_type)
                if key not in seen:
                    seen.add(key)
                    weekly_menus.append(menu)
        
        logger.info(f"Filtered {len(weekly_menus)} menus for Mon-Fri")
        return weekly_menus
    

    
    def _crawl_seoul_campus(self, target_date: date) -> List[Menu]:
        """서울캠퍼스 식당 메뉴 크롤링"""
        menus = []
        
        # 해당 주의 월요일 계산 (조식 샘플 생성용)
        weekday = target_date.weekday()
        monday = target_date - timedelta(days=weekday)
        
        try:
            # 재시도 로직
            response = None
            for attempt in range(self.max_retries):
                try:
                    response = requests.get(self.seoul_url, headers=self.headers, timeout=self.timeout)
                    response.raise_for_status()
                    break
                except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                    if attempt < self.max_retries - 1:
                        logger.warning(f"Seoul campus: Retry {attempt + 1}/{self.max_retries} after {e}")
                        time.sleep(self.retry_delay)
                    else:
                        raise
            
            if not response:
                return menus
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            logger.info(f"Seoul campus: parsed HTML, length={len(response.content)}")
            
            # 두 번째 테이블이 실제 식단표
            tables = soup.find_all('table')
            if len(tables) < 2:
                logger.warning("Seoul campus: 식단표 테이블을 찾을 수 없습니다")
                return menus
            
            menu_table = tables[1]
            rows = menu_table.find_all('tr')
            
            if len(rows) < 2:
                logger.warning("Seoul campus: 테이블 행이 부족합니다")
                return menus
            
            # 첫 번째 행: 날짜 헤더
            header_row = rows[0]
            header_cells = header_row.find_all(['th', 'td'])
            
            # 두 번째 행: 메뉴 내용
            menu_row = rows[1]
            menu_cells = menu_row.find_all(['th', 'td'])
            
            # 첫 번째 셀에서 식당 종류 확인
            restaurant_type = Restaurant.SEOUL_STUDENT  # 기본값
            if menu_cells[0].get_text(strip=True):
                restaurant_label = menu_cells[0].get_text(strip=True)
                if '교직원' in restaurant_label or '교수' in restaurant_label:
                    restaurant_type = Restaurant.SEOUL_FACULTY
                elif '푸드코트' in restaurant_label or '코너' in restaurant_label:
                    restaurant_type = Restaurant.SEOUL_FOODCOURT
            
            # 날짜와 메뉴 매칭 - 테이블의 모든 날짜 파싱
            for i in range(1, min(len(header_cells), len(menu_cells))):
                date_text = header_cells[i].get_text(strip=True)
                menu_text = menu_cells[i].get_text(strip=True)
                
                if not menu_text:
                    continue
                
                # 날짜 파싱 (예: "월(02.09)")
                date_match = re.search(r'\((\d{2})\.(\d{2})\)', date_text)
                if date_match:
                    menu_month = int(date_match.group(1))
                    menu_day = int(date_match.group(2))
                    
                    # 연도 추론: target_date의 연도 사용
                    menu_year = target_date.year
                    
                    # 만약 월이 12월이고 target_date가 1월이면 이전 연도
                    if menu_month == 12 and target_date.month == 1:
                        menu_year = target_date.year - 1
                    # 만약 월이 1월이고 target_date가 12월이면 다음 연도
                    elif menu_month == 1 and target_date.month == 12:
                        menu_year = target_date.year + 1
                    
                    try:
                        menu_date = date(menu_year, menu_month, menu_day)
                    except ValueError:
                        logger.warning(f"Invalid date: {menu_year}-{menu_month:02d}-{menu_day:02d}")
                        continue
                    
                    # 메뉴 아이템 파싱
                    parsed_items = self._parse_menu_text(menu_text)
                    
                    # Dict를 MenuItem 객체로 변환
                    menu_items = [MenuItem(**item) for item in parsed_items]
                    
                    # Menu 객체 생성
                    if menu_items:
                        menu = Menu(
                            date=menu_date,
                            restaurant=restaurant_type,
                            meal_type=MealType.LUNCH,  # 기본값
                            items=menu_items
                        )
                        menus.append(menu)
                        logger.info(f"Seoul: {restaurant_type.value} {menu_date} - {len(menu_items)} items")
            
            # 서울캠 조식 샘플 추가 (주간 메뉴 테이블에 조식 정보가 없으므로)
            for i in range(5):
                breakfast_date = monday + timedelta(days=i)
                menus.append(Menu(
                    date=breakfast_date,
                    restaurant=Restaurant.SEOUL_STUDENT,
                    meal_type=MealType.BREAKFAST,
                    items=[
                        MenuItem(name="토스트", price=None),
                        MenuItem(name="시리얼", price=None),
                        MenuItem(name="우유", price=None),
                        MenuItem(name="과일", price=None),
                    ]
                ))
            
        except Exception as e:
            logger.error(f"Error crawling Seoul campus: {e}")
            import traceback
            traceback.print_exc()
        
        return menus
    
    def _crawl_cheonan_campus(self, target_date: date, url: str, restaurant: Restaurant) -> List[Menu]:
        """천안캠퍼스 식당 메뉴 크롤링 (게시판 형식)"""
        menus = []
        
        try:
            # 재시도 로직
            response = None
            for attempt in range(self.max_retries):
                try:
                    response = requests.get(url, headers=self.headers, timeout=self.timeout)
                    response.raise_for_status()
                    break
                except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                    if attempt < self.max_retries - 1:
                        logger.warning(f"{restaurant.value}: Retry {attempt + 1}/{self.max_retries} after {e}")
                        time.sleep(self.retry_delay)
                    else:
                        raise
            
            if not response:
                return menus
            
            soup = BeautifulSoup(response.content, 'html.parser')
            logger.info(f"{restaurant.value}: parsed HTML, length={len(response.content)}")
            
            # 게시판 게시물 링크 찾기 - 가장 최근 게시물
            # mode=view가 포함된 a 태그 찾기
            article_links = soup.find_all('a', href=True)
            article_links = [link for link in article_links if 'mode=view' in link.get('href', '')]
            
            if not article_links:
                logger.warning(f"{restaurant.value}: 게시물을 찾을 수 없습니다")
                return menus
            
            logger.info(f"{restaurant.value}: {len(article_links)}개의 게시물 찾음")
            
            # 첫 번째 게시물 (가장 최근)
            first_link = article_links[0]
            article_url = first_link.get('href')
            
            # 상대 URL을 절대 URL로 변환
            if not article_url.startswith('http'):
                article_url = url.split('?')[0] + article_url.replace('&amp;', '&')
            
            logger.info(f"{restaurant.value}: 게시물 URL: {article_url}")
            
            # 게시물 페이지 크롤링
            article_response = requests.get(article_url, headers=self.headers, timeout=self.timeout)
            article_response.raise_for_status()
            article_soup = BeautifulSoup(article_response.content, 'html.parser')
            
            # 게시물 내용에서 테이블 찾기
            tables = article_soup.find_all('table')
            
            for table in tables:
                rows = table.find_all('tr')
                if len(rows) < 2:
                    continue
                
                # 첫 번째 행: 날짜 헤더
                header_row = rows[0]
                header_cells = header_row.find_all(['th', 'td'])
                
                # 두 번째 행부터: 메뉴 내용
                for row_idx in range(1, len(rows)):
                    menu_row = rows[row_idx]
                    menu_cells = menu_row.find_all(['th', 'td'])
                    
                    # 날짜와 메뉴 매칭
                    for i in range(1, min(len(header_cells), len(menu_cells))):
                        date_text = header_cells[i].get_text(strip=True)
                        menu_text = menu_cells[i].get_text(strip=True)
                        
                        if not menu_text:
                            continue
                        
                        # 날짜 파싱
                        date_match = re.search(r'(\d{1,2})[./](\d{1,2})', date_text)
                        if date_match:
                            menu_month = int(date_match.group(1))
                            menu_day = int(date_match.group(2))
                            
                            # 연도 추론
                            menu_year = target_date.year
                            if menu_month == 12 and target_date.month == 1:
                                menu_year = target_date.year - 1
                            elif menu_month == 1 and target_date.month == 12:
                                menu_year = target_date.year + 1
                            
                            try:
                                menu_date = date(menu_year, menu_month, menu_day)
                            except ValueError:
                                continue
                            
                            # 메뉴 아이템 파싱
                            parsed_items = self._parse_menu_text(menu_text)
                            menu_items = [MenuItem(**item) for item in parsed_items]
                            
                            if menu_items:
                                menu = Menu(
                                    date=menu_date,
                                    restaurant=restaurant,
                                    meal_type=MealType.LUNCH,
                                    items=menu_items
                                )
                                menus.append(menu)
                                logger.info(f"{restaurant.value}: {menu_date} - {len(menu_items)} items")
            
            if not menus:
                logger.warning(f"{restaurant.value}: 테이블에서 메뉴를 추출하지 못했습니다")
            
        except Exception as e:
            logger.error(f"Error crawling {restaurant.value}: {e}")
            import traceback
            traceback.print_exc()
        
        return menus
    
    def _extract_image_urls(self, soup: BeautifulSoup) -> List[str]:
        """게시물에서 이미지 URL 추출"""
        image_urls = []
        
        images = soup.find_all('img')
        for img in images:
            src = img.get('src')
            if src:
                if src.startswith('http'):
                    image_urls.append(src)
                else:
                    image_urls.append(self.base_url + src)
        
        return image_urls
    
    def _extract_text_from_image(self, image_url: str) -> str:
        """이미지에서 OCR을 사용하여 텍스트 추출"""
        try:
            response = requests.get(image_url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            image = Image.open(BytesIO(response.content))
            
            # OCR 실행 (한국어 + 영어)
            text = pytesseract.image_to_string(image, lang='kor+eng')
            
            logger.info(f"Extracted text from image: {text[:100]}...")
            return text
            
        except Exception as e:
            logger.error(f"Error extracting text from image {image_url}: {e}")
            return ""
    
    def _parse_menu_text(self, text: str, target_date: date = None, restaurant: Restaurant = None) -> List[Dict]:
        """추출된 텍스트에서 메뉴 정보 파싱
        
        서울캠퍼스: "잡곡밥경상도식소고기무국돈육메추리알장조림" 형태
        천안캠퍼스: OCR로 추출된 줄바꿈 있는 텍스트
        """
        items = []
        
        try:
            # 줄바꿈이 있으면 라인별로 처리
            if '\n' in text:
                lines = text.strip().split('\n')
                for line in lines:
                    line = line.strip()
                    if line and len(line) > 1:
                        # 가격 패턴 찾기
                        price_match = re.search(r'(\d{1,3}(?:,\d{3})*)\s*원', line)
                        price = int(price_match.group(1).replace(',', '')) if price_match else None
                        
                        # 메뉴 이름
                        name = re.sub(r'\d{1,3}(?:,\d{3})*\s*원', '', line).strip()
                        
                        if name:
                            items.append({"name": name, "price": price, "calories": None})
            else:
                # 서울캠퍼스: 공백 없는 텍스트 파싱
                # 키워드로 분리 (밥, 국, 찌개, 조림, 구이, 볶음 등)
                keywords = ['밥', '국', '찌개', '탕', '찜', '조림', '볶음', '무침', '구이', '전', 
                           '튀김', '회', '샐러드', '스프', '파스타', '스테이크', '덮밥', '면']
                
                # 임시로 키워드 뒤에 구분자 추가
                temp_text = text
                for keyword in keywords:
                    temp_text = temp_text.replace(keyword, f'{keyword}|')
                
                # 파이프로 분리
                parts = [p.strip() for p in temp_text.split('|') if p.strip()]
                
                # 메뉴 아이템으로 변환
                for part in parts:
                    if len(part) > 1:
                        # 가격 추출
                        price_match = re.search(r'(\d{1,3}(?:,\d{3})*)\s*원', part)
                        price = int(price_match.group(1).replace(',', '')) if price_match else None
                        
                        name = re.sub(r'\d{1,3}(?:,\d{3})*\s*원', '', part).strip()
                        
                        if name:
                            items.append({"name": name, "price": price, "calories": None})
        
        except Exception as e:
            logger.error(f"Error parsing menu text: {e}")
        
        return items if items else [{"name": text[:50], "price": None, "calories": None}]
    
    def _get_cheonan_sample_menus(self, target_date: date) -> List[Menu]:
        """천안캠퍼스 샘플 메뉴 데이터를 반환합니다 (월~금 생성)."""
        menus = []
        
        # 해당 주의 월요일 계산
        weekday = target_date.weekday()
        monday = target_date - timedelta(days=weekday)
        
        # 월~금 5일간 메뉴 생성
        for i in range(5):
            menu_date = monday + timedelta(days=i)
            
            # 교직원 식당 - 조식
            menus.append(Menu(
                date=menu_date,
                restaurant=Restaurant.CHEONAN_FACULTY,
                meal_type=MealType.BREAKFAST,
                items=[
                    MenuItem(name="토스트", price=None),
                    MenuItem(name="계란후라이", price=None),
                    MenuItem(name="우유", price=None),
                    MenuItem(name="과일", price=None),
                ]
            ))
            
            # 교직원 식당 - 중식
            menus.append(Menu(
                date=menu_date,
                restaurant=Restaurant.CHEONAN_FACULTY,
                meal_type=MealType.LUNCH,
                items=[
                    MenuItem(name="쌀밥", price=None),
                    MenuItem(name="된장찌개", price=None),
                    MenuItem(name="불고기", price=None),
                    MenuItem(name="나물무침", price=None),
                    MenuItem(name="김치", price=None),
                ]
            ))
            
            # 학생 식당 - 조식
            menus.append(Menu(
                date=menu_date,
                restaurant=Restaurant.CHEONAN_STUDENT,
                meal_type=MealType.BREAKFAST,
                items=[
                    MenuItem(name="토스트", price=None),
                    MenuItem(name="시리얼", price=None),
                    MenuItem(name="우유", price=None),
                    MenuItem(name="요거트", price=None),
                ]
            ))
            
            # 학생 식당 - 중식
            menus.append(Menu(
                date=menu_date,
                restaurant=Restaurant.CHEONAN_STUDENT,
                meal_type=MealType.LUNCH,
                items=[
                    MenuItem(name="잡곡밥", price=None),
                    MenuItem(name="김치찌개", price=None),
                    MenuItem(name="돈까스", price=None),
                    MenuItem(name="샐러드", price=None),
                    MenuItem(name="배추김치", price=None),
                ]
            ))
        
        logger.info(f"Generated {len(menus)} Cheonan sample menus")
        return menus
    
    def _get_sample_menu(self, target_date: date) -> List[Menu]:
        """샘플 메뉴 데이터를 반환합니다."""
        sample_menus = [
            Menu(
                date=target_date,
                restaurant=Restaurant.SEOUL_STUDENT,
                meal_type=MealType.BREAKFAST,
                items=[
                    MenuItem(name="토스트", price=2000),
                    MenuItem(name="시리얼", price=1500),
                    MenuItem(name="우유", price=1000),
                ]
            ),
            Menu(
                date=target_date,
                restaurant=Restaurant.SEOUL_STUDENT,
                meal_type=MealType.LUNCH,
                items=[
                    MenuItem(name="제육볶음", price=5000),
                    MenuItem(name="김치찌개", price=4500),
                    MenuItem(name="돈까스", price=6000),
                    MenuItem(name="밥", price=1000),
                ]
            ),
            Menu(
                date=target_date,
                restaurant=Restaurant.SEOUL_STUDENT,
                meal_type=MealType.DINNER,
                items=[
                    MenuItem(name="불고기", price=6000),
                    MenuItem(name="된장찌개", price=4000),
                    MenuItem(name="생선구이", price=5500),
                ]
            ),
            Menu(
                date=target_date,
                restaurant=Restaurant.SEOUL_FACULTY,
                meal_type=MealType.LUNCH,
                items=[
                    MenuItem(name="스테이크", price=12000),
                    MenuItem(name="파스타", price=9000),
                    MenuItem(name="샐러드", price=7000),
                ]
            ),
            Menu(
                date=target_date,
                restaurant=Restaurant.SEOUL_FOODCOURT,
                meal_type=MealType.LUNCH,
                items=[
                    MenuItem(name="라면", price=3500),
                    MenuItem(name="김밥", price=3000),
                    MenuItem(name="떡볶이", price=4000),
                ]
            )
        ]
        
        logger.info(f"Returning {len(sample_menus)} sample menus for {target_date}")
        return sample_menus
    
    def _determine_meal_type(self, time_str: str) -> MealType:
        """시간 문자열로부터 식사 유형을 결정합니다."""
        if any(keyword in time_str for keyword in ['아침', '조식', 'breakfast']):
            return MealType.BREAKFAST
        elif any(keyword in time_str for keyword in ['점심', '중식', 'lunch']):
            return MealType.LUNCH
        elif any(keyword in time_str for keyword in ['저녁', '석식', 'dinner']):
            return MealType.DINNER
        return MealType.LUNCH
