from __future__ import annotations

from typing import Any

from app.db.connection import Database
from app.db.repositories import HistoryRepository


class HistoryService:
    def __init__(self, database: Database) -> None:
        self.database = database
        self.repo = HistoryRepository()

    def list_recent(self, limit: int = 200) -> list[dict[str, Any]]:
        with self.database.session() as connection:
            return self.repo.list_recent(connection, limit)
