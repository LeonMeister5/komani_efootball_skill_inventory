from __future__ import annotations

APP_NAME = "实况足球技能仓库"
APP_DIR_NAME = "EFootballSkillManager"
DATABASE_NAME = "efootball.db"
WINDOW_SIZE = "1200x750"
VALID_STATUSES = ("available", "reserved", "consumed")
STATUS_LABELS = {"available": "可用", "reserved": "已预留", "consumed": "已消耗"}
STATUS_VALUES = {value: key for key, value in STATUS_LABELS.items()}

DEFAULT_SETTINGS = {
    "skill_cost_gp": "250000",
    "low_stock_threshold": "1",
    "automatic_backup": "true",
    "backup_keep_count": "20",
    "theme": "System",
}

