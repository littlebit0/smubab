from datetime import date, datetime
from typing import List, Optional
from models import Menu, MenuItem, MealType, Restaurant
import json


class MenuDatabase:
    """간단한 인메모리 데이터베이스 (추후 SQLite/PostgreSQL로 교체 가능)"""
    
    def __init__(self):
        self.menus: List[Menu] = []
        self.push_subscriptions: List[dict] = []
    
    def save_menus(self, menus: List[Menu]) -> int:
        """메뉴 목록을 저장합니다."""
        saved_count = 0
        for menu in menus:
            # 중복 체크 (같은 날짜, 식당, 식사 타입)
            existing = self.get_menu(menu.date, menu.restaurant, menu.meal_type)
            if existing:
                # 기존 메뉴 업데이트
                self.menus.remove(existing)
            
            self.menus.append(menu)
            saved_count += 1
        
        return saved_count
    
    def get_menu(
        self, 
        target_date: date, 
        restaurant: Optional[Restaurant] = None,
        meal_type: Optional[MealType] = None
    ) -> Optional[Menu]:
        """특정 조건의 메뉴를 조회합니다."""
        for menu in self.menus:
            if menu.date == target_date:
                if restaurant and menu.restaurant != restaurant:
                    continue
                if meal_type and menu.meal_type != meal_type:
                    continue
                return menu
        return None
    
    def get_daily_menus(self, target_date: date) -> List[Menu]:
        """특정 날짜의 모든 메뉴를 조회합니다."""
        return [menu for menu in self.menus if menu.date == target_date]
    
    def get_weekly_menus(self, start_date: date, end_date: date) -> List[Menu]:
        """특정 기간의 메뉴를 조회합니다."""
        return [
            menu for menu in self.menus 
            if start_date <= menu.date <= end_date
        ]
    
    def get_menus_by_restaurant(self, restaurant: Restaurant, target_date: date = None) -> List[Menu]:
        """특정 식당의 메뉴를 조회합니다."""
        menus = [menu for menu in self.menus if menu.restaurant == restaurant]
        if target_date:
            menus = [menu for menu in menus if menu.date == target_date]
        return menus
    
    def clear_old_menus(self, before_date: date) -> int:
        """특정 날짜 이전의 메뉴를 삭제합니다."""
        old_menus = [menu for menu in self.menus if menu.date < before_date]
        for menu in old_menus:
            self.menus.remove(menu)
        return len(old_menus)

    def upsert_push_subscription(self, subscription: dict) -> bool:
        endpoint = subscription.get("endpoint")
        if not endpoint:
            return False

        existing = next(
            (item for item in self.push_subscriptions if item.get("endpoint") == endpoint),
            None,
        )
        if existing:
            self.push_subscriptions.remove(existing)

        self.push_subscriptions.append(subscription)
        return True

    def remove_push_subscription(self, endpoint: str) -> bool:
        existing = next(
            (item for item in self.push_subscriptions if item.get("endpoint") == endpoint),
            None,
        )
        if not existing:
            return False

        self.push_subscriptions.remove(existing)
        return True

    def get_push_subscriptions(self) -> List[dict]:
        return list(self.push_subscriptions)


# 전역 데이터베이스 인스턴스
db = MenuDatabase()
