---
name: db-migration
description: Use when adding or changing a database table/column in this repo — the schema must be updated in two places (db.py init_db() and an Alembic migration) and both must agree, since there is no ORM to autogenerate one from the other.
---

# DB Migration (dual-schema pattern)

This backend has **no ORM**. Schema lives in two independent places that must be
kept in sync by hand:

1. `backend/db.py:init_db()` — idempotent `CREATE TABLE IF NOT EXISTS` / raw DDL,
   run on every app startup. This is what fresh local/dev databases and CI's
   Postgres service actually bootstrap from.
2. `backend/alembic/versions/*.py` — the migration history that upgrades
   **existing** (already-deployed) databases, including production.

Because there's no ORM, `alembic revision --autogenerate` will not produce a
correct migration — write it by hand.

## Steps for any schema change

1. **Update `init_db()` first.** Find the relevant `CREATE TABLE IF NOT EXISTS`
   block in `backend/db.py` and add/modify the column or table there, matching
   the existing style (upper-case SQL keywords, aligned column comments, sane
   `DEFAULT`s so old code paths that don't set the field still work).
2. **Write a new Alembic migration by hand** — do not run `--autogenerate`.
   - Get the correct `down_revision`: `ls backend/alembic/versions/` and check
     which file has no other migration pointing at it (or run
     `cd backend && alembic heads`).
   - Generate a revision id file with `cd backend && alembic revision -m "<description>"`,
     then fill in `upgrade()`/`downgrade()` yourself. Match the style of
     recent migrations (e.g. `backend/alembic/versions/d4e5f6a7b8c9_add_start_date_to_plans.py`):
     `from collections.abc import Sequence`, `import sqlalchemy as sa`,
     `from alembic import op`, plain `op.add_column` / `op.create_table` calls.
   - Every `upgrade()` needs a working `downgrade()` — don't leave it as `pass`
     unless the change is genuinely irreversible.
3. **Keep the two definitions equivalent.** A brand-new database created via
   `init_db()` and an old database upgraded via `alembic upgrade head` must end
   up with the identical schema. Double check types/defaults/nullability match.
4. **Verify against a real database**, not just by reading the diff:
   ```bash
   cd backend
   alembic upgrade head        # applies against DATABASE_URL
   ```
   If a Postgres MCP server is configured, use it to inspect the resulting
   table (`\d <table>` equivalent) and confirm it matches what `init_db()`
   would have produced on a fresh database.
5. Run the test suite that touches the schema: `cd backend && pytest tests/unit tests/integration -q`
   (integration tests run against a real Postgres, per `.github/workflows/backend-tests.yml`).

## Common mistakes this skill exists to prevent

- Adding a column only to `init_db()` and forgetting the Alembic migration (or
  vice versa) — works locally on a fresh DB, breaks production upgrades or CI.
- Using `alembic revision --autogenerate`, which has nothing to diff against
  (no ORM models) and will produce an empty or wrong migration.
- Forgetting `DEFAULT` values in `init_db()` for NOT NULL columns, which breaks
  any code path still inserting rows without the new field.
