from __future__ import annotations

from pathlib import Path

import pytest

from app.db.connection import Database
from app.db.migrations import initialize_database


@pytest.fixture
def database(tmp_path: Path) -> Database:
    db = Database(tmp_path / "efootball.db")
    initialize_database(db)
    return db

