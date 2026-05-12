from fastapi import FastAPI, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from datetime import date, datetime, timedelta
from typing import Optional
import threading
import logging
import os
import json
import time
import re

from dotenv import load_dotenv
from pywebpush import webpush, WebPushException

load_dotenv()

from models import (
    MenuResponse, DailyMenuResponse,
    Restaurant,
    PushSubscribeRequest,
    PushUnsubscribeRequest,
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

def get_allowed_origins() -> list[str]:
    origins = os.getenv(
        "CORS_ALLOWED_ORIGINS",
        ",".join(
            [
                "http://localhost:3000",
                "http://127.0.0.1:3000",
                "http://localhost:3001",
                "http://127.0.0.1:3001",
                "http://localhost:5000",
                "http://127.0.0.1:5000",
                "http://localhost:5173",
                "http://127.0.0.1:5173",
            ]
        ),
    )
    return [origin.strip() for origin in origins.split(",") if origin.strip()]


def is_allowed_origin(origin: str) -> bool:
    if origin in get_allowed_origins():
        return True

    origin_regex = os.getenv("CORS_ALLOWED_ORIGIN_REGEX", r"https://.*\.netlify\.app")
    return bool(origin_regex and re.fullmatch(origin_regex, origin))


# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_origin_regex=os.getenv("CORS_ALLOWED_ORIGIN_REGEX", r"https://.*\.netlify\.app"),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_private_network_access_header(request: Request, call_next):
    if (
        request.method == "OPTIONS"
        and request.headers.get("access-control-request-private-network") == "true"
    ):
        origin = request.headers.get("origin", "")
        request_method = request.headers.get("access-control-request-method", "")
        if origin and request_method and is_allowed_origin(origin):
            request_headers = request.headers.get("access-control-request-headers", "*")
            response = Response(status_code=200)
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Methods"] = "DELETE, GET, HEAD, OPTIONS, PATCH, POST, PUT"
            response.headers["Access-Control-Allow-Headers"] = request_headers or "*"
            response.headers["Access-Control-Allow-Private-Network"] = "true"
            response.headers["Access-Control-Max-Age"] = "600"
            response.headers["Vary"] = "Origin"
            return response

    response = await call_next(request)
    response.headers["Access-Control-Allow-Private-Network"] = "true"
    return response

crawler = SMUCafeteriaCrawler()
_update_lock = threading.Lock()
_is_updating = False
_last_update_started_at = 0.0
_scheduler_started = False
_scheduler_stop_event = threading.Event()

VAPID_PUBLIC_KEY = os.getenv("VAPID_PUBLIC_KEY", "")
VAPID_PRIVATE_KEY = os.getenv("VAPID_PRIVATE_KEY", "")
VAPID_CLAIMS_SUB = os.getenv("VAPID_CLAIMS_SUB", "mailto:admin@smubab.app")


def get_effective_week_date(target_date: date) -> date:
    if target_date.weekday() >= 5:
        return target_date + timedelta(days=7 - target_date.weekday())
    return target_date


def get_week_bounds(target_date: date) -> tuple[date, date]:
    effective_date = get_effective_week_date(target_date)
    monday = effective_date - timedelta(days=effective_date.weekday())
    friday = monday + timedelta(days=4)
    return monday, friday


def is_push_enabled() -> bool:
    return bool(VAPID_PUBLIC_KEY and VAPID_PRIVATE_KEY)


def send_push_payload(payload: dict):
    if not is_push_enabled():
        logger.info("Push disabled: missing VAPID keys")
        return {"sent": 0, "removed": 0, "total": 0}

    subscriptions = db.get_push_subscriptions()
    if not subscriptions:
        return {"sent": 0, "removed": 0, "total": 0}

    removed_count = 0
    sent_count = 0
    for subscription in subscriptions:
        try:
            webpush(
                subscription_info=subscription,
                data=json.dumps(payload, ensure_ascii=False),
                vapid_private_key=VAPID_PRIVATE_KEY,
                vapid_claims={"sub": VAPID_CLAIMS_SUB},
            )
            sent_count += 1
        except WebPushException as error:
            status_code = getattr(getattr(error, "response", None), "status_code", None)
            if status_code in (404, 410):
                endpoint = subscription.get("endpoint")
                if endpoint and db.remove_push_subscription(endpoint):
                    removed_count += 1
            else:
                logger.warning(f"Push send failed: {error}")
        except Exception as error:
            logger.warning(f"Push send failed: {error}")

    logger.info(f"Push sent={sent_count}, removed={removed_count}, total={len(subscriptions)}")
    return {"sent": sent_count, "removed": removed_count, "total": len(subscriptions)}


def send_menu_update_notification(target_date: date, saved_count: int):
    title = "🍚 학식 메뉴 업데이트"
    body = f"{target_date} 기준 메뉴가 새로 업데이트되었습니다. ({saved_count}건)"
    payload = {
        "title": title,
        "body": body,
        "url": "/",
        "tag": f"menu-update-{target_date.isoformat()}",
    }
    send_push_payload(payload)


def trigger_test_push_notification(delay_seconds: int = 10):
    def _task():
        time.sleep(delay_seconds)
        payload = {
            "title": "🔔 테스트 알림",
            "body": f"버튼 클릭 후 {delay_seconds}초가 지나 테스트 푸시가 도착했습니다.",
            "url": "/",
            "tag": f"push-test-{int(time.time())}",
        }
        result = send_push_payload(payload)
        logger.info(f"Test push result: {result}")

    thread = threading.Thread(target=_task, daemon=True)
    thread.start()


def update_menus(target_date: Optional[date] = None, notify: bool = False):
    if target_date is None:
        target_date = date.today()

    monday, friday = get_week_bounds(target_date)
    menus = crawler.crawl_weekly_menu(target_date)
    saved_count = db.save_menus(menus)
    db.clear_old_menus(date.today() - timedelta(days=7))
    logger.info(f"Updated {saved_count} menus for {monday} ~ {friday}")

    if notify and saved_count > 0:
        send_menu_update_notification(target_date, saved_count)


def trigger_update_menus(
    target_date: Optional[date] = None,
    notify: bool = False,
    force: bool = False,
) -> bool:
    global _is_updating, _last_update_started_at
    with _update_lock:
        if _is_updating:
            return False

        min_interval_seconds = int(os.getenv("MENU_REFRESH_MIN_INTERVAL_SECONDS", "1800"))
        now = time.time()
        if (
            not force
            and min_interval_seconds > 0
            and _last_update_started_at
            and now - _last_update_started_at < min_interval_seconds
        ):
            return False

        _is_updating = True
        _last_update_started_at = now

    def _task():
        global _is_updating
        try:
            update_menus(target_date, notify)
        except Exception as error:
            logger.warning(f"Menu update failed: {error}")
        finally:
            with _update_lock:
                _is_updating = False

    thread = threading.Thread(target=_task, daemon=True)
    thread.start()
    return True


def start_menu_update_scheduler():
    global _scheduler_started
    if _scheduler_started:
        return

    weekday_interval_seconds = int(os.getenv("MENU_UPDATE_INTERVAL_SECONDS", "21600"))
    weekend_interval_seconds = int(
        os.getenv("MENU_WEEKEND_UPDATE_INTERVAL_SECONDS", "3600")
    )
    if weekday_interval_seconds <= 0 and weekend_interval_seconds <= 0:
        logger.info("Menu update scheduler disabled")
        return

    _scheduler_started = True

    def _loop():
        logger.info(
            "Menu update scheduler started: weekday=%ss weekend=%ss",
            weekday_interval_seconds,
            weekend_interval_seconds,
        )
        while not _scheduler_stop_event.is_set():
            trigger_update_menus(date.today(), notify=True)
            is_weekend = date.today().weekday() >= 5
            interval_seconds = (
                weekend_interval_seconds if is_weekend else weekday_interval_seconds
            )
            if interval_seconds <= 0:
                interval_seconds = max(weekday_interval_seconds, weekend_interval_seconds)
            if _scheduler_stop_event.wait(interval_seconds):
                break

    thread = threading.Thread(target=_loop, daemon=True)
    thread.start()


@app.on_event("startup")
async def startup_event():
    """서버 시작 시 실행"""
    logger.info("Starting SMU-Bab API server...")
    trigger_update_menus(date.today(), notify=False, force=True)
    start_menu_update_scheduler()
    logger.info("Server started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """서버 종료 시 실행"""
    _scheduler_stop_event.set()
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
        trigger_update_menus(today, notify=True, force=True)
        return DailyMenuResponse(
            success=False,
            date=today,
            menus=[],
            error="메뉴 업데이트 중입니다. 잠시 후 다시 시도해 주세요.",
        )

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
        trigger_update_menus(target_date, notify=True, force=True)
        return DailyMenuResponse(
            success=False,
            date=target_date,
            menus=[],
            error="메뉴 업데이트 중입니다. 잠시 후 다시 시도해 주세요.",
        )

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
    monday, friday = get_week_bounds(target_date)
    
    # 데이터베이스에서 조회
    menus = db.get_weekly_menus(monday, friday)

    if not menus:
        trigger_update_menus(target_date, notify=True, force=True)
        return MenuResponse(
            success=False,
            data=[],
            error="메뉴 업데이트 중입니다. 잠시 후 다시 시도해 주세요.",
        )

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
        update_menus(date.today(), notify=True)
        return {
            "success": True,
            "message": "메뉴 정보가 갱신되었습니다"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"메뉴 갱신 실패: {str(e)}")


@app.post("/api/menus/refresh-async")
async def refresh_menus_async():
    """메뉴 갱신을 백그라운드로 예약합니다."""
    started = trigger_update_menus(date.today(), notify=True)
    return {
        "success": True,
        "started": started,
        "message": "메뉴 갱신이 예약되었습니다" if started else "메뉴 갱신이 이미 진행 중입니다",
    }


@app.get("/api/push/public-key")
async def get_push_public_key():
    if not is_push_enabled():
        return {
            "success": False,
            "message": "Push notifications are not configured",
            "publicKey": None,
        }

    return {
        "success": True,
        "publicKey": VAPID_PUBLIC_KEY,
    }


@app.get("/api/push/status")
async def get_push_status():
    return {
        "success": True,
        "configured": is_push_enabled(),
        "subscriptionCount": len(db.get_push_subscriptions()),
    }


@app.post("/api/push/subscribe")
async def subscribe_push(request: PushSubscribeRequest):
    if not is_push_enabled():
        raise HTTPException(status_code=503, detail="Push notifications are not configured")

    saved = db.upsert_push_subscription(request.subscription.model_dump())
    if not saved:
        raise HTTPException(status_code=400, detail="Invalid subscription")

    return {
        "success": True,
        "message": "Push subscription registered",
    }


@app.post("/api/push/unsubscribe")
async def unsubscribe_push(request: PushUnsubscribeRequest):
    removed = db.remove_push_subscription(request.endpoint)
    return {
        "success": True,
        "removed": removed,
    }


@app.post("/api/push/test")
async def send_test_push():
    if not is_push_enabled():
        raise HTTPException(status_code=503, detail="Push notifications are not configured")

    subscription_count = len(db.get_push_subscriptions())
    if subscription_count == 0:
        raise HTTPException(status_code=400, detail="No push subscriptions registered")

    trigger_test_push_notification(delay_seconds=10)

    return {
        "success": True,
        "message": "테스트 알림이 예약되었습니다. 10초 후 도착합니다.",
        "delaySeconds": 10,
        "subscriptionCount": subscription_count,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
