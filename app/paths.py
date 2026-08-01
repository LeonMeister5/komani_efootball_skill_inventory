from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from app.config import APP_DIR_NAME, DATABASE_NAME


@dataclass(frozen=True)
class AppPaths:
    root: Path
    database: Path
    backups: Path
    exports: Path
    logs: Path

    @classmethod
    def default(cls) -> "AppPaths":
        local = os.environ.get("LOCALAPPDATA")
        base = Path(local) if local else Path.home() / "AppData" / "Local"
        return cls.from_root(base / APP_DIR_NAME)

    @classmethod
    def from_root(cls, root: Path) -> "AppPaths":
        return cls(root, root / DATABASE_NAME, root / "backups", root / "exports", root / "logs")

    def ensure(self) -> None:
        for directory in (self.root, self.backups, self.exports, self.logs):
            directory.mkdir(parents=True, exist_ok=True)

