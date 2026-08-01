from __future__ import annotations

from typing import Any

from app.db.connection import Database
from app.db.repositories import HistoryRepository, PlayerRepository, SkillRepository, player_as_dict
from app.models import PlayerItem
from app.utils.datetime_utils import local_now_iso
from app.utils.validators import required_text, validate_status


class PlayerService:
    def __init__(self, database: Database) -> None:
        self.database = database
        self.players = PlayerRepository()
        self.skills = SkillRepository()
        self.history = HistoryRepository()

    def search(self, query: str = "", skill_id: int | None = None, status: str | None = None) -> list[PlayerItem]:
        if status:
            validate_status(status)
        with self.database.session() as connection:
            return self.players.search(connection, query, skill_id, status)

    def get(self, item_id: int) -> PlayerItem | None:
        with self.database.session() as connection:
            return self.players.get(connection, item_id)

    def create(self, player_name: str, skill_id: int, status: str = "available", reserved_for: str | None = None,
               consumed_for: str | None = None, note: str | None = None, *, action: str = "player_created") -> PlayerItem:
        now = local_now_iso()
        data = self._normalize(player_name, skill_id, status, reserved_for, consumed_for, note, now, now)
        with self.database.session() as connection:
            if not self.skills.get(connection, skill_id):
                raise ValueError("所选技能不存在")
            item = self.players.create(connection, data)
            self.history.add(connection, action, item.id, new_data=player_as_dict(item), detail="新增球员载体")
            return item

    def update(self, item_id: int, player_name: str, skill_id: int, status: str, reserved_for: str | None = None,
               consumed_for: str | None = None, note: str | None = None, *, action: str = "player_updated") -> PlayerItem:
        with self.database.session() as connection:
            old = self.players.get(connection, item_id)
            if not old:
                raise ValueError("球员载体不存在")
            if not self.skills.get(connection, skill_id):
                raise ValueError("所选技能不存在")
            consumed_at = old.consumed_at if status == "consumed" and old.status == "consumed" else None
            data = self._normalize(player_name, skill_id, status, reserved_for, consumed_for, note,
                                   old.created_at, local_now_iso(), consumed_at)
            updated = self.players.update(connection, item_id, data)
            actual_action = "status_changed" if old.status != updated.status else action
            self.history.add(connection, actual_action, item_id, player_as_dict(old), player_as_dict(updated), "更新球员载体")
            return updated

    def change_status(self, item_id: int, status: str, target: str | None = None) -> PlayerItem:
        item = self.get(item_id)
        if not item:
            raise ValueError("球员载体不存在")
        reserved = target if status == "reserved" else None
        consumed = target if status == "consumed" else None
        return self.update(item_id, item.player_name, item.skill_id, status, reserved, consumed, item.note)

    def delete(self, item_id: int) -> None:
        with self.database.session() as connection:
            item = self.players.get(connection, item_id)
            if not item:
                raise ValueError("球员载体不存在")
            snapshot = player_as_dict(item)
            self.players.delete(connection, item_id)
            self.history.add(connection, "player_deleted", item_id, old_data=snapshot, detail="删除球员载体")

    @staticmethod
    def _normalize(player_name: str, skill_id: int, status: str, reserved_for: str | None,
                   consumed_for: str | None, note: str | None, created_at: str, updated_at: str,
                   consumed_at: str | None = None) -> dict[str, Any]:
        player_name = required_text(player_name, "球员姓名")
        validate_status(status)
        reserved_for = reserved_for.strip() if reserved_for and reserved_for.strip() else None
        consumed_for = consumed_for.strip() if consumed_for and consumed_for.strip() else None
        note = note.strip() if note and note.strip() else None
        if status == "available":
            reserved_for = consumed_for = consumed_at = None
        elif status == "reserved":
            consumed_for = consumed_at = None
        else:
            reserved_for = None
            consumed_at = consumed_at or local_now_iso()
        return {"player_name": player_name, "skill_id": int(skill_id), "status": status,
                "reserved_for": reserved_for, "consumed_for": consumed_for, "note": note,
                "created_at": created_at, "updated_at": updated_at, "consumed_at": consumed_at}

