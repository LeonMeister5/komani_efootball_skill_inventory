from __future__ import annotations

import csv
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.config import VALID_STATUSES
from app.db.connection import Database
from app.db.repositories import HistoryRepository, PlayerRepository, SkillRepository, player_as_dict
from app.utils.datetime_utils import local_now_iso

EXPORT_FIELDS = ("id", "player_name", "skill_name", "status", "reserved_for", "consumed_for",
                 "note", "created_at", "updated_at", "consumed_at")
REQUIRED_IMPORT_FIELDS = ("player_name", "skill_name", "status")
LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class ImportErrorRow:
    row_number: int
    reason: str
    data: dict[str, str]


@dataclass(frozen=True)
class ImportResult:
    success_count: int
    errors: list[ImportErrorRow]


class ImportExportService:
    def __init__(self, database: Database) -> None:
        self.database = database
        self.players = PlayerRepository()
        self.skills = SkillRepository()
        self.history = HistoryRepository()

    def export_csv(self, target: Path) -> int:
        target = Path(target)
        target.parent.mkdir(parents=True, exist_ok=True)
        with self.database.session() as connection:
            rows = self.players.search(connection)
        with target.open("w", encoding="utf-8-sig", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=EXPORT_FIELDS)
            writer.writeheader()
            for item in rows:
                data = player_as_dict(item)
                writer.writerow({field: data.get(field) or "" for field in EXPORT_FIELDS})
        return len(rows)

    def preview_csv(self, source: Path, limit: int | None = None) -> list[dict[str, str]]:
        with Path(source).open("r", encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            if not reader.fieldnames:
                raise ValueError("CSV 文件没有表头")
            missing = [field for field in REQUIRED_IMPORT_FIELDS if field not in reader.fieldnames]
            if missing:
                raise ValueError("缺少必填列：" + "、".join(missing))
            rows: list[dict[str, str]] = []
            for row in reader:
                rows.append({key: value or "" for key, value in row.items() if key is not None})
                if limit and len(rows) >= limit:
                    break
            return rows

    def import_csv(self, source: Path, auto_create_skills: bool = True) -> ImportResult:
        rows = self.preview_csv(source)
        errors: list[ImportErrorRow] = []
        success = 0
        for index, row in enumerate(rows, start=2):
            try:
                self._import_row(row, auto_create_skills)
                success += 1
            except Exception as exc:
                LOGGER.exception("CSV 第 %s 行导入失败", index)
                errors.append(ImportErrorRow(index, str(exc), row))
        with self.database.session() as connection:
            self.history.add(connection, "csv_import", detail=f"CSV 导入完成：成功 {success}，失败 {len(errors)}")
        return ImportResult(success, errors)

    def _import_row(self, row: dict[str, str], auto_create_skills: bool) -> None:
        player_name = row.get("player_name", "").strip()
        skill_name = row.get("skill_name", "").strip()
        status = row.get("status", "").strip().lower()
        if not player_name:
            raise ValueError("player_name 不能为空")
        if not skill_name:
            raise ValueError("skill_name 不能为空")
        if status not in VALID_STATUSES:
            raise ValueError(f"无效 status：{status}")
        with self.database.session() as connection:
            skill = self.skills.get_by_name(connection, skill_name)
            if not skill:
                if not auto_create_skills:
                    raise ValueError(f"技能不存在：{skill_name}")
                skill = self.skills.create(connection, skill_name, None, local_now_iso())
                self.history.add(connection, "skill_created", new_data=skill.__dict__, detail="CSV 自动创建技能")
            now = local_now_iso()
            data: dict[str, Any] = {
                "player_name": player_name, "skill_id": skill.id, "status": status,
                "reserved_for": row.get("reserved_for", "").strip() or None,
                "consumed_for": row.get("consumed_for", "").strip() or None,
                "note": row.get("note", "").strip() or None,
                "created_at": row.get("created_at", "").strip() or now,
                "updated_at": row.get("updated_at", "").strip() or now,
                "consumed_at": row.get("consumed_at", "").strip() or None,
            }
            if status == "available":
                data["reserved_for"] = data["consumed_for"] = data["consumed_at"] = None
            elif status == "reserved":
                data["consumed_for"] = data["consumed_at"] = None
            else:
                data["reserved_for"] = None
                data["consumed_at"] = data["consumed_at"] or now
            item = self.players.create(connection, data)
            self.history.add(connection, "csv_import_row", item.id, new_data=player_as_dict(item), detail="CSV 导入球员载体")
