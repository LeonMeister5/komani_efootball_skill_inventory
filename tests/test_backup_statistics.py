from __future__ import annotations

from pathlib import Path

from app.db.connection import Database
from app.services.backup_service import BackupService
from app.services.player_service import PlayerService
from app.services.skill_service import SkillService
from app.services.statistics_service import StatisticsService


def test_backup_is_created_and_readable(database: Database, tmp_path: Path) -> None:
    SkillService(database).create("技能")
    target = BackupService(database, tmp_path / "backups").create_backup()
    assert target.exists()
    backup = Database(target)
    assert SkillService(backup).list_skills()[0].name == "技能"


def test_old_backups_are_cleaned(database: Database, tmp_path: Path) -> None:
    service = BackupService(database, tmp_path / "backups")
    for _ in range(4):
        service.create_backup(keep_count=2)
    assert len(list((tmp_path / "backups").glob("*.db"))) == 2


def test_statistics_gp_and_delete_preserves_total_cost(database: Database) -> None:
    skill = SkillService(database).create("技能")
    players = PlayerService(database)
    first = players.create("A", skill.id)
    players.create("B", skill.id, "consumed")
    stats = StatisticsService(database).calculate()
    assert stats.total_created == 2 and stats.total_cost_gp == 500_000 and stats.available_value_gp == 250_000
    players.delete(first.id)
    after = StatisticsService(database).calculate()
    assert after.total_created == 2 and after.total_cost_gp == 500_000 and after.available_value_gp == 0


def test_low_stock_uses_setting(database: Database) -> None:
    SkillService(database).create("低库存技能")
    assert StatisticsService(database).low_stock_skills() == ["低库存技能"]
