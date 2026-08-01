from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

from app.db.connection import Database


class BackupService:
    def __init__(self, database: Database, backup_dir: Path) -> None:
        self.database = database
        self.backup_dir = Path(backup_dir)

    def create_backup(self, keep_count: int = 20) -> Path:
        """通过 SQLite backup API 创建一致性备份。"""
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        target = self.backup_dir / f"efootball_{stamp}.db"
        source = self.database.connect()
        destination = sqlite3.connect(target)
        try:
            source.backup(destination)
        finally:
            destination.close()
            source.close()
        self.cleanup(keep_count)
        return target

    def cleanup(self, keep_count: int) -> None:
        keep_count = max(1, int(keep_count))
        backups = sorted(self.backup_dir.glob("efootball_*.db"), key=lambda path: path.stat().st_mtime, reverse=True)
        for old in backups[keep_count:]:
            old.unlink(missing_ok=True)

