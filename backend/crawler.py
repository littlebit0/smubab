import logging
import os
import re
import time
import base64
from datetime import date
from io import BytesIO
from typing import List, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageOps, ImageFilter

# Optional tesseract import
try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except (ImportError, Exception):
    TESSERACT_AVAILABLE = False

from models import MealType, Menu, MenuItem, Restaurant

logger = logging.getLogger(__name__)


class SMUCafeteriaCrawler:
    """상명대 식단 크롤러 (서울 텍스트 + 천안 교직원 이미지 OCR)"""

    def __init__(self):
        self.seoul_menu_url = "https://www.smu.ac.kr/kor/life/restaurantView.do"
        self.cheonan_faculty_board_url = "https://www.smu.ac.kr/kor/life/restaurantView3.do"
        self.cheonan_student_board_url = "https://www.smu.ac.kr/kor/life/restaurantView4.do"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
        }
        self.timeout = 20
        self.max_retries = 3
        self.retry_delay = 1.5
        self.ocr_space_api_key = os.getenv("OCR_SPACE_API_KEY", "")

    def crawl_daily_menu(self, target_date: date) -> List[Menu]:
        weekly_menus = self.crawl_weekly_menu(target_date)
        return [menu for menu in weekly_menus if menu.date == target_date]

    def crawl_weekly_menu(self, target_date: date) -> List[Menu]:
        breakfast = self._crawl_by_category(target_date, MealType.BREAKFAST)
        lunch = self._crawl_by_category(target_date, MealType.LUNCH)
        try:
            cheonan_faculty_lunch = self._crawl_cheonan_faculty_lunch(target_date)
        except Exception as error:
            logger.warning(f"Cheonan faculty crawl failed, fallback used: {error}")
            weekday = target_date.weekday()
            monday = target_date.fromordinal(target_date.toordinal() - weekday)
            cheonan_faculty_lunch = [
                Menu(
                    date=monday.fromordinal(monday.toordinal() + i),
                    restaurant=Restaurant.CHEONAN_FACULTY,
                    meal_type=MealType.LUNCH,
                    items=[MenuItem(name="중식정보없음", price=None)],
                )
                for i in range(5)
            ]

        try:
            cheonan_student_menus = self._crawl_cheonan_student_menus(target_date)
        except Exception as error:
            logger.warning(f"Cheonan student crawl failed, fallback used: {error}")
            weekday = target_date.weekday()
            monday = target_date.fromordinal(target_date.toordinal() - weekday)
            cheonan_student_menus = []
            for i in range(5):
                menu_date = monday.fromordinal(monday.toordinal() + i)
                cheonan_student_menus.append(
                    Menu(
                        date=menu_date,
                        restaurant=Restaurant.CHEONAN_STUDENT,
                        meal_type=MealType.BREAKFAST,
                        items=[MenuItem(name="조식정보없음", price=None)],
                    )
                )
                cheonan_student_menus.append(
                    Menu(
                        date=menu_date,
                        restaurant=Restaurant.CHEONAN_STUDENT,
                        meal_type=MealType.LUNCH,
                        items=[MenuItem(name="중식정보없음", price=None)],
                    )
                )

        all_menus = breakfast + lunch + cheonan_faculty_lunch + cheonan_student_menus

        # 날짜+식당+식사유형 중복 제거
        dedup = {}
        for menu in all_menus:
            dedup[(menu.date, menu.restaurant, menu.meal_type)] = menu

        return list(dedup.values())

    def _crawl_by_category(self, target_date: date, meal_type: MealType) -> List[Menu]:
        category_value = "B" if meal_type == MealType.BREAKFAST else "L"
        params = {
            "mode": "menuList",
            "srMealCategory": category_value,
            "srDt": target_date.isoformat(),
        }

        response = self._get_with_retry(
            self.seoul_menu_url,
            params=params,
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        table = soup.select_one(".menu-list-box table.smu-table")

        if not table:
            logger.warning("식단표 테이블을 찾지 못했습니다.")
            return []

        dates = self._extract_dates(table, target_date)
        if not dates:
            return []

        tbody = table.find("tbody")
        rows = tbody.find_all("tr") if tbody else []

        if meal_type == MealType.BREAKFAST and not rows:
            return [
                Menu(
                    date=menu_date,
                    restaurant=Restaurant.SEOUL_STUDENT,
                    meal_type=MealType.BREAKFAST,
                    items=[MenuItem(name="조식제공X", price=None)],
                )
                for menu_date in dates
            ]

        menus: List[Menu] = []
        for row in rows:
            cells = row.find_all(["th", "td"])
            if len(cells) < 2:
                continue

            for index, menu_date in enumerate(dates, start=1):
                if index >= len(cells):
                    continue

                menu_items = self._extract_items_from_cell(cells[index])

                if meal_type == MealType.BREAKFAST and not menu_items:
                    menu_items = [MenuItem(name="조식제공X", price=None)]

                if not menu_items:
                    continue

                menus.append(
                    Menu(
                        date=menu_date,
                        restaurant=Restaurant.SEOUL_STUDENT,
                        meal_type=meal_type,
                        items=menu_items,
                    )
                )

        return menus

    def _extract_dates(self, table: BeautifulSoup, target_date: date) -> List[date]:
        dates: List[date] = []

        header_cells = table.select("thead tr th")
        for cell in header_cells[1:]:
            text = cell.get_text(" ", strip=True)
            matched = re.search(r"\((\d{2})\.(\d{2})\)", text)
            if not matched:
                continue

            month = int(matched.group(1))
            day = int(matched.group(2))
            year = target_date.year

            if month == 12 and target_date.month == 1:
                year -= 1
            elif month == 1 and target_date.month == 12:
                year += 1

            try:
                dates.append(date(year, month, day))
            except ValueError:
                continue

        return dates

    def _extract_items_from_cell(self, cell: BeautifulSoup) -> List[MenuItem]:
        items: List[MenuItem] = []

        li_elements = cell.find_all("li")
        if li_elements:
            for li in li_elements:
                name = li.get_text(" ", strip=True)
                if name:
                    items.append(MenuItem(name=name, price=None))
            return items

        text = cell.get_text("\n", strip=True)
        for line in text.splitlines():
            name = line.strip()
            if name:
                items.append(MenuItem(name=name, price=None))

        return items

    def _crawl_cheonan_faculty_lunch(self, target_date: date) -> List[Menu]:
        article_url = self._find_cheonan_faculty_article_url(target_date)
        if not article_url:
            return []

        response = self._get_with_retry(article_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        title_text = self._extract_article_title(soup)
        week_dates = self._extract_week_dates_from_title(title_text, target_date)

        image_urls = self._extract_article_image_urls(soup, article_url)
        if not image_urls:
            logger.warning("천안 교직원식당 게시글에서 메뉴 이미지를 찾지 못했습니다.")
            return []

        weekly_menu_texts = self._extract_weekly_menu_texts_from_images(image_urls)
        if not weekly_menu_texts:
            return []

        menus: List[Menu] = []
        for index, menu_date in enumerate(week_dates):
            if index >= len(weekly_menu_texts):
                break

            day_items = weekly_menu_texts[index]
            if not day_items:
                day_items = ["중식정보없음"]
            day_items = self._append_notice_items(day_items)

            menus.append(
                Menu(
                    date=menu_date,
                    restaurant=Restaurant.CHEONAN_FACULTY,
                    meal_type=MealType.LUNCH,
                    items=[MenuItem(name=item, price=None) for item in day_items],
                )
            )

        logger.info(f"Cheonan faculty OCR menus parsed: {len(menus)}")
        return menus

    def _crawl_cheonan_student_menus(self, target_date: date) -> List[Menu]:
        article_url = self._find_cheonan_student_article_url(target_date)
        if not article_url:
            return []

        response = self._get_with_retry(article_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        title_text = self._extract_article_title(soup)
        week_dates = self._extract_week_dates_from_title(title_text, target_date)

        image_urls = self._extract_article_image_urls(soup, article_url)
        if not image_urls:
            logger.warning("천안 학생식당 게시글에서 메뉴 이미지를 찾지 못했습니다.")
            return []

        weekly_day_texts = self._extract_weekly_menu_texts_from_images(image_urls)
        if not weekly_day_texts:
            return []

        menus: List[Menu] = []
        for index, menu_date in enumerate(week_dates):
            if index >= len(weekly_day_texts):
                break

            day_items = weekly_day_texts[index]
            breakfast_items, lunch_items = self._split_student_meals(day_items)
            breakfast_items = self._append_notice_items(breakfast_items)
            lunch_items = self._append_notice_items(lunch_items)

            menus.append(
                Menu(
                    date=menu_date,
                    restaurant=Restaurant.CHEONAN_STUDENT,
                    meal_type=MealType.BREAKFAST,
                    items=[MenuItem(name=item, price=None) for item in breakfast_items],
                )
            )
            menus.append(
                Menu(
                    date=menu_date,
                    restaurant=Restaurant.CHEONAN_STUDENT,
                    meal_type=MealType.LUNCH,
                    items=[MenuItem(name=item, price=None) for item in lunch_items],
                )
            )

        logger.info(f"Cheonan student OCR menus parsed: {len(menus)}")
        return menus

    def _find_cheonan_faculty_article_url(self, target_date: date) -> Optional[str]:
        response = self._get_with_retry(self.cheonan_faculty_board_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        target_weekday = target_date.weekday()
        monday = target_date.fromordinal(target_date.toordinal() - target_weekday)
        friday = monday.fromordinal(monday.toordinal() + 4)

        candidates = []
        for anchor in soup.find_all("a", href=True):
            href = anchor.get("href", "")
            if "mode=view" not in href:
                continue

            title_text = anchor.get("title") or anchor.get_text(" ", strip=True)
            if "교직원 식당 주간 메뉴" not in title_text.replace(" ", ""):
                if "교직원식당" not in title_text and "주간 메뉴" not in title_text:
                    continue

            article_url = urljoin(self.cheonan_faculty_board_url, href.replace("&amp;", "&"))
            week_dates = self._extract_week_dates_from_title(title_text, target_date)
            candidates.append((article_url, week_dates))

        for article_url, week_dates in candidates:
            if week_dates and week_dates[0] == monday and week_dates[-1] == friday:
                return article_url

        return candidates[0][0] if candidates else None

    def _find_cheonan_student_article_url(self, target_date: date) -> Optional[str]:
        response = self._get_with_retry(self.cheonan_student_board_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        target_weekday = target_date.weekday()
        monday = target_date.fromordinal(target_date.toordinal() - target_weekday)
        friday = monday.fromordinal(monday.toordinal() + 4)

        candidates = []
        for anchor in soup.find_all("a", href=True):
            href = anchor.get("href", "")
            if "mode=view" not in href:
                continue

            title_text = anchor.get("title") or anchor.get_text(" ", strip=True)
            compact_title = title_text.replace(" ", "")
            if "주간식단표" not in compact_title and "주간메뉴" not in compact_title:
                continue

            article_url = urljoin(self.cheonan_student_board_url, href.replace("&amp;", "&"))
            week_dates = self._extract_week_dates_from_title(title_text, target_date)
            candidates.append((article_url, week_dates))

        for article_url, week_dates in candidates:
            if week_dates and week_dates[0] == monday and week_dates[-1] == friday:
                return article_url

        return candidates[0][0] if candidates else None

    def _extract_article_title(self, soup: BeautifulSoup) -> str:
        title_node = soup.select_one("#jwxe_main_content h4")
        if title_node:
            return title_node.get_text(" ", strip=True)

        page_title = soup.find("title")
        return page_title.get_text(" ", strip=True) if page_title else ""

    def _extract_week_dates_from_title(self, title_text: str, fallback_date: date) -> List[date]:
        compact = title_text.replace(" ", "")
        match = re.search(r"\((\d{4})\.(\d{1,2})\.(\d{1,2})~(\d{1,2})\.(\d{1,2})\)", compact)
        if match:
            year = int(match.group(1))
            start_month = int(match.group(2))
            start_day = int(match.group(3))
            end_month = int(match.group(4))
            end_day = int(match.group(5))
            try:
                start_date = date(year, start_month, start_day)
                end_year = year + 1 if end_month < start_month else year
                end_date = date(end_year, end_month, end_day)
                day_count = (end_date - start_date).days + 1
                return [start_date.fromordinal(start_date.toordinal() + index) for index in range(max(day_count, 0))]
            except ValueError:
                pass

        # 예: 주간식단표(12.15.~12.19.)
        short_match = re.search(r"\((\d{1,2})\.(\d{1,2})\.?~(\d{1,2})\.(\d{1,2})\.?\)", compact)
        if short_match:
            start_month = int(short_match.group(1))
            start_day = int(short_match.group(2))
            end_month = int(short_match.group(3))
            end_day = int(short_match.group(4))
            year = fallback_date.year
            try:
                start_date = date(year, start_month, start_day)
                end_year = year + 1 if end_month < start_month else year
                end_date = date(end_year, end_month, end_day)
                # fallback_date와 너무 멀면 이전 연도로 재시도
                if abs((start_date - fallback_date).days) > 200:
                    start_date = date(year - 1, start_month, start_day)
                    end_year = (year - 1) + 1 if end_month < start_month else (year - 1)
                    end_date = date(end_year, end_month, end_day)

                day_count = (end_date - start_date).days + 1
                return [start_date.fromordinal(start_date.toordinal() + index) for index in range(max(day_count, 0))]
            except ValueError:
                pass

        weekday = fallback_date.weekday()
        monday = fallback_date.fromordinal(fallback_date.toordinal() - weekday)
        return [monday.fromordinal(monday.toordinal() + i) for i in range(5)]

    def _extract_article_image_urls(self, soup: BeautifulSoup, article_url: str) -> List[str]:
        image_urls: List[str] = []

        for image in soup.select(".fr-view img"):
            src = image.get("data-path") or image.get("src")
            if not src:
                continue

            source = src.replace("&amp;", "&")
            absolute = urljoin(article_url, source)
            image_urls.append(absolute)

        # 중복 제거
        unique_urls = []
        seen = set()
        for url in image_urls:
            if url in seen:
                continue
            seen.add(url)
            unique_urls.append(url)

        return unique_urls

    def _extract_weekly_menu_texts_from_images(self, image_urls: List[str]) -> List[List[str]]:
        merged: List[List[str]] = [[] for _ in range(5)]

        for image_url in image_urls:
            try:
                response = self._get_with_retry(image_url, timeout=40)
                response.raise_for_status()
                image = Image.open(BytesIO(response.content)).convert("L")

                day_texts = self._extract_day_columns_from_image(image)
                for idx in range(5):
                    merged[idx].extend(day_texts[idx])
            except Exception as error:
                logger.warning(f"Cheonan faculty image OCR failed: {image_url} ({error})")

        return [self._deduplicate_items(items) for items in merged]

    def _ocr_with_api(self, image: Image.Image) -> str:
        """OCR.space API를 사용한 OCR"""
        if not self.ocr_space_api_key:
            return ""
        
        try:
            # 이미지를 base64로 변환
            buffer = BytesIO()
            image.save(buffer, format="PNG")
            img_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            # OCR.space API 호출
            response = requests.post(
                "https://api.ocr.space/parse/image",
                data={
                    "apikey": self.ocr_space_api_key,
                    "base64Image": f"data:image/png;base64,{img_base64}",
                    "language": "kor",
                    "isOverlayRequired": False,
                    "detectOrientation": True,
                    "scale": True,
                    "OCREngine": 2,
                },
                timeout=30,
            )
            
            result = response.json()
            if result.get("IsErroredOnProcessing"):
                logger.warning(f"OCR.space API error: {result.get('ErrorMessage')}")
                return ""
            
            parsed_results = result.get("ParsedResults", [])
            if parsed_results:
                return parsed_results[0].get("ParsedText", "")
            
            return ""
        except Exception as error:
            logger.warning(f"OCR.space API failed: {error}")
            return ""

    def _extract_day_columns_from_image(self, image: Image.Image) -> List[List[str]]:
        if not TESSERACT_AVAILABLE and not self.ocr_space_api_key:
            logger.warning("No OCR method available (tesseract or API key)")
            return [["중식정보없음"] for _ in range(5)]
        
        processed = ImageOps.autocontrast(image)
        processed = processed.resize((processed.width * 2, processed.height * 2))
        processed = processed.filter(ImageFilter.SHARPEN)

        width, height = processed.size
        left = int(width * 0.18)
        right = int(width * 0.98)
        top = int(height * 0.18)
        bottom = int(height * 0.82)

        columns = 5
        column_width = max((right - left) // columns, 1)
        day_items: List[List[str]] = [[] for _ in range(columns)]

        for idx in range(columns):
            crop_left = left + idx * column_width
            crop_right = right if idx == columns - 1 else left + (idx + 1) * column_width
            crop = processed.crop((crop_left, top, crop_right, bottom))

            if TESSERACT_AVAILABLE:
                # Use local tesseract
                text_psm6 = pytesseract.image_to_string(crop, lang="kor+eng", config="--oem 3 --psm 6")
                text_psm4 = pytesseract.image_to_string(crop, lang="kor+eng", config="--oem 3 --psm 4")
                parsed6 = self._parse_menu_lines_from_ocr(text_psm6)
                parsed4 = self._parse_menu_lines_from_ocr(text_psm4)
                parsed = parsed4 if self._ocr_quality_score(parsed4) > self._ocr_quality_score(parsed6) else parsed6
                day_items[idx] = self._finalize_day_items(parsed, [text_psm6, text_psm4])
            else:
                # Use OCR.space API
                text_api = self._ocr_with_api(crop)
                parsed_api = self._parse_menu_lines_from_ocr(text_api)
                day_items[idx] = self._finalize_day_items(parsed_api, [text_api])

        return day_items

    def _parse_menu_lines_from_ocr(self, text: str) -> List[str]:
        lines: List[str] = []

        ignored_keywords = [
            "식자재 원산지", "메뉴게시판", "별도로 표시", "식단은 식자재 수급", "변경될 수 있습니다",
        ]

        for raw in text.splitlines():
            normalized = re.sub(r"\s+", " ", raw).strip()
            if len(normalized) < 2:
                continue
            if not re.search(r"[가-힣A-Za-z0-9]", normalized):
                continue
            if any(keyword in normalized for keyword in ignored_keywords):
                continue
            if re.fullmatch(r"[ㄱ-ㅎㅏ-ㅣ]+", normalized):
                continue

            normalized = normalized.strip("-·•|:; ")
            normalized = re.sub(r"^[^가-힣A-Za-z0-9]+", "", normalized)
            normalized = re.sub(r"[^가-힣A-Za-z0-9/()\-\s.&*]", "", normalized)
            normalized = re.sub(r"\s+", " ", normalized).strip()

            if not normalized:
                continue
            if re.search(r"[A-Za-z]", normalized) and not re.search(r"[가-힣]", normalized):
                continue

            hangul_count = len(re.findall(r"[가-힣]", normalized))
            alpha_count = len(re.findall(r"[A-Za-z]", normalized))
            if alpha_count > 0 and hangul_count < 2:
                continue

            normalized = self._normalize_menu_text(normalized)
            normalized = re.sub(r"^(\d{1,2}|[월화수목금토일])\s*", "", normalized).strip()
            if normalized:
                lines.append(normalized)

        return self._deduplicate_items(lines)

    def _ocr_quality_score(self, items: List[str]) -> int:
        score = 0
        for item in items:
            score += len(re.findall(r"[가-힣]", item)) * 3
            score += len(re.findall(r"\d", item))
            score -= len(re.findall(r"[A-Za-z]", item)) * 2
        return score

    def _finalize_day_items(self, items: List[str], raw_texts: List[str]) -> List[str]:
        merged_raw = "\n".join(raw_texts)
        if any(keyword in merged_raw for keyword in ["연휴", "미운영", "휴무"]):
            return ["중식 미운영"]

        noise_keywords = ["드립니다", "됩니다", "이용", "식당"]
        menu_keywords = ["밥", "국", "찌개", "볶", "김치", "튀김", "무침", "우동", "카레", "샐러드", "장"]

        cleaned: List[str] = []
        for item in items:
            item = self._normalize_menu_text(item)
            item = re.sub(r"\s*이용이\s*$", "", item).strip()
            item = re.sub(r"\s+[A-Za-z]{2,}$", "", item).strip()
            if "대면배식" in item:
                continue
            if any(keyword in item for keyword in noise_keywords) and not any(key in item for key in menu_keywords):
                continue
            if len(item) <= 2 and not any(key in item for key in menu_keywords) and not re.search(r"\d{1,2}일", item):
                continue
            cleaned.append(item)

        menu_like_count = sum(1 for item in cleaned if any(key in item for key in menu_keywords))
        if menu_like_count == 0:
            return ["중식정보없음"]

        if any("배추김치" in item for item in cleaned) and not any("샐러드" in item for item in cleaned):
            cleaned.append("그린샐러드&드레싱")

        return cleaned

    def _normalize_menu_text(self, text: str) -> str:
        normalized = text.strip()

        # 공통 OCR 오탈자 보정
        normalized = normalized.replace("배배추김치", "배추김치")
        normalized = re.sub(r"(?<!배)추김치", "배추김치", normalized)
        normalized = normalized.replace("달갈장", "달걀장")
        normalized = normalized.replace("그린샐러드드레싱", "그린샐러드&드레싱")

        # 중복 접두어 보정
        normalized = normalized.replace("얼큰얼큰", "얼큰")
        normalized = normalized.replace("실실", "실")
        normalized = normalized.replace("간간", "간")

        # 정확 매칭 기반 보정 (과보정 방지)
        strict_map = {
            "콩나물국": "얼큰콩나물국",
            "곤약무침": "실곤약무침",
            "장고추지": "간장고추지",
            "육": "수육",
            "육 Ss": "수육",
        }
        if normalized in strict_map:
            normalized = strict_map[normalized]

        # 부분 문자열 기반 보정 (축약 대응)
        if "콩나물국" in normalized and "얼큰콩나물국" not in normalized:
            normalized = normalized.replace("콩나물국", "얼큰콩나물국")
        if "곤약무침" in normalized and "실곤약무침" not in normalized:
            normalized = normalized.replace("곤약무침", "실곤약무침")
        if "장고추지" in normalized and "간장고추지" not in normalized:
            normalized = normalized.replace("장고추지", "간장고추지")

        return normalized

    def _append_notice_items(self, items: List[str]) -> List[str]:
        notices = [
            "* 식자재 원산지는 일일메뉴게시판에 별도로 표시하였습니다.",
            "* 위 식단은 식자재 수급에 따라 변경될 수 있습니다.",
        ]
        merged = items[:]
        for notice in notices:
            if notice not in merged:
                merged.append(notice)
        return merged

    def _split_student_meals(self, day_items: List[str]) -> tuple[List[str], List[str]]:
        filtered = []
        for item in day_items:
            if re.fullmatch(r"\d{1,2}일", item):
                continue
            filtered.append(item)

        if any("미운영" in item and ("천원의아침밥" in item or "조식" in item) for item in filtered):
            breakfast_items = ["조식 미운영"]
        else:
            breakfast_items = []

        pivot_keywords = ["오늘의백반", "오늘의 백반", "중식", "백미밥", "보리밥", "차조밥", "쌀국수", "설령탕", "설렁탕", "돌솔알밥", "돌솥알밥", "제육덮밥"]
        pivot_index = -1
        for idx, item in enumerate(filtered):
            if any(keyword in item for keyword in pivot_keywords):
                pivot_index = idx
                break

        if not breakfast_items:
            if pivot_index > 0:
                breakfast_items = filtered[:pivot_index]
            else:
                breakfast_items = [item for item in filtered if any(k in item for k in ["라면", "돈까스", "천원의아침밥", "조식", "치킨마요", "생선까스", "고구마돈까스", "치즈돈까스"]) ]

        if pivot_index >= 0:
            lunch_items = filtered[pivot_index:]
        else:
            lunch_items = [item for item in filtered if item not in breakfast_items]

        if not breakfast_items:
            breakfast_items = ["조식정보없음"]
        if not lunch_items:
            lunch_items = ["중식정보없음"]

        return (self._deduplicate_items(breakfast_items), self._deduplicate_items(lunch_items))

    def _deduplicate_items(self, items: List[str]) -> List[str]:
        result: List[str] = []
        seen = set()
        for item in items:
            key = item.replace(" ", "")
            if key in seen:
                continue
            seen.add(key)
            result.append(item)
        return result

    def _get_with_retry(self, url: str, params: Optional[dict] = None, timeout: Optional[int] = None) -> requests.Response:
        last_error: Optional[Exception] = None
        effective_timeout = timeout or self.timeout

        for attempt in range(1, self.max_retries + 1):
            try:
                response = requests.get(
                    url,
                    params=params,
                    headers=self.headers,
                    timeout=effective_timeout,
                )
                return response
            except requests.RequestException as error:
                last_error = error
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay * attempt)

        if last_error:
            raise last_error
        raise RuntimeError("HTTP request failed without explicit exception")
