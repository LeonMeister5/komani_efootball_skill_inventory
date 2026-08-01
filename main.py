from __future__ import annotations

import logging
from tkinter import messagebox

from app.db.connection import Database
from app.db.migrations import initialize_database
from app.logging_config import configure_logging
from app.paths import AppPaths
from app.services.backup_service import BackupService
from app.services.settings_service import SettingsService


def main() -> None:
    paths = AppPaths.default()
    paths.ensure()
    configure_logging(paths.logs / "app.log")
    database = Database(paths.database)
    try:
        # 已有数据库在迁移前先备份；首次创建没有可备份内容。
        if paths.database.exists() and paths.database.stat().st_size > 0:
            BackupService(database, paths.backups).create_backup(20)
        initialize_database(database)
        settings = SettingsService(database)
        if settings.get_bool("automatic_backup", True):
            BackupService(database, paths.backups).create_backup(settings.get_int("backup_keep_count", 20))
        from app.ui.main_window import MainWindow
        MainWindow(database, paths).mainloop()
    except Exception as exc:
        logging.getLogger(__name__).exception("应用启动失败")
        try:
            messagebox.showerror("启动失败", f"应用无法启动：{exc}\n\n详细信息已写入：{paths.logs / 'app.log'}")
        except Exception:
            pass
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()

