from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PlayerItem:
    id: int
    player_name: str
    skill_id: int
    skill_name: str
    status: str
    reserved_for: str | None
    consumed_for: str | None
    note: str | None
    created_at: str
    updated_at: str
    consumed_at: str | None

