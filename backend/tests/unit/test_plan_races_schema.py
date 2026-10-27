"""init_db() and the Alembic migration must create the same plan_races columns (db-migration skill)."""

import re
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[2]
COLUMNS = {
    "id", "plan_id", "race_name", "course_ref", "race_date", "distance_km", "elevation_gain_m", "options_km",
    "effort", "status", "kept_against", "verdict", "verdict_text", "predicted", "result_seconds", "activity_id",
    "debrief", "created_at", "cancelled_at",
}  # fmt: skip


def test_init_db_creates_every_plan_races_column():
    src = (BACKEND / "db.py").read_text()
    block = re.search(r"CREATE TABLE IF NOT EXISTS plan_races \((.*?)\n\s*\)\n", src, re.S)
    assert block, "plan_races missing from init_db"
    found = {line.split()[0] for line in block.group(1).strip().splitlines() if line.strip()}
    assert found == COLUMNS
    assert "ADD COLUMN IF NOT EXISTS plan_race_id" in src


def test_init_db_creates_plan_races_after_activities():
    src = (BACKEND / "db.py").read_text()
    assert src.index("CREATE TABLE IF NOT EXISTS activities") < src.index("CREATE TABLE IF NOT EXISTS plan_races")


def test_alembic_migration_has_the_same_columns():
    src = (BACKEND / "alembic/versions/d1b7a3c9e2f4_add_plan_races.py").read_text()
    assert set(re.findall(r'sa\.Column\("(\w+)"', src)) == COLUMNS | {"plan_race_id"}
    assert 'down_revision: str | Sequence[str] | None = "c5a1d8e3f702"' in src
