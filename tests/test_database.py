from __future__ import annotations

from app.db.connection import Database
from app.db.migrations import CURRENT_SCHEMA_VERSION, get_schema_version, initialize_database
from app.services.skill_service import SkillService


def test_first_start_creates_all_tables(database: Database) -> None:
    with database.session() as connection:
        names = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"skills", "player_items", "operation_history", "settings", "schema_version"} <= names


def test_repeated_initialization_keeps_data(database: Database) -> None:
    SkillService(database).create("两次触球")
    initialize_database(database)
    assert [skill.name for skill in SkillService(database).list_skills()] == ["两次触球"]


def test_schema_version_is_current(database: Database) -> None:
    assert get_schema_version(database) == CURRENT_SCHEMA_VERSION


def test_foreign_keys_are_enabled(database: Database) -> None:
    with database.session() as connection:
        assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1

