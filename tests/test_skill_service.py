from __future__ import annotations

import pytest

from app.db.connection import Database
from app.services.skill_service import SkillService


def test_skill_name_is_trimmed_and_unique(database: Database) -> None:
    service = SkillService(database)
    created = service.create("  单触传球  ", "传球")
    assert created.name == "单触传球"
    with pytest.raises(ValueError, match="已存在"):
        service.create("单触传球")


def test_skill_name_is_case_insensitive_unique(database: Database) -> None:
    service = SkillService(database)
    service.create("Track Back")
    with pytest.raises(ValueError):
        service.create("track back")


def test_empty_skill_is_rejected(database: Database) -> None:
    with pytest.raises(ValueError, match="不能为空"):
        SkillService(database).create("   ")


def test_disable_skill_keeps_it_available_for_existing_data(database: Database) -> None:
    service = SkillService(database)
    skill = service.create("截球")
    service.update(skill.id, skill.name, None, False)
    assert service.list_skills(enabled_only=True) == []
    assert service.list_skills()[0].enabled is False

