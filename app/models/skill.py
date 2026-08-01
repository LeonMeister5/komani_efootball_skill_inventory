from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Skill:
    id: int
    name: str
    category: str | None
    enabled: bool
    created_at: str
    updated_at: str

