from __future__ import annotations

from pathlib import Path

from app.db.connection import Database
from app.services.import_export_service import ImportExportService
from app.services.player_service import PlayerService
from app.services.skill_service import SkillService


def test_import_valid_csv_and_auto_create_skill(database: Database, tmp_path: Path) -> None:
    source = tmp_path / "input.csv"
    source.write_text("player_name,skill_name,status,note\n球员甲,加速,available,备注\n", encoding="utf-8-sig")
    result = ImportExportService(database).import_csv(source)
    assert result.success_count == 1 and not result.errors
    assert SkillService(database).list_skills()[0].name == "加速"


def test_bad_import_row_does_not_rollback_good_rows(database: Database, tmp_path: Path) -> None:
    source = tmp_path / "input.csv"
    source.write_text("player_name,skill_name,status\n正确,技能A,available\n错误,技能B,bad\n", encoding="utf-8")
    result = ImportExportService(database).import_csv(source)
    assert result.success_count == 1 and len(result.errors) == 1 and result.errors[0].row_number == 3
    assert len(PlayerService(database).search()) == 1


def test_import_requires_headers(database: Database, tmp_path: Path) -> None:
    source = tmp_path / "input.csv"
    source.write_text("name,status\nA,available\n", encoding="utf-8")
    try:
        ImportExportService(database).preview_csv(source)
    except ValueError as exc:
        assert "缺少必填列" in str(exc)
    else:
        raise AssertionError("missing columns should fail")


def test_export_has_utf8_bom(database: Database, tmp_path: Path) -> None:
    skill = SkillService(database).create("单触传球")
    PlayerService(database).create("中文球员", skill.id)
    target = tmp_path / "output.csv"
    assert ImportExportService(database).export_csv(target) == 1
    assert target.read_bytes().startswith(b"\xef\xbb\xbf")
    assert "中文球员" in target.read_text(encoding="utf-8-sig")

