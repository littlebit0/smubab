from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from datetime import date, datetime, timedelta
from typing import Optional
import threading
import logging
import os
import json
import time

from pywebpush import webpush, WebPushException

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

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인만 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

crawler = SMUCafeteriaCrawler()
_update_lock = threading.Lock()
_is_updating = False

VAPID_PUBLIC_KEY = os.getenv("VAPID_PUBLIC_KEY", "")
VAPID_PRIVATE_KEY = os.getenv("VAPID_PRIVATE_KEY", "")
VAPID_CLAIMS_SUB = os.getenv("VAPID_CLAIMS_SUB", "mailto:admin@smubab.app")


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

    weekday = target_date.weekday()
    monday = target_date - timedelta(days=weekday)
    friday = monday + timedelta(days=4)

    menus = crawler.crawl_weekly_menu(target_date)
    saved_count = db.save_menus(menus)
    db.clear_old_menus(date.today() - timedelta(days=7))
    logger.info(f"Updated {saved_count} menus for {monday} ~ {friday}")

    if notify and saved_count > 0:
        send_menu_update_notification(target_date, saved_count)


def trigger_update_menus(target_date: Optional[date] = None, notify: bool = False) -> bool:
    global _is_updating
    with _update_lock:
        if _is_updating:
            return False
        _is_updating = True

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


@app.on_event("startup")
async def startup_event():
    """서버 시작 시 실행"""
    logger.info("Starting SMU-Bab API server...")
    trigger_update_menus(date.today(), notify=False)
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
        trigger_update_menus(today, notify=True)
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
        trigger_update_menus(target_date, notify=True)
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
    weekday = target_date.weekday()
    monday = target_date - timedelta(days=weekday)
    friday = monday + timedelta(days=4)
    
    # 데이터베이스에서 조회
    menus = db.get_weekly_menus(monday, friday)

    if not menus:
        trigger_update_menus(target_date, notify=True)
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
        db.menus = []
        update_menus(date.today(), notify=True)
        return {
            "success": True,
            "message": "메뉴 정보가 갱신되었습니다"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"메뉴 갱신 실패: {str(e)}")


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
    uvicorn.run(app, host="0.0.0.0", port=8000)
