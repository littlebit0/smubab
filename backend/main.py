from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from datetime import date, datetime, timedelta
from typing import List, Optional
from apscheduler.schedulers.background import BackgroundScheduler
import logging

from models import (
    Menu, MenuResponse, DailyMenuResponse, 
    Restaurant, MealType
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

# 크롤러 인스턴스
crawler = SMUCafeteriaCrawler()

# 스케줄러 설정
scheduler = BackgroundScheduler()


def update_menus():
    """메뉴 정보를 업데이트합니다."""
    logger.info("Updating menus...")
    try:
        # 오늘부터 일주일치 메뉴 크롤링
        menus = crawler.crawl_weekly_menu()
        saved_count = db.save_menus(menus)
        logger.info(f"Updated {saved_count} menus")
        
        # 7일 이전 데이터 삭제
        deleted_count = db.clear_old_menus(date.today() - timedelta(days=7))
        logger.info(f"Deleted {deleted_count} old menus")
    except Exception as e:
        logger.error(f"Failed to update menus: {e}")


@app.on_event("startup")
async def startup_event():
    """서버 시작 시 실행"""
    logger.info("Starting SMU-Bab API server...")
    
    # 매일 오전 6시에 메뉴 업데이트
    scheduler.add_job(update_menus, 'cron', hour=6, minute=0)
    scheduler.start()
    
    # 초기 데이터는 백그라운드에서 로드 (서버 시작 차단 방지)
    from threading import Thread
    Thread(target=update_menus, daemon=True).start()
    
    logger.info("Server started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """서버 종료 시 실행"""
    scheduler.shutdown()
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
        # 데이터가 없으면 즉시 크롤링
        logger.info("No menus found, crawling now...")
        menus = crawler.crawl_daily_menu(today)
        db.save_menus(menus)
    
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
        # 미래 날짜는 크롤링 시도
        if target_date >= date.today():
            menus = crawler.crawl_daily_menu(target_date)
            if menus:
                db.save_menus(menus)
    
    return DailyMenuResponse(
        success=True,
        date=target_date,
        menus=menus,
        message=f"총 {len(menus)}개의 메뉴" if menus else "메뉴 정보가 없습니다"
    )


@app.get("/api/menus/week", response_model=MenuResponse)
async def get_weekly_menus(
    start_date: Optional[date] = Query(None, description="시작 날짜 (기본값: 오늘)")
):
    """주간 메뉴를 조회합니다."""
    if start_date is None:
        start_date = date.today()
    
    end_date = start_date + timedelta(days=6)
    menus = db.get_weekly_menus(start_date, end_date)
    
    if not menus:
        # 데이터가 없으면 크롤링
        menus = crawler.crawl_weekly_menu(start_date)
        db.save_menus(menus)
    
    return MenuResponse(
        success=True,
        data=menus,
        message=f"{start_date} ~ {end_date} 메뉴 {len(menus)}개"
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


@app.get("/api/menus/month", response_model=MenuResponse)
async def get_monthly_menus(
    year: Optional[int] = Query(None, description="연도 (기본값: 올해)"),
    month: Optional[int] = Query(None, description="월 (기본값: 이번달)")
):
    """월간 메뉴를 조회합니다."""
    if year is None or month is None:
        today = date.today()
        year = year or today.year
        month = month or today.month
    
    # 데이터베이스에서 해당 월의 메뉴 조회
    import calendar
    _, last_day = calendar.monthrange(year, month)
    start_date = date(year, month, 1)
    end_date = date(year, month, last_day)
    
    menus = db.get_weekly_menus(start_date, end_date)
    
    if not menus:
        # 데이터가 없으면 크롤링
        menus = crawler.crawl_monthly_menu(year, month)
        if menus:
            db.save_menus(menus)
    
    return MenuResponse(
        success=True,
        data=menus,
        message=f"{year}년 {month}월 메뉴 {len(menus)}개"
    )


@app.post("/api/menus/refresh")
async def refresh_menus():
    """메뉴 정보를 강제로 갱신합니다."""
    try:
        update_menus()
        return {
            "success": True,
            "message": "메뉴 정보가 갱신되었습니다"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"메뉴 갱신 실패: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
