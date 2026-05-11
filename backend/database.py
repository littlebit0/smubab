from __future__ import annotations

import json
import os
import sqlite3
import threading
from datetime import date, datetime
from pathlib import Path
from typing import List, Optional

from models import MealType, Menu, MenuItem, Restaurant


class MenuDatabase:
    """SQLite-backed cache for menus and web push subscriptions."""

    def __init__(self, database_url: Optional[str] = None):
        self.db_path = self._resolve_db_path(database_url)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._connection = sqlite3.connect(
            self.db_path,
            check_same_thread=False,
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        self._connection.row_factory = sqlite3.Row
        self._initialize()

    @staticmethod
    def _resolve_db_path(database_url: Optional[str]) -> Path:
        raw = (
            database_url
            or os.getenv("MENU_DB_PATH")
            or os.getenv("DATABASE_URL")
            or str(Path(__file__).with_name("smubab.db"))
        )
        if raw.startswith("sqlite:///"):
            raw = raw.removeprefix("sqlite:///")
        elif raw.startswith("sqlite://"):
            raw = raw.removeprefix("sqlite://")
        return Path(raw).expanduser().resolve()

    def _initialize(self) -> None:
        with self._lock, self._connection:
            self._connection.execute(
                """
                CREATE TABLE IF NOT EXISTS menus (
                    date TEXT NOT NULL,
                    restaurant TEXT NOT NULL,
                    meal_type TEXT NOT NULL,
                    items_json TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY (date, restaurant, meal_type)
                )
                """
            )
            self._connection.execute(
                """
                CREATE TABLE IF NOT EXISTS push_subscriptions (
                    endpoint TEXT PRIMARY KEY,
                    subscription_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            self._connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_menus_date ON menus(date)"
            )

    def save_menus(self, menus: List[Menu]) -> int:
        """Upsert menus and return the number of newly changed rows."""
        changed_count = 0
        now = datetime.now().isoformat()
        with self._lock, self._connection:
            for menu in menus:
                items_json = self._items_to_json(menu.items)
                content_hash = self._menu_hash(items_json)
                key = (
                    menu.date.isoformat(),
                    self._enum_value(menu.restaurant),
                    self._enum_value(menu.meal_type),
                )
                existing = self._connection.execute(
                    """
                    SELECT content_hash, created_at
                    FROM menus
                    WHERE date = ? AND restaurant = ? AND meal_type = ?
                    """,
                    key,
                ).fetchone()
                if existing and existing["content_hash"] == content_hash:
                    continue

                created_at = existing["created_at"] if existing else now
                self._connection.execute(
                    """
                    INSERT INTO menus (
                        date, restaurant, meal_type, items_json,
                        content_hash, created_at, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(date, restaurant, meal_type)
                    DO UPDATE SET
                        items_json = excluded.items_json,
                        content_hash = excluded.content_hash,
                        updated_at = excluded.updated_at
                    """,
                    (*key, items_json, content_hash, created_at, now),
                )
                changed_count += 1

        return changed_count

    def get_menu(
        self,
        target_date: date,
        restaurant: Optional[Restaurant] = None,
        meal_type: Optional[MealType] = None,
    ) -> Optional[Menu]:
        query = "SELECT * FROM menus WHERE date = ?"
        params: list[str] = [target_date.isoformat()]
        if restaurant:
            query += " AND restaurant = ?"
            params.append(self._enum_value(restaurant))
        if meal_type:
            query += " AND meal_type = ?"
            params.append(self._enum_value(meal_type))
        query += " ORDER BY restaurant, meal_type LIMIT 1"

        with self._lock:
            row = self._connection.execute(query, params).fetchone()
        return self._row_to_menu(row) if row else None

    def get_daily_menus(self, target_date: date) -> List[Menu]:
        with self._lock:
            rows = self._connection.execute(
                """
                SELECT * FROM menus
                WHERE date = ?
                ORDER BY restaurant, meal_type
                """,
                (target_date.isoformat(),),
            ).fetchall()
        return [self._row_to_menu(row) for row in rows]

    def get_weekly_menus(self, start_date: date, end_date: date) -> List[Menu]:
        with self._lock:
            rows = self._connection.execute(
                """
                SELECT * FROM menus
                WHERE date BETWEEN ? AND ?
                ORDER BY date, restaurant, meal_type
                """,
                (start_date.isoformat(), end_date.isoformat()),
            ).fetchall()
        return [self._row_to_menu(row) for row in rows]

    def get_menus_by_restaurant(
        self,
        restaurant: Restaurant,
        target_date: date | None = None,
    ) -> List[Menu]:
        query = "SELECT * FROM menus WHERE restaurant = ?"
        params = [self._enum_value(restaurant)]
        if target_date:
            query += " AND date = ?"
            params.append(target_date.isoformat())
        query += " ORDER BY date, meal_type"

        with self._lock:
            rows = self._connection.execute(query, params).fetchall()
        return [self._row_to_menu(row) for row in rows]

    def clear_old_menus(self, before_date: date) -> int:
        with self._lock, self._connection:
            cursor = self._connection.execute(
                "DELETE FROM menus WHERE date < ?",
                (before_date.isoformat(),),
            )
            return cursor.rowcount

    def clear_menus(self) -> int:
        with self._lock, self._connection:
            cursor = self._connection.execute("DELETE FROM menus")
            return cursor.rowcount

    def upsert_push_subscription(self, subscription: dict) -> bool:
        endpoint = subscription.get("endpoint")
        if not endpoint:
            return False

        with self._lock, self._connection:
            self._connection.execute(
                """
                INSERT INTO push_subscriptions (
                    endpoint, subscription_json, updated_at
                )
                VALUES (?, ?, ?)
                ON CONFLICT(endpoint)
                DO UPDATE SET
                    subscription_json = excluded.subscription_json,
                    updated_at = excluded.updated_at
                """,
                (
                    endpoint,
                    json.dumps(subscription, ensure_ascii=False),
                    datetime.now().isoformat(),
                ),
            )
        return True

    def remove_push_subscription(self, endpoint: str) -> bool:
        with self._lock, self._connection:
            cursor = self._connection.execute(
                "DELETE FROM push_subscriptions WHERE endpoint = ?",
                (endpoint,),
            )
            return cursor.rowcount > 0

    def get_push_subscriptions(self) -> List[dict]:
        with self._lock:
            rows = self._connection.execute(
                "SELECT subscription_json FROM push_subscriptions"
            ).fetchall()
        return [json.loads(row["subscription_json"]) for row in rows]

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
    def _menu_hash(items_json: str) -> str:
        import hashlib

        return hashlib.sha256(items_json.encode("utf-8")).hexdigest()

    @staticmethod
    def _row_to_menu(row: sqlite3.Row) -> Menu:
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
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )


db = MenuDatabase()
