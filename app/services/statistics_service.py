from __future__ import annotations

from dataclasses import dataclass

from app.db.connection import Database
from app.db.repositories import SettingsRepository


@dataclass(frozen=True)
class InventoryStatistics:
    available: int
    reserved: int
    consumed: int
    skill_count: int
    total_created: int
    total_cost_gp: int
    available_value_gp: int


class StatisticsService:
    def __init__(self, database: Database) -> None:
        self.database = database
        self.settings = SettingsRepository()

    def calculate(self) -> InventoryStatistics:
        with self.database.session() as connection:
            counts = {row["status"]: int(row["amount"]) for row in connection.execute(
                "SELECT status, COUNT(*) amount FROM player_items GROUP BY status"
            ).fetchall()}
            skill_count = int(connection.execute("SELECT COUNT(*) FROM skills").fetchone()[0])
            total_created = int(connection.execute(
                "SELECT COUNT(*) FROM operation_history WHERE action IN ('player_created', 'csv_import_row')"
            ).fetchone()[0])
            cost = int(self.settings.get(connection, "skill_cost_gp", "250000"))
        available = counts.get("available", 0)
        return InventoryStatistics(available, counts.get("reserved", 0), counts.get("consumed", 0),
                                   skill_count, total_created, total_created * cost, available * cost)

    def low_stock_skills(self) -> list[str]:
        with self.database.session() as connection:
            threshold = int(self.settings.get(connection, "low_stock_threshold", "1"))
            rows = connection.execute(
                """SELECT s.name, SUM(CASE WHEN p.status='available' THEN 1 ELSE 0 END) amount
                   FROM skills s LEFT JOIN player_items p ON p.skill_id=s.id WHERE s.enabled=1
                   GROUP BY s.id HAVING amount <= ? ORDER BY s.name COLLATE NOCASE""", (threshold,)
            ).fetchall()
            return [str(row["name"]) for row in rows]
