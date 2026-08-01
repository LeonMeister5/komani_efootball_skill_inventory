from __future__ import annotations

import sqlite3

from app.config import DEFAULT_SETTINGS
from app.db.connection import Database

CURRENT_SCHEMA_VERSION = 1


def initialize_database(database: Database) -> None:
    """幂等创建数据库，并依次应用未执行的迁移。"""
    with database.session() as connection:
        connection.execute(
            "CREATE TABLE IF NOT EXISTS schema_version "
            "(version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)"
        )
        row = connection.execute("SELECT COALESCE(MAX(version), 0) AS version FROM schema_version").fetchone()
        version = int(row["version"])
        if version < 1:
            _migration_1(connection)
            connection.execute("INSERT INTO schema_version(version) VALUES (?)", (1,))


def get_schema_version(database: Database) -> int:
    with database.session() as connection:
        row = connection.execute("SELECT COALESCE(MAX(version), 0) AS version FROM schema_version").fetchone()
        return int(row["version"])


def _migration_1(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TABLE skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE COLLATE NOCASE,
            category TEXT,
            enabled INTEGER NOT NULL DEFAULT 1 CHECK(enabled IN (0, 1)),
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE player_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_name TEXT NOT NULL,
            skill_id INTEGER NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('available', 'reserved', 'consumed')),
            reserved_for TEXT,
            consumed_for TEXT,
            note TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            consumed_at TEXT,
            FOREIGN KEY(skill_id) REFERENCES skills(id) ON UPDATE CASCADE
        );
        CREATE TABLE operation_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_item_id INTEGER,
            action TEXT NOT NULL,
            old_data TEXT,
            new_data TEXT,
            detail TEXT,
            created_at TEXT NOT NULL
        );
        CREATE TABLE settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
        CREATE INDEX idx_player_skill_status ON player_items(skill_id, status);
        CREATE INDEX idx_player_name ON player_items(player_name COLLATE NOCASE);
        CREATE INDEX idx_player_status ON player_items(status);
        CREATE INDEX idx_history_player ON operation_history(player_item_id);
        CREATE INDEX idx_history_created ON operation_history(created_at);
        """
    )
    connection.executemany(
        "INSERT OR IGNORE INTO settings(key, value) VALUES (?, ?)", DEFAULT_SETTINGS.items()
    )
