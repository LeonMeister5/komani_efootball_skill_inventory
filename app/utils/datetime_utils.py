from __future__ import annotations

from datetime import datetime


def local_now_iso() -> str:
    """返回带秒精度的本地 ISO 8601 时间。"""
    return datetime.now().astimezone().isoformat(timespec="seconds")

