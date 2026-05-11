from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import threading
from datetime import date, datetime
from pathlib import Path
from typing import Any, List, Optional

from models import MealType, Menu, MenuItem, Restaurant


class MenuDatabase:
    """Persistent menu cache and web push subscription store.

    Uses PostgreSQL when DATABASE_URL starts with postgres/postgresql, otherwise
    falls back to a local SQLite file. This avoids ORM compatibility issues in
    local Python 3.14 while keeping Render PostgreSQL support.
    """

    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or os.getenv("DATABASE_URL", "")
        self.is_postgres = self.database_url.startswith(("postgres://", "postgresql://"))
        self._lock = threading.RLock()

        if self.is_postgres:
            import psycopg
            from psycopg.rows import dict_row

            self._connection = psycopg.connect(
                self.database_url,
                autocommit=False,
                row_factory=dict_row,
            )
        else:
            db_path = Path(
                os.getenv("MENU_DB_PATH", str(Path(__file__).with_name("smubab.db")))
            )
            db_path.parent.mkdir(parents=True, exist_ok=True)
            self._connection = sqlite3.connect(
                db_path.expanduser().resolve(),
                check_same_thread=False,
            )
            self._connection.row_factory = sqlite3.Row

        self._initialize()

    def _initialize(self) -> None:
        with self._lock:
            cursor = self._connection.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS menus (
                    date TEXT NOT NULL,
                    restaurant TEXT NOT NULL,
                    meal_type TEXT NOT NULL,
                    items_json TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL,
                    PRIMARY KEY (date, restaurant, meal_type)
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS push_subscriptions (
                    endpoint TEXT PRIMARY KEY,
                    subscription_json TEXT NOT NULL,
                    updated_at TIMESTAMP NOT NULL
                )
                """
            )
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_menus_date ON menus(date)")
            self._connection.commit()

    def save_menus(self, menus: List[Menu]) -> int:
        changed_count = 0
        now = datetime.now()
        with self._lock:
            cursor = self._connection.cursor()
            for menu in menus:
                date_value = menu.date.isoformat()
                restaurant = self._enum_value(menu.restaurant)
                meal_type = self._enum_value(menu.meal_type)
                items_json = self._items_to_json(menu.items)
                content_hash = hashlib.sha256(items_json.encode("utf-8")).hexdigest()

                cursor.execute(
                    self._sql(
                        """
                        SELECT content_hash, created_at
                        FROM menus
                        WHERE date = ? AND restaurant = ? AND meal_type = ?
                        """
                    ),
                    (date_value, restaurant, meal_type),
                )
                existing = cursor.fetchone()
                if existing and existing["content_hash"] == content_hash:
                    continue

                if existing:
                    cursor.execute(
                        self._sql(
                            """
                            UPDATE menus
                            SET items_json = ?,
                                content_hash = ?,
                                updated_at = ?
                            WHERE date = ? AND restaurant = ? AND meal_type = ?
                            """
                        ),
                        (
                            items_json,
                            content_hash,
                            now,
                            date_value,
                            restaurant,
                            meal_type,
                        ),
                    )
                else:
                    cursor.execute(
                        self._sql(
                            """
                            INSERT INTO menus (
                                date, restaurant, meal_type, items_json,
                                content_hash, created_at, updated_at
                            )
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                            """
                        ),
                        (
                            date_value,
                            restaurant,
                            meal_type,
                            items_json,
                            content_hash,
                            now,
                            now,
                        ),
                    )
                changed_count += 1

            self._connection.commit()
        return changed_count

    def get_menu(
        self,
        target_date: date,
        restaurant: Optional[Restaurant] = None,
        meal_type: Optional[MealType] = None,
    ) -> Optional[Menu]:
        query = "SELECT * FROM menus WHERE date = ?"
        params: list[Any] = [target_date.isoformat()]
        if restaurant:
            query += " AND restaurant = ?"
            params.append(self._enum_value(restaurant))
        if meal_type:
            query += " AND meal_type = ?"
            params.append(self._enum_value(meal_type))
        query += " ORDER BY restaurant, meal_type LIMIT 1"

        with self._lock:
            cursor = self._connection.cursor()
            cursor.execute(self._sql(query), params)
            row = cursor.fetchone()
        return self._row_to_menu(row) if row else None

    def get_daily_menus(self, target_date: date) -> List[Menu]:
        with self._lock:
            cursor = self._connection.cursor()
            cursor.execute(
                self._sql(
                    """
                    SELECT * FROM menus
                    WHERE date = ?
                    ORDER BY restaurant, meal_type
                    """
                ),
                (target_date.isoformat(),),
            )
            rows = cursor.fetchall()
        return [self._row_to_menu(row) for row in rows]

    def get_weekly_menus(self, start_date: date, end_date: date) -> List[Menu]:
        with self._lock:
            cursor = self._connection.cursor()
            cursor.execute(
                self._sql(
                    """
                    SELECT * FROM menus
                    WHERE date >= ? AND date <= ?
                    ORDER BY date, restaurant, meal_type
                    """
                ),
                (start_date.isoformat(), end_date.isoformat()),
            )
            rows = cursor.fetchall()
        return [self._row_to_menu(row) for row in rows]

    def get_menus_by_restaurant(
        self,
        restaurant: Restaurant,
        target_date: date | None = None,
    ) -> List[Menu]:
        query = "SELECT * FROM menus WHERE restaurant = ?"
        params: list[Any] = [self._enum_value(restaurant)]
        if target_date:
            query += " AND date = ?"
            params.append(target_date.isoformat())
        query += " ORDER BY date, meal_type"

        with self._lock:
            cursor = self._connection.cursor()
            cursor.execute(self._sql(query), params)
            rows = cursor.fetchall()
        return [self._row_to_menu(row) for row in rows]

    def clear_old_menus(self, before_date: date) -> int:
        with self._lock:
            cursor = self._connection.cursor()
            cursor.execute(
                self._sql("DELETE FROM menus WHERE date < ?"),
                (before_date.isoformat(),),
            )
            self._connection.commit()
            return cursor.rowcount or 0

    def clear_menus(self) -> int:
        with self._lock:
            cursor = self._connection.cursor()
            cursor.execute("DELETE FROM menus")
            self._connection.commit()
            return cursor.rowcount or 0

    def upsert_push_subscription(self, subscription: dict) -> bool:
        endpoint = subscription.get("endpoint")
        if not endpoint:
            return False

        now = datetime.now()
        payload = json.dumps(subscription, ensure_ascii=False)
        with self._lock:
            cursor = self._connection.cursor()
            cursor.execute(
                self._sql("SELECT endpoint FROM push_subscriptions WHERE endpoint = ?"),
                (endpoint,),
            )
            existing = cursor.fetchone()
            if existing:
                cursor.execute(
                    self._sql(
                        """
                        UPDATE push_subscriptions
                        SET subscription_json = ?, updated_at = ?
                        WHERE endpoint = ?
                        """
                    ),
                    (payload, now, endpoint),
                )
            else:
                cursor.execute(
                    self._sql(
                        """
                        INSERT INTO push_subscriptions (
                            endpoint, subscription_json, updated_at
                        )
                        VALUES (?, ?, ?)
                        """
                    ),
                    (endpoint, payload, now),
                )
            self._connection.commit()
        return True

    def remove_push_subscription(self, endpoint: str) -> bool:
        with self._lock:
            cursor = self._connection.cursor()
            cursor.execute(
                self._sql("DELETE FROM push_subscriptions WHERE endpoint = ?"),
                (endpoint,),
            )
            self._connection.commit()
            return bool(cursor.rowcount)

    def get_push_subscriptions(self) -> List[dict]:
        with self._lock:
            cursor = self._connection.cursor()
            cursor.execute("SELECT subscription_json FROM push_subscriptions")
            rows = cursor.fetchall()
        return [json.loads(row["subscription_json"]) for row in rows]

    def _sql(self, query: str) -> str:
        if self.is_postgres:
            return query.replace("?", "%s")
        return query

    @staticmethod
    def _enum_value(value) -> str:
        return getattr(value, "value", value)

    @staticmethod
    def _items_to_json(items: List[MenuItem]) -> str:
        normalized = [
            {
                "name": item.name,
                "price": item.price,
                "calories": item.calories,
            }
            for item in items
        ]
        return json.dumps(normalized, ensure_ascii=False, sort_keys=True)

    @staticmethod
    def _row_to_menu(row) -> Menu:
        items = [
            MenuItem(
                name=item.get("name", ""),
                price=item.get("price"),
                calories=item.get("calories"),
            )
            for item in json.loads(row["items_json"])
        ]
        return Menu(
            date=date.fromisoformat(row["date"]),
            restaurant=row["restaurant"],
            meal_type=row["meal_type"],
            items=items,
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


db = MenuDatabase()
