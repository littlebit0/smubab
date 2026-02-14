from pydantic import BaseModel
from datetime import date, datetime
from typing import List, Optional
from enum import Enum


class MealType(str, Enum):
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"


class Restaurant(str, Enum):
    # 서울캠퍼스
    SEOUL_STUDENT = "서울_학생식당"
    SEOUL_FACULTY = "서울_교직원식당"
    SEOUL_FOODCOURT = "서울_푸드코트"
    # 천안캠퍼스
    CHEONAN_STUDENT = "천안_학생식당"
    CHEONAN_FACULTY = "천안_교직원식당"


class MenuItem(BaseModel):
    name: str
    price: Optional[int] = None
    calories: Optional[int] = None


class Menu(BaseModel):
    id: Optional[int] = None
    date: date
    restaurant: Restaurant
    meal_type: MealType
    items: List[MenuItem]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        use_enum_values = True


class MenuResponse(BaseModel):
    success: bool
    data: List[Menu]
    message: Optional[str] = None


class DailyMenuResponse(BaseModel):
    success: bool
    date: date
    menus: List[Menu]
    message: Optional[str] = None


class PushSubscriptionKeys(BaseModel):
    p256dh: str
    auth: str


class PushSubscription(BaseModel):
    endpoint: str
    expirationTime: Optional[int] = None
    keys: PushSubscriptionKeys


class PushSubscribeRequest(BaseModel):
    subscription: PushSubscription


class PushUnsubscribeRequest(BaseModel):
    endpoint: str
