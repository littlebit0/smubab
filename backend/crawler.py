import base64
import hashlib
import json
import logging
import os
import re
import time
from dataclasses import dataclass
from datetime import date
from io import BytesIO
from pathlib import Path
from typing import List, Optional
from urllib.parse import parse_qs, urljoin, urlparse

import requests
from bs4 import BeautifulSoup, Tag
from PIL import Image, ImageFilter, ImageOps

try:
    import pytesseract

    TESSERACT_AVAILABLE = True
    default_tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    if os.getenv("TESSERACT_CMD"):
        pytesseract.pytesseract.tesseract_cmd = os.getenv("TESSERACT_CMD", "")
    elif os.name == "nt" and Path(default_tesseract_cmd).exists():
        pytesseract.pytesseract.tesseract_cmd = default_tesseract_cmd
except (ImportError, Exception):
    TESSERACT_AVAILABLE = False

from models import MealType, Menu, MenuItem, Restaurant

logger = logging.getLogger(__name__)


@dataclass
class WeeklyArticle:
    title: str
    url: str
    week_dates: List[date]
    article_no: Optional[str] = None


class SMUCafeteriaCrawler:
    """상명대 식단 크롤러.

    서울캠퍼스는 공식 메뉴 표의 텍스트를 파싱하고, 천안캠퍼스는 게시판 최신 글을
    감지한 뒤 글 본문 이미지에서 OCR로 요일별 식단을 추출한다.
    """

    def __init__(self):
        self.seoul_menu_url = "https://www.smu.ac.kr/kor/life/restaurantView.do"
        self.cheonan_faculty_board_url = "https://www.smu.ac.kr/kor/life/restaurantView3.do"
        self.cheonan_student_board_url = "https://www.smu.ac.kr/kor/life/restaurantView4.do"
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
            )
        }
        self.timeout = int(os.getenv("SMU_CRAWLER_TIMEOUT", "25"))
        self.max_retries = int(os.getenv("SMU_CRAWLER_RETRIES", "3"))
        self.retry_delay = float(os.getenv("SMU_CRAWLER_RETRY_DELAY", "1.5"))
        self.ocr_space_api_key = os.getenv("OCR_SPACE_API_KEY", "")
        self.ocr_cache_path = Path(
            os.getenv(
                "MENU_OCR_CACHE_PATH",
                str(Path(__file__).with_name("menu_ocr_cache.json")),
            )
        )
        self._ocr_cache = self._load_ocr_cache()

    def crawl_daily_menu(self, target_date: date) -> List[Menu]:
        weekly_menus = self.crawl_weekly_menu(target_date)
        return [menu for menu in weekly_menus if menu.date == target_date]

    def crawl_weekly_menu(self, target_date: date) -> List[Menu]:
        week_date = self._effective_week_date(target_date)
        menus: List[Menu] = []

        for meal_type in (MealType.BREAKFAST, MealType.LUNCH, MealType.DINNER):
            try:
                menus.extend(self._crawl_seoul_by_category(week_date, meal_type))
            except Exception as error:
                logger.warning("Seoul %s crawl failed: %s", meal_type.value, error)

        try:
            menus.extend(self._crawl_cheonan_faculty_lunch(week_date))
        except Exception as error:
            logger.warning("Cheonan faculty crawl failed: %s", error)
            menus.extend(
                self._unknown_week_menus(
                    week_date,
                    Restaurant.CHEONAN_FACULTY,
                    MealType.LUNCH,
                    "중식정보없음",
                )
            )

        try:
            menus.extend(self._crawl_cheonan_student_menus(week_date))
        except Exception as error:
            logger.warning("Cheonan student crawl failed: %s", error)
            menus.extend(
                self._unknown_week_menus(
                    week_date,
                    Restaurant.CHEONAN_STUDENT,
                    MealType.BREAKFAST,
                    "조식정보없음",
                )
            )
            menus.extend(
                self._unknown_week_menus(
                    week_date,
                    Restaurant.CHEONAN_STUDENT,
                    MealType.LUNCH,
                    "중식정보없음",
                )
            )

        return self._merge_menus(menus)

    def _crawl_seoul_by_category(self, target_date: date, meal_type: MealType) -> List[Menu]:
        category_value = {
            MealType.BREAKFAST: "B",
            MealType.LUNCH: "L",
            MealType.DINNER: "D",
        }[meal_type]
        response = self._get_with_retry(
            self.seoul_menu_url,
            params={
                "mode": "menuList",
                "srMealCategory": category_value,
                "srDt": target_date.isoformat(),
            },
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        table = soup.select_one(".menu-list-box table.smu-table") or soup.select_one("table.tb-w150")
        if not table:
            logger.warning("서울캠퍼스 식단표 테이블을 찾지 못했습니다.")
            return []

        dates = self._extract_dates_from_table(table, target_date)
        if not dates:
            return []

        rows = table.select("tbody tr")
        if not rows and meal_type == MealType.BREAKFAST:
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
            header = row.find("th")
            row_label = self._clean_text(header.get_text(" ", strip=True) if header else "")
            restaurant = self._seoul_restaurant_from_row_label(row_label)
            data_cells = row.find_all("td", recursive=False)

            for index, cell in enumerate(data_cells[: len(dates)]):
                items = self._extract_items_from_cell(cell)
                if not items and meal_type == MealType.BREAKFAST:
                    items = [MenuItem(name="조식제공X", price=None)]
                if not items:
                    continue

                menus.append(
                    Menu(
                        date=dates[index],
                        restaurant=restaurant,
                        meal_type=meal_type,
                        items=items,
                    )
                )

        return menus

    def _crawl_cheonan_faculty_lunch(self, target_date: date) -> List[Menu]:
        article = self._find_weekly_article(
            self.cheonan_faculty_board_url,
            target_date,
            required_keywords=("교직원", "주간"),
        )
        if not article:
            return []

        day_texts = self._extract_weekly_texts_from_article(
            article,
            expected_days=5,
            layout="cheonan_faculty",
        )
        menus: List[Menu] = []
        for index, menu_date in enumerate(article.week_dates[:5]):
            items = day_texts[index] if index < len(day_texts) else []
            if not items:
                items = ["중식정보없음"]
            menus.append(
                Menu(
                    date=menu_date,
                    restaurant=Restaurant.CHEONAN_FACULTY,
                    meal_type=MealType.LUNCH,
                    items=[MenuItem(name=item, price=None) for item in items],
                )
            )

        logger.info("Cheonan faculty article %s parsed: %s menus", article.article_no, len(menus))
        return menus

    def _crawl_cheonan_student_menus(self, target_date: date) -> List[Menu]:
        article = self._find_weekly_article(
            self.cheonan_student_board_url,
            target_date,
            required_keywords=("주간식단",),
        )
        if not article:
            return []

        day_texts = self._extract_weekly_texts_from_article(
            article,
            expected_days=5,
            layout="cheonan_student",
        )
        menus: List[Menu] = []
        for index, menu_date in enumerate(article.week_dates[:5]):
            items = day_texts[index] if index < len(day_texts) else []
            breakfast_items, lunch_items = self._split_student_meals(items)

            menus.append(
                Menu(
                    date=menu_date,
                    restaurant=Restaurant.CHEONAN_STUDENT,
                    meal_type=MealType.BREAKFAST,
                    items=[
                        MenuItem(name=item, price=None)
                        for item in breakfast_items
                    ],
                )
            )
            menus.append(
                Menu(
                    date=menu_date,
                    restaurant=Restaurant.CHEONAN_STUDENT,
                    meal_type=MealType.LUNCH,
                    items=[
                        MenuItem(name=item, price=None)
                        for item in lunch_items
                    ],
                )
            )

        logger.info("Cheonan student article %s parsed: %s menus", article.article_no, len(menus))
        return menus

    def _find_weekly_article(
        self,
        board_url: str,
        target_date: date,
        required_keywords: tuple[str, ...],
    ) -> Optional[WeeklyArticle]:
        response = self._get_with_retry(board_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        monday = self._monday_of(target_date)
        friday = monday.fromordinal(monday.toordinal() + 4)
        candidates: List[WeeklyArticle] = []

        for anchor in soup.find_all("a", href=True):
            href = anchor.get("href", "")
            if "mode=view" not in href:
                continue

            raw_title = anchor.get("title") or anchor.get_text(" ", strip=True)
            title = self._clean_title(raw_title)
            compact_title = re.sub(r"\s+", "", title)
            if not all(keyword.replace(" ", "") in compact_title for keyword in required_keywords):
                continue

            week_dates = self._extract_week_dates_from_title(title, target_date, fallback=False)
            if not week_dates:
                continue

            article_url = urljoin(board_url, href.replace("&amp;", "&"))
            candidates.append(
                WeeklyArticle(
                    title=title,
                    url=article_url,
                    week_dates=week_dates,
                    article_no=self._extract_article_no(article_url),
                )
            )

        for article in candidates:
            if article.week_dates[0] <= target_date <= article.week_dates[-1]:
                return article
            if article.week_dates[0] == monday and article.week_dates[-1] == friday:
                return article

        if candidates:
            logger.info(
                "No exact weekly article for %s; using latest article %s",
                target_date,
                candidates[0].article_no,
            )
            return candidates[0]

        return None

    def _extract_weekly_texts_from_article(
        self,
        article: WeeklyArticle,
        expected_days: int,
        layout: str = "generic",
    ) -> List[List[str]]:
        response = self._get_with_retry(article.url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        text_day_items = self._extract_day_items_from_article_text(soup, expected_days)
        if self._has_enough_menu_text(text_day_items):
            return text_day_items

        image_urls = self._extract_article_image_urls(soup, article.url)
        if not image_urls:
            logger.warning("Article %s has no menu image", article.url)
            return [[] for _ in range(expected_days)]

        return self._extract_weekly_menu_texts_from_images(image_urls, expected_days, layout)

    def _extract_article_image_urls(self, soup: BeautifulSoup, article_url: str) -> List[str]:
        image_urls: List[str] = []
        selectors = [
            ".fr-view img",
            ".board-view img",
            ".board-view-content img",
            "#jwxe_main_content img.fr-dib",
        ]

        for image in soup.select(", ".join(selectors)):
            src = image.get("data-path") or image.get("src")
            if not src:
                continue

            absolute = urljoin(article_url, src.replace("&amp;", "&"))
            if self._is_menu_image_url(absolute):
                image_urls.append(absolute)

        return self._deduplicate_urls(image_urls)

    def _extract_weekly_menu_texts_from_images(
        self,
        image_urls: List[str],
        expected_days: int,
        layout: str = "generic",
    ) -> List[List[str]]:
        merged: List[List[str]] = [[] for _ in range(expected_days)]

        for image_url in image_urls:
            try:
                response = self._get_with_retry(image_url, timeout=45)
                response.raise_for_status()
                content_hash = hashlib.sha256(response.content).hexdigest()
                cache_key = f"{layout}|v4|{image_url}|{content_hash}"

                cached_day_items = self._ocr_cache.get(cache_key)
                if cached_day_items and self._has_enough_menu_text(cached_day_items):
                    day_items = cached_day_items
                else:
                    image = Image.open(BytesIO(response.content)).convert("RGB")
                    day_items = self._extract_day_columns_from_image(
                        image,
                        expected_days,
                        layout,
                    )
                    self._ocr_cache[cache_key] = day_items
                    self._save_ocr_cache()

                for index in range(expected_days):
                    if index < len(day_items):
                        merged[index].extend(day_items[index])
            except Exception as error:
                logger.warning("Menu image OCR failed: %s (%s)", image_url, error)

        return [self._deduplicate_strings(items) for items in merged]

    def _extract_day_columns_from_image(
        self,
        image: Image.Image,
        expected_days: int,
        layout: str = "generic",
    ) -> List[List[str]]:
        if not TESSERACT_AVAILABLE and not self.ocr_space_api_key:
            logger.warning("No OCR method available. Install Tesseract or set OCR_SPACE_API_KEY.")
            return [[] for _ in range(expected_days)]

        if layout == "cheonan_faculty":
            return self._extract_cheonan_faculty_table(image, expected_days)

        if layout == "cheonan_student":
            return self._extract_cheonan_student_table(image, expected_days)

        processed = ImageOps.autocontrast(image.convert("L"))
        processed = processed.resize((processed.width * 2, processed.height * 2))
        processed = processed.filter(ImageFilter.SHARPEN)

        width, height = processed.size
        left = int(width * 0.12)
        right = int(width * 0.98)
        top = int(height * 0.16)
        bottom = int(height * 0.92)
        column_width = max((right - left) // expected_days, 1)

        day_items: List[List[str]] = [[] for _ in range(expected_days)]
        for index in range(expected_days):
            crop_left = left + index * column_width
            crop_right = right if index == expected_days - 1 else left + (index + 1) * column_width
            crop = processed.crop((crop_left, top, crop_right, bottom))
            raw_texts = self._ocr_image(crop)

            parsed_variants = [self._parse_menu_lines_from_ocr(text) for text in raw_texts]
            parsed = max(parsed_variants, key=self._ocr_quality_score, default=[])
            day_items[index] = self._finalize_day_items(parsed, raw_texts)

        return day_items

    def _extract_cheonan_faculty_table(
        self,
        image: Image.Image,
        expected_days: int,
    ) -> List[List[str]]:
        width, height = image.size
        x_ranges = self._scale_ranges(
            [(175, 327), (327, 479), (479, 631), (631, 783), (783, 935)],
            width,
            968,
        )[:expected_days]
        y_ranges = self._scale_ranges(
            [(188, 236), (236, 285), (285, 334), (334, 383), (383, 431), (431, 480), (480, 528)],
            height,
            577,
        )

        day_items: List[List[str]] = []
        for x_range in x_ranges:
            items: List[str] = []
            for y_range in y_ranges:
                raw_texts = self._ocr_image(self._prepare_ocr_crop(image, x_range, y_range), ("7", "6"))
                parsed = self._best_ocr_lines(raw_texts)
                items.extend(parsed)
            day_items.append(self._finalize_day_items(items, items))

        return day_items

    def _extract_cheonan_student_table(
        self,
        image: Image.Image,
        expected_days: int,
    ) -> List[List[str]]:
        width, height = image.size
        x_ranges = self._scale_ranges(
            [(218, 396), (397, 574), (574, 773), (773, 982), (982, 1159)],
            width,
            1225,
        )[:expected_days]
        row_ranges = {
            "breakfast": self._scale_range((132, 266), height, 900),
            "b_corner": self._scale_range((266, 411), height, 900),
            "c_corner": self._scale_range((411, 593), height, 900),
        }

        day_items: List[List[str]] = []
        for x_range in x_ranges:
            breakfast_texts = self._ocr_image(
                self._prepare_ocr_crop(image, x_range, row_ranges["breakfast"]),
                ("6", "7"),
            )
            lunch_texts = []
            for row_name in ("b_corner", "c_corner"):
                lunch_texts.extend(
                    self._ocr_image(
                        self._prepare_ocr_crop(image, x_range, row_ranges[row_name]),
                        ("6", "7"),
                    )
                )

            breakfast_items = self._finalize_day_items(
                self._merged_ocr_lines(breakfast_texts),
                breakfast_texts,
            )
            lunch_items = self._finalize_day_items(
                self._merged_ocr_lines(lunch_texts),
                lunch_texts,
            )
            day_items.append(
                ["__SMUBAB_BREAKFAST__"]
                + breakfast_items
                + ["__SMUBAB_LUNCH__"]
                + lunch_items
            )

        return day_items

    def _prepare_ocr_crop(
        self,
        image: Image.Image,
        x_range: tuple[int, int],
        y_range: tuple[int, int],
    ) -> Image.Image:
        crop = image.crop((x_range[0], y_range[0], x_range[1], y_range[1])).convert("L")
        crop = ImageOps.autocontrast(crop)
        crop = crop.resize((crop.width * 3, crop.height * 3))
        return crop.filter(ImageFilter.SHARPEN)

    def _scale_ranges(
        self,
        ranges: List[tuple[int, int]],
        actual_size: int,
        base_size: int,
    ) -> List[tuple[int, int]]:
        return [self._scale_range(item, actual_size, base_size) for item in ranges]

    def _scale_range(
        self,
        item: tuple[int, int],
        actual_size: int,
        base_size: int,
    ) -> tuple[int, int]:
        return (
            max(0, round(item[0] * actual_size / base_size)),
            min(actual_size, round(item[1] * actual_size / base_size)),
        )

    def _best_ocr_lines(self, raw_texts: List[str]) -> List[str]:
        parsed_variants = [self._parse_menu_lines_from_ocr(text) for text in raw_texts]
        return max(parsed_variants, key=self._ocr_quality_score, default=[])

    def _merged_ocr_lines(self, raw_texts: List[str]) -> List[str]:
        merged: List[str] = []
        for text in raw_texts:
            merged.extend(self._parse_menu_lines_from_ocr(text))
        return self._deduplicate_strings(merged)

    def _ocr_image(self, image: Image.Image, psm_values: tuple[str, ...] = ("6", "4")) -> List[str]:
        texts: List[str] = []

        if TESSERACT_AVAILABLE:
            tessdata_dir = os.getenv("TESSDATA_DIR", "")
            if tessdata_dir:
                os.environ["TESSDATA_PREFIX"] = tessdata_dir
            for psm in psm_values:
                try:
                    texts.append(
                        pytesseract.image_to_string(
                            image,
                            lang=os.getenv("TESSERACT_LANG", "kor+eng"),
                            config=f"--oem 3 --psm {psm}",
                        )
                    )
                except Exception as error:
                    logger.warning("Tesseract OCR failed: %s", error)

        api_text = self._ocr_with_api(image)
        if api_text:
            texts.append(api_text)

        return texts

    def _ocr_with_api(self, image: Image.Image) -> str:
        if not self.ocr_space_api_key:
            return ""

        try:
            buffer = BytesIO()
            image.save(buffer, format="PNG")
            img_base64 = base64.b64encode(buffer.getvalue()).decode()
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
                timeout=45,
            )
            response.raise_for_status()
            result = response.json()
            if result.get("IsErroredOnProcessing"):
                logger.warning("OCR.space API error: %s", result.get("ErrorMessage"))
                return ""

            parsed_results = result.get("ParsedResults", [])
            if parsed_results:
                return parsed_results[0].get("ParsedText", "")
        except Exception as error:
            logger.warning("OCR.space API failed: %s", error)

        return ""

    def _extract_dates_from_table(self, table: Tag, target_date: date) -> List[date]:
        dates: List[date] = []

        for cell in table.select("thead tr th")[1:]:
            text = cell.get_text(" ", strip=True)
            matched = re.search(r"\((\d{1,2})\.(\d{1,2})\)", text)
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

    def _extract_week_dates_from_title(
        self,
        title_text: str,
        fallback_date: date,
        fallback: bool = True,
    ) -> List[date]:
        compact = re.sub(r"\s+", "", title_text)
        patterns = [
            re.compile(r"\((\d{4})\.(\d{1,2})\.(\d{1,2})\.?~(\d{1,2})\.(\d{1,2})\.?\)"),
            re.compile(r"(\d{4})\.(\d{1,2})\.(\d{1,2})\.?~(\d{1,2})\.(\d{1,2})\.?"),
        ]

        for pattern in patterns:
            match = pattern.search(compact)
            if match:
                year = int(match.group(1))
                start_month = int(match.group(2))
                start_day = int(match.group(3))
                end_month = int(match.group(4))
                end_day = int(match.group(5))
                return self._build_date_range(year, start_month, start_day, end_month, end_day)

        short_match = re.search(r"\((\d{1,2})\.(\d{1,2})\.?~(\d{1,2})\.(\d{1,2})\.?\)", compact)
        if short_match:
            start_month = int(short_match.group(1))
            start_day = int(short_match.group(2))
            end_month = int(short_match.group(3))
            end_day = int(short_match.group(4))
            year = fallback_date.year
            dates = self._build_date_range(year, start_month, start_day, end_month, end_day)
            if dates and abs((dates[0] - fallback_date).days) > 200:
                dates = self._build_date_range(year - 1, start_month, start_day, end_month, end_day)
            return dates

        if not fallback:
            return []

        monday = self._monday_of(fallback_date)
        return [monday.fromordinal(monday.toordinal() + index) for index in range(5)]

    def _build_date_range(
        self,
        year: int,
        start_month: int,
        start_day: int,
        end_month: int,
        end_day: int,
    ) -> List[date]:
        try:
            start_date = date(year, start_month, start_day)
            end_year = year + 1 if end_month < start_month else year
            end_date = date(end_year, end_month, end_day)
        except ValueError:
            return []

        day_count = (end_date - start_date).days + 1
        if day_count <= 0:
            return []
        return [start_date.fromordinal(start_date.toordinal() + index) for index in range(day_count)]

    def _extract_items_from_cell(self, cell: Tag) -> List[MenuItem]:
        lines: List[str] = []
        list_items = cell.find_all("li")
        if list_items:
            lines = [item.get_text(" ", strip=True) for item in list_items]
        else:
            lines = cell.get_text("\n", strip=True).splitlines()

        menu_items = []
        for line in lines:
            name = self._normalize_menu_text(line)
            if not name or self._is_noise_line(name):
                continue
            menu_items.append(MenuItem(name=name, price=None))

        return menu_items

    def _extract_day_items_from_article_text(
        self,
        soup: BeautifulSoup,
        expected_days: int,
    ) -> List[List[str]]:
        content_nodes = soup.select(".fr-view, .board-view-content, .view-con")
        if not content_nodes:
            return [[] for _ in range(expected_days)]

        text = "\n".join(node.get_text("\n", strip=True) for node in content_nodes)
        lines = self._parse_menu_lines_from_ocr(text)
        if len(lines) < expected_days * 2:
            return [[] for _ in range(expected_days)]

        day_markers = {"월": 0, "화": 1, "수": 2, "목": 3, "금": 4}
        day_items: List[List[str]] = [[] for _ in range(expected_days)]
        current_index: Optional[int] = None

        for line in lines:
            marker = line[:1]
            if marker in day_markers:
                current_index = day_markers[marker]
                line = line[1:].strip()
            if current_index is None:
                continue
            if line:
                day_items[current_index].append(line)

        return [self._finalize_day_items(items, items) for items in day_items]

    def _parse_menu_lines_from_ocr(self, text: str) -> List[str]:
        lines: List[str] = []
        for raw in text.splitlines():
            normalized = self._normalize_menu_text(raw)
            if not normalized or self._is_noise_line(normalized):
                continue
            if re.search(r"[A-Za-z]", normalized) and not re.search(r"[가-힣]", normalized):
                continue
            if len(normalized) <= 1:
                continue
            lines.append(normalized)

        return self._deduplicate_strings(lines)

    def _ocr_quality_score(self, items: List[str]) -> int:
        if not items:
            return 0

        score = len(items) * 10
        score += sum(5 for item in items if self._looks_like_menu_item(item))
        score -= sum(4 for item in items if len(item) > 35)
        score -= sum(3 for item in items if re.fullmatch(r"[\d\s./~()-]+", item))
        return score

    def _finalize_day_items(self, items: List[str], raw_texts: List[str]) -> List[str]:
        merged_raw = "\n".join(raw_texts)
        if any(keyword in merged_raw for keyword in ("미운영", "휴무", "휴점")):
            return ["미운영"]

        cleaned: List[str] = []
        for item in items:
            item = self._normalize_menu_text(item)
            if not item or self._is_noise_line(item):
                continue
            compact_item = item.replace(" ", "")
            if re.fullmatch(r"\d{1,2}일?", item):
                continue
            if re.fullmatch(r"\d{1,2}:?\d{2}~?", item):
                continue
            if re.fullmatch(r"\d{1,2}[./]\d{1,2}", item):
                continue
            if re.fullmatch(r"\d{1,2}월\s*\d{1,2}일", item):
                continue
            if re.fullmatch(r"[월화수목금토일]", item):
                continue
            if item in ("<오늘의백반>", "오늘의백반", "OPEN", "CLOSE"):
                continue
            if compact_item in ("아이", "었나", "었나."):
                continue
            if len(compact_item) <= 3 and not self._looks_like_menu_item(item):
                continue
            cleaned.append(item)

        if not cleaned:
            return []

        menu_like_count = sum(1 for item in cleaned if self._looks_like_menu_item(item))
        if menu_like_count == 0 and len(cleaned) > 4:
            return []

        return self._deduplicate_strings(cleaned)

    def _split_student_meals(self, day_items: List[str]) -> tuple[List[str], List[str]]:
        if "__SMUBAB_BREAKFAST__" in day_items or "__SMUBAB_LUNCH__" in day_items:
            breakfast_items: List[str] = []
            lunch_items: List[str] = []
            current: Optional[str] = None

            for item in day_items:
                if item == "__SMUBAB_BREAKFAST__":
                    current = "breakfast"
                    continue
                if item == "__SMUBAB_LUNCH__":
                    current = "lunch"
                    continue
                if not item or self._is_noise_line(item):
                    continue
                if current == "breakfast":
                    breakfast_items.append(item)
                elif current == "lunch":
                    lunch_items.append(item)

            if not breakfast_items:
                breakfast_items = ["조식정보없음"]
            if not lunch_items:
                lunch_items = ["중식정보없음"]

            return self._deduplicate_strings(breakfast_items), self._deduplicate_strings(lunch_items)

        filtered = [
            item
            for item in day_items
            if item and not item.startswith("*") and not self._is_noise_line(item)
        ]

        if not filtered:
            return ["조식정보없음"], ["중식정보없음"]

        if any("미운영" in item and ("조식" in item or "아침" in item or "천원의아침밥" in item) for item in filtered):
            breakfast_items = ["조식 미운영"]
        else:
            breakfast_items = []

        pivot_keywords = (
            "오늘의백반",
            "오늘의 백반",
            "중식",
            "백미밥",
            "잡곡밥",
            "흑미밥",
            "보리밥",
            "볶음밥",
            "덮밥",
            "국",
            "찌개",
            "탕",
            "카레",
            "제육",
            "불고기",
            "쌀국수",
            "돈까스",
            "돈가스",
            "생선까스",
            "치킨마요",
            "스파게티",
        )
        pivot_index = -1
        for index, item in enumerate(filtered):
            if any(keyword in item for keyword in pivot_keywords):
                pivot_index = index
                break

        if not breakfast_items:
            if pivot_index > 0:
                breakfast_items = filtered[:pivot_index]
            else:
                breakfast_items = [
                    item
                    for item in filtered
                    if any(keyword in item for keyword in ("조식", "천원의아침밥", "라면", "샌드위치"))
                ]

        lunch_items = filtered[pivot_index:] if pivot_index >= 0 else [
            item for item in filtered if item not in breakfast_items
        ]

        if not breakfast_items:
            breakfast_items = ["조식정보없음"]
        if not lunch_items:
            lunch_items = ["중식정보없음"]

        return self._deduplicate_strings(breakfast_items), self._deduplicate_strings(lunch_items)

    def _normalize_menu_text(self, text: str) -> str:
        normalized = re.sub(r"\s+", " ", text).strip()
        normalized = normalized.strip("-·•|:;[] ")
        normalized = re.sub(r"^[^가-힣A-Za-z0-9*]+", "", normalized)
        normalized = re.sub(r"[^가-힣A-Za-z0-9/()&*+.,~\-\s]", "", normalized)
        normalized = re.sub(r"\s+", " ", normalized).strip()

        replacements = {
            "배배추김치": "배추김치",
            "당면아재볶음": "당면야채볶음",
            "매호박": "애호박",
            "고추상찌개": "고추장찌개",
            "짝두기": "깍두기",
            "청경재": "청경채",
            "조상": "초장",
            "아체무침": "야채무침",
            "돈욱": "돈육",
            "케참": "케찹",
            "끌여주는라면": "끓여주는라면",
            "끊여주는라면": "끓여주는라면",
            "딸기크림방": "딸기크림빵",
            "핀만두": "찐만두",
            "전통씩해": "전통식혜",
            "타르타르5": "타르타르소스",
            "그린샐러드드레싱": "그린샐러드&드레싱",
            "그린샐러드*드레싱": "그린샐러드&드레싱",
            "돌솔알밥": "돌솥알밥",
            "설령탕": "설렁탕",
        }
        for source, target in replacements.items():
            normalized = normalized.replace(source, target)

        return normalized

    def _is_noise_line(self, text: str) -> bool:
        compact = text.replace(" ", "")
        if not compact:
            return True
        noise_keywords = (
            "작성자",
            "작성일",
            "조회수",
            "게시글",
            "첨부파일",
            "이전글",
            "다음글",
            "메뉴게시판",
            "원산지",
            "식자재수급",
            "변경될수있습니다",
            "문의전화",
            "교직원식당",
            "학생식당",
            "천안캠퍼스",
            "서울캠퍼스",
            "상명대학교",
            "총무인사회계팀",
            "원산지표시",
            "국내산",
            "외국산",
            "수입산",
            "수급사정",
            "카카오채널",
            "엘리시온",
            "참고해주세요",
            "번호호출",
            "재료소진",
            "단품코너",
            "생명대엘리시온",
        )
        if any(keyword in compact for keyword in noise_keywords):
            return True
        if re.fullmatch(r"[A-Za-z\s|/.,~:-]+", text):
            return True
        if len(compact) <= 1:
            return True
        return False

    def _looks_like_menu_item(self, text: str) -> bool:
        return any(
            keyword in text
            for keyword in (
                "밥",
                "국",
                "탕",
                "찌개",
                "볶",
                "구이",
                "튀김",
                "까스",
                "김치",
                "무침",
                "샐러드",
                "우동",
                "라면",
                "덮밥",
                "카레",
                "소스",
                "음료",
                "죽",
                "빵",
                "식혜",
                "만두",
                "개장",
                "파스타",
                "스파게티",
                "고로케",
                "요구르트",
                "주스",
            )
        )

    def _seoul_restaurant_from_row_label(self, row_label: str) -> Restaurant:
        if "푸드" in row_label or "면류" in row_label or "까스" in row_label:
            return Restaurant.SEOUL_FOODCOURT
        if "교직" in row_label:
            return Restaurant.SEOUL_FACULTY
        return Restaurant.SEOUL_STUDENT

    def _append_notice_items(self, items: List[str]) -> List[str]:
        notices = [
            "* 식자재 원산지는 일일메뉴게시판에 별도로 표시됩니다.",
            "* 위 식단은 식자재 수급에 따라 변경될 수 있습니다.",
        ]
        merged = items[:]
        for notice in notices:
            if notice not in merged:
                merged.append(notice)
        return merged

    def _unknown_week_menus(
        self,
        target_date: date,
        restaurant: Restaurant,
        meal_type: MealType,
        message: str,
    ) -> List[Menu]:
        monday = self._monday_of(target_date)
        return [
            Menu(
                date=monday.fromordinal(monday.toordinal() + index),
                restaurant=restaurant,
                meal_type=meal_type,
                items=[MenuItem(name=message, price=None)],
            )
            for index in range(5)
        ]

    def _merge_menus(self, menus: List[Menu]) -> List[Menu]:
        merged: dict[tuple[date, str, str], Menu] = {}
        for menu in menus:
            key = (menu.date, str(menu.restaurant), str(menu.meal_type))
            if key not in merged:
                merged[key] = menu
                continue

            existing_names = {item.name for item in merged[key].items}
            for item in menu.items:
                if item.name not in existing_names:
                    merged[key].items.append(item)
                    existing_names.add(item.name)

        return sorted(
            merged.values(),
            key=lambda item: (item.date, str(item.restaurant), str(item.meal_type)),
        )

    def _has_enough_menu_text(self, day_items: List[List[str]]) -> bool:
        return sum(len(items) for items in day_items) >= 8 and sum(bool(items) for items in day_items) >= 3

    def _is_menu_image_url(self, image_url: str) -> bool:
        parsed = urlparse(image_url)
        if "editorImage.do" in parsed.path:
            return True
        if "/_attach/" in parsed.path and "thumb_" not in parsed.path:
            return True
        return False

    def _extract_article_no(self, article_url: str) -> Optional[str]:
        return parse_qs(urlparse(article_url).query).get("articleNo", [None])[0]

    def _clean_title(self, title: str) -> str:
        title = title.replace("자세히 보기", "")
        return self._clean_text(title)

    def _clean_text(self, text: str) -> str:
        return re.sub(r"\s+", " ", text).strip()

    def _monday_of(self, target_date: date) -> date:
        return target_date.fromordinal(target_date.toordinal() - target_date.weekday())

    def _effective_week_date(self, target_date: date) -> date:
        if target_date.weekday() >= 5:
            return target_date.fromordinal(target_date.toordinal() + (7 - target_date.weekday()))
        return target_date

    def _deduplicate_strings(self, items: List[str]) -> List[str]:
        result: List[str] = []
        seen = set()
        for item in items:
            key = item.replace(" ", "")
            if key in seen:
                continue
            if any(key in existing and len(key) + 2 < len(existing) for existing in seen):
                continue
            superseded = [
                existing
                for existing in seen
                if existing in key and len(existing) + 2 < len(key)
            ]
            if superseded:
                result = [value for value in result if value.replace(" ", "") not in superseded]
                seen.difference_update(superseded)
            seen.add(key)
            result.append(item)
        return result

    def _deduplicate_urls(self, urls: List[str]) -> List[str]:
        result: List[str] = []
        seen = set()
        for url in urls:
            if url in seen:
                continue
            seen.add(url)
            result.append(url)
        return result

    def _load_ocr_cache(self) -> dict:
        try:
            if self.ocr_cache_path.exists():
                return json.loads(self.ocr_cache_path.read_text(encoding="utf-8"))
        except Exception as error:
            logger.warning("Failed to load OCR cache: %s", error)
        return {}

    def _save_ocr_cache(self):
        try:
            self.ocr_cache_path.parent.mkdir(parents=True, exist_ok=True)
            self.ocr_cache_path.write_text(
                json.dumps(self._ocr_cache, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception as error:
            logger.warning("Failed to save OCR cache: %s", error)

    def _get_with_retry(
        self,
        url: str,
        params: Optional[dict] = None,
        timeout: Optional[int] = None,
    ) -> requests.Response:
        last_error: Optional[Exception] = None
        effective_timeout = timeout or self.timeout

        for attempt in range(1, self.max_retries + 1):
            try:
                return requests.get(
                    url,
                    params=params,
                    headers=self.headers,
                    timeout=effective_timeout,
                )
            except requests.RequestException as error:
                last_error = error
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay * attempt)

        if last_error:
            raise last_error
        raise RuntimeError("HTTP request failed without explicit exception")
