from __future__ import annotations

from app.config import VALID_STATUSES


def required_text(value: str, field_name: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"{field_name}不能为空")
    return cleaned


def validate_status(status: str) -> str:
    if status not in VALID_STATUSES:
        raise ValueError(f"无效状态：{status}")
    return status

