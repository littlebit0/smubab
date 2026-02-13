from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from datetime import date, datetime, timedelta
from typing import Optional
import logging

from models import (
    MenuResponse, DailyMenuResponse,
    Restaurant
)
from crawler import SMUCafeteriaCrawler
from database import db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="SMU-Bab API",
    description="상명대학교 학식 정보 API",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인만 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

crawler = SMUCafeteriaCrawler()


def update_menus(target_date: Optional[date] = None):
    if target_date is None:
        target_date = date.today()

    weekday = target_date.weekday()
    monday = target_date - timedelta(days=weekday)
    friday = monday + timedelta(days=4)

    menus = crawler.crawl_weekly_menu(target_date)
    saved_count = db.save_menus(menus)
    db.clear_old_menus(date.today() - timedelta(days=7))
    logger.info(f"Updated {saved_count} menus for {monday} ~ {friday}")


@app.on_event("startup")
async def startup_event():
    """서버 시작 시 실행"""
    logger.info("Starting SMU-Bab API server...")
    update_menus(date.today())
    logger.info("Server started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """서버 종료 시 실행"""
    logger.info("Server shutdown")


@app.get("/")
async def root():
    """API 정보"""
    return {
        "name": "SMU-Bab API",
        "version": "1.0.0",
        "description": "상명대학교 학식 정보 API"
    }


@app.get("/api/health")
async def health_check():
    """헬스 체크"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/menus/today", response_model=DailyMenuResponse)
async def get_today_menus():
    """오늘의 메뉴를 조회합니다."""
    today = date.today()
    menus = db.get_daily_menus(today)

    if not menus:
        update_menus(today)
        menus = db.get_daily_menus(today)

    return DailyMenuResponse(
        success=True,
        date=today,
        menus=menus,
        message=f"총 {len(menus)}개의 메뉴"
    )


@app.get("/api/menus/date/{target_date}", response_model=DailyMenuResponse)
async def get_menus_by_date(target_date: date):
    """특정 날짜의 메뉴를 조회합니다."""
    menus = db.get_daily_menus(target_date)

    if not menus:
        update_menus(target_date)
        menus = db.get_daily_menus(target_date)

    return DailyMenuResponse(
        success=True,
        date=target_date,
        menus=menus,
        message=f"총 {len(menus)}개의 메뉴" if menus else "메뉴 정보가 없습니다"
    )


@app.get("/api/menus/week", response_model=MenuResponse)
async def get_weekly_menus(
    target_date: Optional[date] = Query(None, description="기준 날짜 (기본값: 오늘, 해당 주의 월~금 반환)")
):
    """주간 메뉴를 조회합니다 (해당 주의 월~금)."""
    if target_date is None:
        target_date = date.today()
    
    # 해당 날짜가 속한 주의 월요일과 금요일 계산
    weekday = target_date.weekday()
    monday = target_date - timedelta(days=weekday)
    friday = monday + timedelta(days=4)
    
    # 데이터베이스에서 조회
    menus = db.get_weekly_menus(monday, friday)

    if not menus:
        update_menus(target_date)
        menus = db.get_weekly_menus(monday, friday)

    return MenuResponse(
        success=True,
        data=menus,
        message=f"{monday} ~ {friday} 메뉴 {len(menus)}개"
    )


@app.get("/api/menus/restaurant/{restaurant}", response_model=MenuResponse)
async def get_menus_by_restaurant(
    restaurant: Restaurant,
    target_date: Optional[date] = Query(None, description="날짜 (기본값: 오늘)")
):
    """특정 식당의 메뉴를 조회합니다."""
    if target_date is None:
        target_date = date.today()
    
    menus = db.get_menus_by_restaurant(restaurant, target_date)
    
    return MenuResponse(
        success=True,
        data=menus,
        message=f"{restaurant.value} 메뉴 {len(menus)}개"
    )


@app.get("/api/restaurants")
async def get_restaurants():
    """식당 목록을 조회합니다."""
    restaurant_names = {
        "서울_학생식당": "서울캠퍼스 학생식당",
        "서울_교직원식당": "서울캠퍼스 교직원식당",
        "서울_푸드코트": "서울캠퍼스 푸드코트",
        "천안_학생식당": "천안캠퍼스 학생식당",
        "천안_교직원식당": "천안캠퍼스 교직원식당",
    }
    return {
        "success": True,
        "data": [
            {
                "value": r.value, 
                "name": restaurant_names.get(r.value, r.value)
            } 
            for r in Restaurant
        ]
    }


@app.post("/api/menus/refresh")
async def refresh_menus():
    """메뉴 정보를 강제로 갱신합니다."""
    try:
        db.menus = []
        update_menus(date.today())
        return {
            "success": True,
            "message": "메뉴 정보가 갱신되었습니다"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"메뉴 갱신 실패: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
