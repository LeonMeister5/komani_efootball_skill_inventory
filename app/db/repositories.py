from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict
from typing import Any, Iterable

from app.models import PlayerItem, Skill
from app.utils.datetime_utils import local_now_iso


def _skill(row: sqlite3.Row) -> Skill:
    return Skill(row["id"], row["name"], row["category"], bool(row["enabled"]), row["created_at"], row["updated_at"])


def _player(row: sqlite3.Row) -> PlayerItem:
    return PlayerItem(
        row["id"], row["player_name"], row["skill_id"], row["skill_name"], row["status"],
        row["reserved_for"], row["consumed_for"], row["note"], row["created_at"],
        row["updated_at"], row["consumed_at"],
    )


class SkillRepository:
    def list(self, connection: sqlite3.Connection, enabled_only: bool = False) -> list[Skill]:
        sql = "SELECT * FROM skills"
        params: tuple[Any, ...] = ()
        if enabled_only:
            sql += " WHERE enabled = ?"
            params = (1,)
        rows = connection.execute(sql + " ORDER BY name COLLATE NOCASE", params).fetchall()
        return [_skill(row) for row in rows]

    def get(self, connection: sqlite3.Connection, skill_id: int) -> Skill | None:
        row = connection.execute("SELECT * FROM skills WHERE id = ?", (skill_id,)).fetchone()
        return _skill(row) if row else None

    def get_by_name(self, connection: sqlite3.Connection, name: str) -> Skill | None:
        row = connection.execute("SELECT * FROM skills WHERE name = ? COLLATE NOCASE", (name,)).fetchone()
        return _skill(row) if row else None

    def create(self, connection: sqlite3.Connection, name: str, category: str | None, now: str) -> Skill:
        cursor = connection.execute(
            "INSERT INTO skills(name, category, enabled, created_at, updated_at) VALUES (?, ?, 1, ?, ?)",
            (name, category, now, now),
        )
        return self.get(connection, int(cursor.lastrowid))  # type: ignore[return-value]

    def update(self, connection: sqlite3.Connection, skill_id: int, name: str, category: str | None, enabled: bool, now: str) -> Skill:
        connection.execute(
            "UPDATE skills SET name = ?, category = ?, enabled = ?, updated_at = ? WHERE id = ?",
            (name, category, int(enabled), now, skill_id),
        )
        return self.get(connection, skill_id)  # type: ignore[return-value]

    def counts(self, connection: sqlite3.Connection) -> list[dict[str, Any]]:
        rows = connection.execute(
            """SELECT s.id, s.name, s.category, s.enabled,
               SUM(CASE WHEN p.status='available' THEN 1 ELSE 0 END) available,
               SUM(CASE WHEN p.status='reserved' THEN 1 ELSE 0 END) reserved,
               SUM(CASE WHEN p.status='consumed' THEN 1 ELSE 0 END) consumed
               FROM skills s LEFT JOIN player_items p ON p.skill_id=s.id
               GROUP BY s.id ORDER BY s.name COLLATE NOCASE"""
        ).fetchall()
        return [dict(row) for row in rows]


class PlayerRepository:
    _select = """SELECT p.*, s.name AS skill_name FROM player_items p
                 JOIN skills s ON s.id = p.skill_id"""

    def get(self, connection: sqlite3.Connection, item_id: int) -> PlayerItem | None:
        row = connection.execute(self._select + " WHERE p.id = ?", (item_id,)).fetchone()
        return _player(row) if row else None

    def search(self, connection: sqlite3.Connection, query: str = "", skill_id: int | None = None, status: str | None = None) -> list[PlayerItem]:
        clauses: list[str] = []
        params: list[Any] = []
        if query.strip():
            clauses.append("(p.player_name LIKE ? COLLATE NOCASE OR s.name LIKE ? COLLATE NOCASE)")
            term = f"%{query.strip()}%"
            params.extend((term, term))
        if skill_id is not None:
            clauses.append("p.skill_id = ?")
            params.append(skill_id)
        if status:
            clauses.append("p.status = ?")
            params.append(status)
        sql = self._select
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY CASE p.status WHEN 'available' THEN 0 WHEN 'reserved' THEN 1 ELSE 2 END, p.id DESC"
        return [_player(row) for row in connection.execute(sql, params).fetchall()]

    def create(self, connection: sqlite3.Connection, data: dict[str, Any]) -> PlayerItem:
        cursor = connection.execute(
            """INSERT INTO player_items(player_name, skill_id, status, reserved_for, consumed_for,
               note, created_at, updated_at, consumed_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            tuple(data[key] for key in ("player_name", "skill_id", "status", "reserved_for", "consumed_for", "note", "created_at", "updated_at", "consumed_at")),
        )
        return self.get(connection, int(cursor.lastrowid))  # type: ignore[return-value]

    def update(self, connection: sqlite3.Connection, item_id: int, data: dict[str, Any]) -> PlayerItem:
        connection.execute(
            """UPDATE player_items SET player_name=?, skill_id=?, status=?, reserved_for=?,
               consumed_for=?, note=?, updated_at=?, consumed_at=? WHERE id=?""",
            tuple(data[key] for key in ("player_name", "skill_id", "status", "reserved_for", "consumed_for", "note", "updated_at", "consumed_at")) + (item_id,),
        )
        return self.get(connection, item_id)  # type: ignore[return-value]

    def delete(self, connection: sqlite3.Connection, item_id: int) -> None:
        connection.execute("DELETE FROM player_items WHERE id = ?", (item_id,))


class HistoryRepository:
    def add(self, connection: sqlite3.Connection, action: str, player_item_id: int | None = None,
            old_data: Any = None, new_data: Any = None, detail: str | None = None) -> None:
        encode = lambda value: json.dumps(value, ensure_ascii=False, default=str) if value is not None else None
        connection.execute(
            "INSERT INTO operation_history(player_item_id, action, old_data, new_data, detail, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (player_item_id, action, encode(old_data), encode(new_data), detail, local_now_iso()),
        )

    def list_recent(self, connection: sqlite3.Connection, limit: int = 200) -> list[dict[str, Any]]:
        rows = connection.execute("SELECT * FROM operation_history ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return [dict(row) for row in rows]


class SettingsRepository:
    def get(self, connection: sqlite3.Connection, key: str, default: str = "") -> str:
        row = connection.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        return str(row["value"]) if row else default

    def set(self, connection: sqlite3.Connection, key: str, value: str) -> None:
        connection.execute(
            "INSERT INTO settings(key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, value),
        )


def player_as_dict(item: PlayerItem) -> dict[str, Any]:
    return asdict(item)

