from __future__ import annotations

from app.db.connection import Database
from app.db.repositories import SettingsRepository


class SettingsService:
    def __init__(self, database: Database) -> None:
        self.database = database
        self.repo = SettingsRepository()

    def get(self, key: str, default: str = "") -> str:
        with self.database.session() as connection:
            return self.repo.get(connection, key, default)

    def set(self, key: str, value: str) -> None:
        with self.database.session() as connection:
            self.repo.set(connection, key, value)

    def get_bool(self, key: str, default: bool = False) -> bool:
        return self.get(key, str(default).lower()).lower() in {"1", "true", "yes", "on"}

    def get_int(self, key: str, default: int) -> int:
        try:
            return int(self.get(key, str(default)))
        except ValueError:
            return default

