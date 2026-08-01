from __future__ import annotations

from app.db.connection import Database
from app.services.player_service import PlayerService
from app.services.skill_service import SkillService


def setup_services(database: Database) -> tuple[PlayerService, int]:
    skill = SkillService(database).create("直传球")
    return PlayerService(database), skill.id


def test_create_player(database: Database) -> None:
    service, skill_id = setup_services(database)
    item = service.create("球员甲", skill_id)
    assert item.id > 0 and item.skill_id == skill_id and item.status == "available"


def test_duplicate_player_names_are_allowed(database: Database) -> None:
    service, skill_id = setup_services(database)
    first = service.create("同名球员", skill_id)
    second = service.create("同名球员", skill_id)
    assert first.id != second.id


def test_each_player_has_exactly_one_skill(database: Database) -> None:
    service, skill_id = setup_services(database)
    item = service.create("球员", skill_id)
    with database.session() as connection:
        assert connection.execute("SELECT skill_id FROM player_items WHERE id=?", (item.id,)).fetchone()[0] == skill_id


def test_status_transitions_set_and_clear_consumed_at(database: Database) -> None:
    service, skill_id = setup_services(database)
    item = service.create("球员", skill_id)
    consumed = service.change_status(item.id, "consumed", "目标球员")
    assert consumed.consumed_at and consumed.consumed_for == "目标球员"
    available = service.change_status(item.id, "available")
    assert available.consumed_at is None and available.consumed_for is None


def test_available_clears_reserved_for(database: Database) -> None:
    service, skill_id = setup_services(database)
    item = service.create("球员", skill_id, "reserved", "目标")
    assert item.reserved_for == "目标"
    assert service.change_status(item.id, "available").reserved_for is None


def test_search_player_and_skill_case_insensitive(database: Database) -> None:
    service, skill_id = setup_services(database)
    service.create("Alpha Player", skill_id)
    assert len(service.search("alpha")) == 1
    assert len(service.search("直传")) == 1


def test_filter_status(database: Database) -> None:
    service, skill_id = setup_services(database)
    service.create("A", skill_id)
    service.create("B", skill_id, "reserved", "目标")
    assert [item.player_name for item in service.search(status="reserved")] == ["B"]


def test_updates_are_written_to_history(database: Database) -> None:
    service, skill_id = setup_services(database)
    item = service.create("A", skill_id)
    service.change_status(item.id, "reserved", "目标")
    with database.session() as connection:
        actions = [row[0] for row in connection.execute("SELECT action FROM operation_history")]
    assert "player_created" in actions and "status_changed" in actions

