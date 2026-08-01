from __future__ import annotations

import sqlite3

from app.db.connection import Database
from app.db.repositories import HistoryRepository, SkillRepository
from app.models import Skill
from app.utils.datetime_utils import local_now_iso
from app.utils.validators import required_text


class SkillService:
    def __init__(self, database: Database) -> None:
        self.database = database
        self.repo = SkillRepository()
        self.history = HistoryRepository()

    def list_skills(self, enabled_only: bool = False) -> list[Skill]:
        with self.database.session() as connection:
            return self.repo.list(connection, enabled_only)

    def create(self, name: str, category: str | None = None) -> Skill:
        name = required_text(name, "技能名称")
        category = category.strip() if category and category.strip() else None
        try:
            with self.database.session() as connection:
                skill = self.repo.create(connection, name, category, local_now_iso())
                self.history.add(connection, "skill_created", new_data=skill.__dict__, detail=f"新增技能：{name}")
                return skill
        except sqlite3.IntegrityError as exc:
            raise ValueError("技能名称已存在") from exc

    def update(self, skill_id: int, name: str, category: str | None, enabled: bool) -> Skill:
        name = required_text(name, "技能名称")
        category = category.strip() if category and category.strip() else None
        try:
            with self.database.session() as connection:
                old = self.repo.get(connection, skill_id)
                if not old:
                    raise ValueError("技能不存在")
                updated = self.repo.update(connection, skill_id, name, category, enabled, local_now_iso())
                action = "skill_disabled" if old.enabled and not enabled else "skill_updated"
                self.history.add(connection, action, old_data=old.__dict__, new_data=updated.__dict__, detail=f"更新技能：{name}")
                return updated
        except sqlite3.IntegrityError as exc:
            raise ValueError("技能名称已存在") from exc

    def counts(self) -> list[dict[str, object]]:
        with self.database.session() as connection:
            return self.repo.counts(connection)

