"""
Database layer — SQLAlchemy Core with PostgreSQL.
All raw SQL uses %s-style placeholders via psycopg2 through SQLAlchemy.
"""

import datetime
import json
import uuid
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.pool import QueuePool

from config import settings

# ─── Engine ─────────────────────────────────────────────────────────────────

engine = create_engine(
    settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    echo=False,
)


def get_conn():
    """Context manager: yields a raw connection from the pool."""
    return engine.connect()


# ─── Schema Init ─────────────────────────────────────────────────────────────


def init_db():
    """Create all tables if they don't exist. Safe to call on every startup."""
    with engine.connect() as conn:
        conn.execute(
            text("""
        CREATE TABLE IF NOT EXISTS users (
            id                      SERIAL PRIMARY KEY,
            email                   TEXT UNIQUE NOT NULL,
            name                    TEXT,
            role                    TEXT NOT NULL DEFAULT 'user',
            provider                TEXT NOT NULL DEFAULT 'email',
            provider_user_id        TEXT,
            password_hash           TEXT,
            -- physiology
            dob                     DATE,
            age                     INTEGER DEFAULT 30,
            current_weekly_km       REAL DEFAULT 30.0,
            max_hr                  INTEGER DEFAULT 185,
            resting_hr              INTEGER DEFAULT 60,
            aet_hr                  INTEGER DEFAULT 135,
            ant_hr                  INTEGER DEFAULT 165,
            zone2_pace_min          TEXT DEFAULT '6:30',
            zone2_pace_max          TEXT DEFAULT '5:45',
            -- onboarding
            onboarding_complete     BOOLEAN DEFAULT FALSE,
            goal_type               TEXT,
            injury_history          TEXT,
            preferred_run_days      TEXT,
            long_run_day            TEXT,
            days_per_week           INTEGER DEFAULT 4,
            has_gym_access          BOOLEAN DEFAULT FALSE,
            use_treadmill           INTEGER DEFAULT 0,
            -- api keys
            gemini_api_key          TEXT,
            created_at              TIMESTAMPTZ DEFAULT NOW()
        )
        """)
        )

        conn.execute(
            text("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_token   TEXT PRIMARY KEY,
            user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            expires_at      TIMESTAMPTZ NOT NULL
        )
        """)
        )

        conn.execute(
            text("""
        CREATE TABLE IF NOT EXISTS sources (
            id          SERIAL PRIMARY KEY,
            title       TEXT NOT NULL,
            type        TEXT NOT NULL,
            content     TEXT NOT NULL,
            url_path    TEXT,
            summary     TEXT,
            created_at  TIMESTAMPTZ DEFAULT NOW()
        )
        """)
        )

        conn.execute(
            text("""
        CREATE TABLE IF NOT EXISTS plans (
            id                      SERIAL PRIMARY KEY,
            user_id                 INTEGER REFERENCES users(id) ON DELETE CASCADE,
            race_name               TEXT NOT NULL,
            race_date               TEXT NOT NULL,
            goal_type               TEXT NOT NULL,
            target_time_hours       REAL,
            total_weeks             INTEGER NOT NULL,
            current_week            INTEGER DEFAULT 1,
            course_distance_km      REAL,
            course_elevation_gain_m REAL,
            created_at              TIMESTAMPTZ DEFAULT NOW()
        )
        """)
        )

        conn.execute(
            text("""
        CREATE TABLE IF NOT EXISTS workouts (
            id                  SERIAL PRIMARY KEY,
            plan_id             INTEGER NOT NULL REFERENCES plans(id) ON DELETE CASCADE,
            week_number         INTEGER NOT NULL,
            day_of_week         TEXT NOT NULL,
            phase               TEXT NOT NULL,
            title               TEXT NOT NULL,
            type                TEXT NOT NULL,
            duration_minutes    REAL NOT NULL,
            distance_km         REAL,
            target_zone         TEXT NOT NULL,
            target_hr_range     TEXT,
            target_pace         TEXT,
            treadmill_incline   REAL DEFAULT 0.0,
            treadmill_speed     REAL DEFAULT 0.0,
            elevation_gain_m    REAL DEFAULT 0.0,
            grade_percent       REAL DEFAULT 0.0,
            description         TEXT,
            fueling_tip         TEXT,
            is_completed        INTEGER DEFAULT 0
        )
        """)
        )

        conn.execute(
            text("""
        CREATE TABLE IF NOT EXISTS nutrition_products (
            id              SERIAL PRIMARY KEY,
            brand           TEXT NOT NULL,
            name            TEXT NOT NULL,
            type            TEXT NOT NULL,
            carbs_grams     REAL NOT NULL,
            sodium_mg       REAL NOT NULL,
            caffeine_mg     REAL DEFAULT 0.0,
            water_ratio_ml  REAL DEFAULT 250.0
        )
        """)
        )

        conn.execute(
            text("""
        CREATE TABLE IF NOT EXISTS analytics_events (
            id              SERIAL PRIMARY KEY,
            user_id         INTEGER REFERENCES users(id) ON DELETE SET NULL,
            event_name      TEXT NOT NULL,
            properties      JSONB DEFAULT '{}'::jsonb,
            timestamp       TIMESTAMPTZ DEFAULT NOW(),
            session_id      TEXT,
            url             TEXT,
            user_agent      TEXT
        )
        """)
        )

        conn.execute(
            text("""
        CREATE TABLE IF NOT EXISTS shoes (
            id              SERIAL PRIMARY KEY,
            brand           TEXT NOT NULL,
            model           TEXT NOT NULL,
            surface         TEXT NOT NULL,
            cushioning      TEXT NOT NULL,
            drop_mm         INTEGER DEFAULT 6,
            plate           TEXT DEFAULT 'none',
            width           TEXT DEFAULT 'normal',
            review_summary  TEXT
        )
        """)
        )

        conn.execute(
            text("""
        CREATE TABLE IF NOT EXISTS workout_types (
            id              SERIAL PRIMARY KEY,
            type_key        TEXT NOT NULL,
            display_name    TEXT NOT NULL,
            zone            TEXT NOT NULL,
            color           TEXT NOT NULL,
            overview        TEXT NOT NULL,
            execution       TEXT NOT NULL,
            benefit         TEXT NOT NULL,
            warning         TEXT NOT NULL,
            lang            TEXT NOT NULL DEFAULT 'en',
            created_at      TIMESTAMPTZ DEFAULT NOW(),
            UNIQUE (type_key, lang)
        )
        """)
        )

        conn.execute(
            text("""
        CREATE TABLE IF NOT EXISTS knowledge_cards (
            id              SERIAL PRIMARY KEY,
            chapter_title   TEXT NOT NULL,
            summary         TEXT NOT NULL,
            key_points      TEXT NOT NULL,
            tags            TEXT NOT NULL,
            topic           TEXT NOT NULL,
            source_label    TEXT DEFAULT 'Uphill Athlete Podcasts',
            lang            TEXT DEFAULT 'en',
            created_at      TIMESTAMPTZ DEFAULT NOW()
        )
        """)
        )

        conn.commit()

        try:
            conn.execute(text("ALTER TABLE knowledge_cards ADD COLUMN lang TEXT DEFAULT 'en'"))
            conn.commit()
            print("Added 'lang' column to knowledge_cards.")
        except Exception:
            conn.rollback()

        # block_reviews: one row per 2-week block check-in before next-block generation
        conn.execute(
            text("""
        CREATE TABLE IF NOT EXISTS block_reviews (
            id           SERIAL PRIMARY KEY,
            plan_id      INTEGER NOT NULL REFERENCES plans(id) ON DELETE CASCADE,
            block_number INTEGER NOT NULL,
            overall_rpe  INTEGER,
            notes        TEXT,
            created_at   TIMESTAMPTZ DEFAULT NOW()
        )
        """)
        )
        conn.commit()

        for col_sql in [
            "ALTER TABLE workouts ADD COLUMN IF NOT EXISTS rpe INTEGER",
            "ALTER TABLE workouts ADD COLUMN IF NOT EXISTS notes TEXT",
            "ALTER TABLE workouts ADD COLUMN IF NOT EXISTS session_slot TEXT DEFAULT 'main'",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS double_session_days TEXT",
            "ALTER TABLE plans ADD COLUMN IF NOT EXISTS preferred_run_days TEXT",
            "ALTER TABLE plans ADD COLUMN IF NOT EXISTS long_run_day TEXT",
            "ALTER TABLE plans ADD COLUMN IF NOT EXISTS days_per_week INTEGER DEFAULT 4",
            "ALTER TABLE plans ADD COLUMN IF NOT EXISTS double_session_days TEXT",
            "ALTER TABLE plans ADD COLUMN IF NOT EXISTS start_date TEXT",
        ]:
            try:
                conn.execute(text(col_sql))
                conn.commit()
            except Exception:
                conn.rollback()

    seed_data()
    print("PostgreSQL database tables initialized successfully.")


def seed_data():
    """Seed default users, nutrition, shoes, and knowledge cards if tables are empty."""
    with engine.connect() as conn:
        # Users
        count = conn.execute(text("SELECT COUNT(*) FROM users")).scalar()
        if count == 0:
            conn.execute(
                text("""
                INSERT INTO users (email, name, role, provider, provider_user_id, age, current_weekly_km,
                                   max_hr, resting_hr, aet_hr, ant_hr, use_treadmill, onboarding_complete)
                VALUES
                  ('admin@uphill.ai', 'Uphill Admin', 'admin', 'mock', 'mock-admin-id',
                   35, 50.0, 185, 50, 140, 168, 1, TRUE),
                  ('athlete@uphill.ai', 'Uphill Athlete', 'user', 'mock', 'mock-athlete-id',
                   30, 30.0, 190, 60, 130, 165, 0, TRUE)
            """)
            )
            print("Seeded default users.")

        # Nutrition
        count = conn.execute(text("SELECT COUNT(*) FROM nutrition_products")).scalar()
        if count == 0:
            conn.execute(
                text("""
                INSERT INTO nutrition_products (brand, name, type, carbs_grams, sodium_mg, caffeine_mg, water_ratio_ml)
                VALUES
                  ('Maurten', 'Gel 100', 'gel', 25.0, 20.0, 0.0, 0.0),
                  ('Maurten', 'Gel 100 Caf 100', 'gel', 25.0, 20.0, 100.0, 0.0),
                  ('Tailwind', 'Endurance Fuel (1 scoop)', 'drink_mix', 25.0, 310.0, 0.0, 300.0),
                  ('GU', 'Energy Gel', 'gel', 22.0, 60.0, 20.0, 0.0),
                  ('SiS', 'Beta Fuel Gel', 'gel', 40.0, 30.0, 0.0, 0.0),
                  ('Skratch', 'Hydration Mix (1 scoop)', 'drink_mix', 20.0, 380.0, 0.0, 350.0),
                  ('Clif Bar', 'Shot Energy Gel', 'gel', 24.0, 90.0, 0.0, 0.0)
            """)
            )
            print("Seeded nutrition products.")

        # Shoes
        count = conn.execute(text("SELECT COUNT(*) FROM shoes")).scalar()
        if count == 0:
            conn.execute(
                text("""
                INSERT INTO shoes (brand, model, surface, cushioning, drop_mm, plate, width, review_summary)
                VALUES
                  ('Hoka', 'Speedgoat 6', 'trail', 'plush', 4, 'none', 'normal', 'Cushioned trail shoe for technical vertical loops. Deep lugs.'),
                  ('Hoka', 'Speedgoat 6 Wide', 'trail', 'plush', 4, 'none', 'wide', 'Cushioned wide trail shoe for technical vertical loops.'),
                  ('Saucony', 'Peregrine 14', 'trail', 'balanced', 4, 'none', 'normal', 'Lightweight, responsive trail shoe. Aggressive grip.'),
                  ('Brooks', 'Cascadia 18', 'trail', 'balanced', 8, 'none', 'normal', 'Protective, stable, and durable trail shoe for long mountain runs.'),
                  ('Nike', 'Pegasus Trail 5', 'trail', 'balanced', 9, 'none', 'normal', 'Road-to-trail hybrid shoe, comfortable and versatile.'),
                  ('Nike', 'Alphafly 3', 'road', 'plush', 8, 'carbon', 'normal', 'Elite carbon-plated road marathon racer. Ultra responsive.'),
                  ('Asics', 'Superblast 2', 'road', 'plush', 8, 'none', 'normal', 'Highly cushioned non-plated trainer for marathon recovery and long tempos.'),
                  ('Saucony', 'Endorphin Speed 4', 'road', 'balanced', 8, 'nylon', 'normal', 'Nylon-plated tempo and race shoe. Responsive cushioning.')
            """)
            )
            print("Seeded shoes.")

        conn.commit()

    # Seed knowledge cards if table is empty for the respective language
    import os

    # Seed EN cards
    backup_path_en = os.path.join(os.path.dirname(os.path.abspath(__file__)), "knowledge_cards_backup.json")
    if os.path.exists(backup_path_en):
        with engine.connect() as conn:
            en_count = conn.execute(text("SELECT COUNT(*) FROM knowledge_cards WHERE lang = 'en'")).scalar()
        if en_count == 0:
            try:
                with open(backup_path_en, encoding="utf-8") as f:
                    cards = json.load(f)
                saved = save_knowledge_cards(cards, lang="en")
                print(f"Seeded {saved} English knowledge cards from default backup file.")
            except Exception as e:
                print(f"Error seeding English knowledge cards: {e}")

    # Seed VI cards
    backup_path_vi = os.path.join(os.path.dirname(os.path.abspath(__file__)), "knowledge_cards_backup_vi.json")
    if os.path.exists(backup_path_vi):
        with engine.connect() as conn:
            vi_count = conn.execute(text("SELECT COUNT(*) FROM knowledge_cards WHERE lang = 'vi'")).scalar()
        if vi_count == 0:
            try:
                with open(backup_path_vi, encoding="utf-8") as f:
                    cards = json.load(f)
                saved = save_knowledge_cards(cards, lang="vi")
                print(f"Seeded {saved} Vietnamese knowledge cards from default backup file.")
            except Exception as e:
                print(f"Error seeding Vietnamese knowledge cards: {e}")


# ─── Helper ──────────────────────────────────────────────────────────────────


def _row_to_dict(row) -> dict[str, Any]:
    return dict(row._mapping)


# ─── RAG / Sources ───────────────────────────────────────────────────────────


def add_source(title: str, type_str: str, content: str, url_path: str | None = None, summary: str | None = None) -> int:
    with engine.connect() as conn:
        result = conn.execute(
            text(
                "INSERT INTO sources (title, type, content, url_path, summary) "
                "VALUES (:title, :type, :content, :url_path, :summary) RETURNING id"
            ),
            {"title": title, "type": type_str, "content": content, "url_path": url_path, "summary": summary},
        )
        conn.commit()
        return result.scalar()


def list_sources() -> list[dict[str, Any]]:
    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT id, title, type, url_path, summary, created_at " "FROM sources ORDER BY created_at DESC")
        ).fetchall()
    return [_row_to_dict(r) for r in rows]


def get_all_grounding_content() -> list[dict[str, Any]]:
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT title, type, content FROM sources")).fetchall()
    return [_row_to_dict(r) for r in rows]


def delete_source(source_id: int) -> bool:
    with engine.connect() as conn:
        result = conn.execute(text("DELETE FROM sources WHERE id = :id"), {"id": source_id})
        conn.commit()
    return result.rowcount > 0


# ─── Training Plans ──────────────────────────────────────────────────────────


def create_plan(
    user_id: int,
    race_name: str,
    race_date: str,
    goal_type: str,
    target_time_hours: float | None,
    total_weeks: int,
    course_distance_km: float | None = None,
    course_elevation_gain_m: float | None = None,
    preferred_run_days: list | None = None,
    long_run_day: str | None = None,
    days_per_week: int = 4,
    double_session_days: list | None = None,
    start_date: str | None = None,
) -> int:
    with engine.connect() as conn:
        result = conn.execute(
            text("""
            INSERT INTO plans (user_id, race_name, race_date, goal_type,
                               target_time_hours, total_weeks, course_distance_km,
                               course_elevation_gain_m, preferred_run_days, long_run_day,
                               days_per_week, double_session_days, start_date)
            VALUES (:user_id, :race_name, :race_date, :goal_type,
                    :tth, :total_weeks, :dist_km, :elev_m, :preferred_run_days,
                    :long_run_day, :days_per_week, :double_session_days, :start_date)
            RETURNING id
        """),
            {
                "user_id": user_id,
                "race_name": race_name,
                "race_date": race_date,
                "goal_type": goal_type,
                "tth": target_time_hours,
                "total_weeks": total_weeks,
                "dist_km": course_distance_km,
                "elev_m": course_elevation_gain_m,
                "preferred_run_days": json.dumps(preferred_run_days or []),
                "long_run_day": long_run_day,
                "days_per_week": days_per_week or 4,
                "double_session_days": json.dumps(double_session_days or []),
                "start_date": start_date,
            },
        )
        conn.commit()
        return result.scalar()


def get_recent_plans(user_id: int, limit: int = 3) -> list[dict[str, Any]]:
    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT * FROM plans WHERE user_id = :uid " "ORDER BY created_at DESC, id DESC LIMIT :lim"),
            {"uid": user_id, "lim": limit},
        ).fetchall()
    return [_row_to_dict(r) for r in rows]


def save_workouts(plan_id: int, workouts: list[dict[str, Any]]):
    if not workouts:
        return
    week_numbers = [wo["week_number"] for wo in workouts]
    week_start, week_end = min(week_numbers), max(week_numbers)
    with engine.connect() as conn:
        # Clear any existing rows in this block's week range first, so retries/duplicate
        # generation calls overwrite instead of stacking duplicate workouts on top.
        conn.execute(
            text("""
                DELETE FROM workouts
                WHERE plan_id = :plan_id AND week_number BETWEEN :week_start AND :week_end
            """),
            {"plan_id": plan_id, "week_start": week_start, "week_end": week_end},
        )
        for wo in workouts:
            conn.execute(
                text("""
                INSERT INTO workouts (plan_id, week_number, day_of_week, phase, title, type,
                    duration_minutes, distance_km, target_zone, target_hr_range, target_pace,
                    treadmill_incline, treadmill_speed, elevation_gain_m, grade_percent,
                    description, fueling_tip, session_slot)
                VALUES (:plan_id, :week_number, :day_of_week, :phase, :title, :type,
                    :duration_minutes, :distance_km, :target_zone, :target_hr_range, :target_pace,
                    :treadmill_incline, :treadmill_speed, :elevation_gain_m, :grade_percent,
                    :description, :fueling_tip, :session_slot)
            """),
                {
                    "plan_id": plan_id,
                    "week_number": wo["week_number"],
                    "day_of_week": wo["day_of_week"],
                    "phase": wo["phase"],
                    "title": wo["title"],
                    "type": wo["type"],
                    "duration_minutes": wo["duration_minutes"],
                    "distance_km": wo.get("distance_km"),
                    "target_zone": wo["target_zone"],
                    "target_hr_range": wo.get("target_hr_range"),
                    "target_pace": wo.get("target_pace"),
                    "treadmill_incline": wo.get("treadmill_incline", 0.0),
                    "treadmill_speed": wo.get("treadmill_speed", 0.0),
                    "elevation_gain_m": wo.get("elevation_gain_m", 0.0),
                    "grade_percent": wo.get("grade_percent", 0.0),
                    "description": wo.get("description"),
                    "fueling_tip": wo.get("fueling_tip"),
                    "session_slot": wo.get("session_slot", "main"),
                },
            )
        conn.commit()


def get_active_plan(user_id: int) -> dict[str, Any] | None:
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT * FROM plans WHERE user_id = :uid " "ORDER BY created_at DESC, id DESC LIMIT 1"),
            {"uid": user_id},
        ).fetchone()
    return _row_to_dict(row) if row else None


def set_plan_active(user_id: int, plan_id: int) -> bool:
    with engine.connect() as conn:
        result = conn.execute(
            text("UPDATE plans SET created_at = NOW() WHERE id = :pid AND user_id = :uid"),
            {"pid": plan_id, "uid": user_id},
        )
        conn.commit()
    return result.rowcount > 0


def get_plan_workouts(plan_id: int) -> list[dict[str, Any]]:
    with engine.connect() as conn:
        rows = conn.execute(
            text("""
            SELECT * FROM workouts WHERE plan_id = :plan_id
            ORDER BY week_number ASC,
            CASE day_of_week
              WHEN 'Monday'    THEN 1
              WHEN 'Tuesday'   THEN 2
              WHEN 'Wednesday' THEN 3
              WHEN 'Thursday'  THEN 4
              WHEN 'Friday'    THEN 5
              WHEN 'Saturday'  THEN 6
              WHEN 'Sunday'    THEN 7
            END ASC
        """),
            {"plan_id": plan_id},
        ).fetchall()
    return [_row_to_dict(r) for r in rows]


def update_workout_log(
    workout_id: int, is_completed: int | None = None, rpe: int | None = None, notes: str | None = None
) -> bool:
    """Update is_completed, rpe, and/or notes for a workout."""
    with engine.connect() as conn:
        row = conn.execute(text("SELECT id FROM workouts WHERE id = :id"), {"id": workout_id}).fetchone()
        if not row:
            return False
        if is_completed is not None:
            conn.execute(
                text("UPDATE workouts SET is_completed = :v WHERE id = :id"), {"v": is_completed, "id": workout_id}
            )
        if rpe is not None:
            conn.execute(text("UPDATE workouts SET rpe = :v WHERE id = :id"), {"v": rpe, "id": workout_id})
        if notes is not None:
            conn.execute(text("UPDATE workouts SET notes = :v WHERE id = :id"), {"v": notes, "id": workout_id})
        conn.commit()
    return True


def swap_workouts(plan_id: int, week_number: int, day_1: str, day_2: str) -> bool:
    with engine.connect() as conn:
        wo1 = conn.execute(
            text("SELECT * FROM workouts WHERE plan_id=:pid AND week_number=:wn AND day_of_week=:day"),
            {"pid": plan_id, "wn": week_number, "day": day_1},
        ).fetchone()
        wo2 = conn.execute(
            text("SELECT * FROM workouts WHERE plan_id=:pid AND week_number=:wn AND day_of_week=:day"),
            {"pid": plan_id, "wn": week_number, "day": day_2},
        ).fetchone()

        if not wo1 or not wo2:
            return False

        swap_cols = [
            "phase",
            "title",
            "type",
            "duration_minutes",
            "distance_km",
            "target_zone",
            "target_hr_range",
            "target_pace",
            "treadmill_incline",
            "treadmill_speed",
            "description",
            "fueling_tip",
            "is_completed",
            "session_slot",
        ]
        d1, d2 = _row_to_dict(wo1), _row_to_dict(wo2)

        set1 = ", ".join([f"{c} = :{c}_v" for c in swap_cols])
        params1 = {f"{c}_v": d2[c] for c in swap_cols}
        params1["id"] = d1["id"]
        conn.execute(text(f"UPDATE workouts SET {set1} WHERE id = :id"), params1)

        set2 = ", ".join([f"{c} = :{c}_v" for c in swap_cols])
        params2 = {f"{c}_v": d1[c] for c in swap_cols}
        params2["id"] = d2["id"]
        conn.execute(text(f"UPDATE workouts SET {set2} WHERE id = :id"), params2)

        conn.commit()
    return True


# ─── Block Reviews ────────────────────────────────────────────────────────────


def save_block_review(plan_id: int, block_number: int, overall_rpe: int | None, notes: str | None) -> dict[str, Any]:
    with engine.connect() as conn:
        row = conn.execute(
            text("""
            INSERT INTO block_reviews (plan_id, block_number, overall_rpe, notes)
            VALUES (:plan_id, :block_number, :overall_rpe, :notes)
            RETURNING *
            """),
            {"plan_id": plan_id, "block_number": block_number, "overall_rpe": overall_rpe, "notes": notes},
        ).fetchone()
        conn.commit()
    return _row_to_dict(row)


def get_block_reviews(plan_id: int) -> list[dict[str, Any]]:
    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT * FROM block_reviews WHERE plan_id = :plan_id ORDER BY block_number ASC"),
            {"plan_id": plan_id},
        ).fetchall()
    return [_row_to_dict(r) for r in rows]


def get_block_completion(plan_id: int, block_number: int) -> dict[str, Any]:
    """Returns total and completed hours for a 2-week block (block 1 = weeks 1-2, etc.)."""
    week_start = (block_number - 1) * 2 + 1
    week_end = block_number * 2
    with engine.connect() as conn:
        rows = conn.execute(
            text("""
            SELECT is_completed, duration_minutes
            FROM workouts
            WHERE plan_id = :plan_id
              AND week_number BETWEEN :ws AND :we
              AND type != 'Rest'
              AND duration_minutes > 0
            """),
            {"plan_id": plan_id, "ws": week_start, "we": week_end},
        ).fetchall()
    total_minutes = sum(r[1] or 0 for r in rows)
    completed_minutes = sum(r[1] or 0 for r in rows if r[0] == 1)
    pct = round(completed_minutes / total_minutes * 100) if total_minutes > 0 else 0
    return {
        "block_number": block_number,
        "week_start": week_start,
        "week_end": week_end,
        "total_minutes": total_minutes,
        "completed_minutes": completed_minutes,
        "completion_pct": pct,
        "unlocked": pct >= 70,
    }


def get_max_generated_week(plan_id: int) -> int:
    """Returns the highest week_number that has been generated for this plan."""
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT COALESCE(MAX(week_number), 0) FROM workouts WHERE plan_id = :plan_id"),
            {"plan_id": plan_id},
        ).scalar()
    return result or 0


# ─── Catalog ─────────────────────────────────────────────────────────────────


def query_nutrition_catalog() -> list[dict[str, Any]]:
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT * FROM nutrition_products ORDER BY brand, name")).fetchall()
    return [_row_to_dict(r) for r in rows]


def query_shoes_catalog(surface: str, cushioning: str, width: str) -> list[dict[str, Any]]:
    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT * FROM shoes WHERE surface=:s AND cushioning=:c AND width=:w"),
            {"s": surface, "c": cushioning, "w": width},
        ).fetchall()
        if not rows:
            rows = conn.execute(text("SELECT * FROM shoes WHERE surface=:s LIMIT 3"), {"s": surface}).fetchall()
    return [_row_to_dict(r) for r in rows]


# ─── Auth / Users ─────────────────────────────────────────────────────────────


def create_or_get_user(
    email: str, name: str, provider: str, provider_user_id: str, role: str = "user", onboarding_complete: bool = False
) -> dict[str, Any]:
    email = email.lower().strip()
    with engine.connect() as conn:
        row = conn.execute(text("SELECT * FROM users WHERE email = :e"), {"e": email}).fetchone()
        if row:
            return _row_to_dict(row)
        conn.execute(
            text("""
            INSERT INTO users (email, name, role, provider, provider_user_id, onboarding_complete)
            VALUES (:e, :n, :r, :p, :pid, :oc)
        """),
            {"e": email, "n": name, "r": role, "p": provider, "pid": provider_user_id, "oc": onboarding_complete},
        )
        conn.commit()
        row = conn.execute(text("SELECT * FROM users WHERE email = :e"), {"e": email}).fetchone()
        return _row_to_dict(row)


def create_user_with_password(email: str, name: str, password_hash: str) -> dict[str, Any]:
    email = email.lower().strip()
    with engine.connect() as conn:
        conn.execute(
            text("""
            INSERT INTO users (email, name, role, provider, provider_user_id, password_hash, onboarding_complete)
            VALUES (:e, :n, 'user', 'email', :e, :ph, FALSE)
        """),
            {"e": email, "n": name, "ph": password_hash},
        )
        conn.commit()
        row = conn.execute(text("SELECT * FROM users WHERE email = :e"), {"e": email}).fetchone()
        return _row_to_dict(row)


def get_user_by_id(user_id: int) -> dict[str, Any] | None:
    with engine.connect() as conn:
        row = conn.execute(text("SELECT * FROM users WHERE id = :id"), {"id": user_id}).fetchone()
    return _row_to_dict(row) if row else None


def get_user_by_email(email: str) -> dict[str, Any] | None:
    with engine.connect() as conn:
        row = conn.execute(text("SELECT * FROM users WHERE email = :e"), {"e": email.lower().strip()}).fetchone()
    return _row_to_dict(row) if row else None


def set_user_password(user_id: int, password_hash: str) -> bool:
    with engine.connect() as conn:
        result = conn.execute(
            text("UPDATE users SET password_hash = :ph WHERE id = :id"), {"ph": password_hash, "id": user_id}
        )
        conn.commit()
    return result.rowcount > 0


def update_user_profile(user_id: int, profile_data: dict[str, Any]) -> bool:
    with engine.connect() as conn:
        result = conn.execute(
            text("""
            UPDATE users SET
                age = :age, current_weekly_km = :ckm, max_hr = :max_hr,
                resting_hr = :rhr, aet_hr = :aet, ant_hr = :ant,
                use_treadmill = :ut, gemini_api_key = :gak,
                zone2_pace_min = :z2min, zone2_pace_max = :z2max
            WHERE id = :id
        """),
            {
                "age": int(profile_data.get("age", 30)),
                "ckm": float(profile_data.get("current_weekly_km", 30.0)),
                "max_hr": int(profile_data.get("max_hr", 185)),
                "rhr": int(profile_data.get("resting_hr", 60)),
                "aet": int(profile_data.get("aet_hr", 135)),
                "ant": int(profile_data.get("ant_hr", 165)),
                "ut": 1 if profile_data.get("use_treadmill") else 0,
                "gak": profile_data.get("gemini_api_key"),
                "z2min": profile_data.get("zone2_pace_min", "6:30"),
                "z2max": profile_data.get("zone2_pace_max", "5:45"),
                "id": user_id,
            },
        )
        conn.commit()
    return result.rowcount > 0


def update_onboarding_profile(user_id: int, data: dict[str, Any]) -> bool:
    """Save all onboarding answers to the user profile."""
    with engine.connect() as conn:
        result = conn.execute(
            text("""
            UPDATE users SET
                dob = :dob,
                age = :age,
                goal_type = :goal_type,
                injury_history = :injury_history,
                preferred_run_days = :preferred_run_days,
                long_run_day = :long_run_day,
                days_per_week = :days_per_week,
                has_gym_access = :has_gym_access,
                use_treadmill = :use_treadmill,
                current_weekly_km = :current_weekly_km,
                max_hr = :max_hr,
                resting_hr = :resting_hr,
                aet_hr = :aet_hr,
                ant_hr = :ant_hr,
                zone2_pace_min = :zone2_pace_min,
                zone2_pace_max = :zone2_pace_max,
                double_session_days = :double_session_days
            WHERE id = :id
        """),
            {
                "dob": data.get("dob"),
                "age": data.get("age", 30),
                "goal_type": data.get("goal_type"),
                "injury_history": data.get("injury_history"),
                "preferred_run_days": json.dumps(data.get("preferred_run_days", [])),
                "long_run_day": data.get("long_run_day"),
                "days_per_week": data.get("days_per_week", 4),
                "has_gym_access": data.get("has_gym_access", False),
                "use_treadmill": 1 if data.get("has_gym_access") else 0,
                "current_weekly_km": float(data.get("current_weekly_km", 30.0)),
                "max_hr": int(data.get("max_hr", 185)),
                "resting_hr": int(data.get("resting_hr", 60)),
                "aet_hr": int(data.get("aet_hr", 135)),
                "ant_hr": int(data.get("ant_hr", 165)),
                "zone2_pace_min": data.get("zone2_pace_min", "6:30"),
                "zone2_pace_max": data.get("zone2_pace_max", "5:45"),
                "double_session_days": json.dumps(data.get("double_session_days", [])),
                "id": user_id,
            },
        )
        conn.commit()
    return result.rowcount > 0


def mark_onboarding_complete(user_id: int) -> bool:
    with engine.connect() as conn:
        result = conn.execute(text("UPDATE users SET onboarding_complete = TRUE WHERE id = :id"), {"id": user_id})
        conn.commit()
    return result.rowcount > 0


# ─── Sessions (JWT-based, stored for revocation) ─────────────────────────────


def create_session(user_id: int, duration_days: int = 7) -> dict[str, Any]:
    """Creates a DB session record alongside JWT. Returns JWT token."""
    import jwt

    from config import settings

    now = datetime.datetime.now(datetime.UTC)
    expires_at = now + datetime.timedelta(days=duration_days)

    payload = {
        "sub": str(user_id),
        "exp": expires_at,
        "iat": now,
        "jti": str(uuid.uuid4()),
    }
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

    with engine.connect() as conn:
        conn.execute(
            text("""
            INSERT INTO sessions (session_token, user_id, expires_at)
            VALUES (:tok, :uid, :exp)
        """),
            {"tok": token, "uid": user_id, "exp": expires_at},
        )
        conn.commit()

    return {
        "session_token": token,
        "user_id": user_id,
        "expires_at": expires_at.isoformat(),
    }


def verify_session(session_token: str) -> dict[str, Any] | None:
    """Verifies JWT signature + expiry, then loads user from DB."""
    import jwt

    from config import settings

    try:
        payload = jwt.decode(session_token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        user_id = int(payload["sub"])
    except Exception:
        return None

    with engine.connect() as conn:
        # Confirm session still exists (allows server-side revocation)
        row = conn.execute(
            text("SELECT * FROM sessions WHERE session_token = :tok AND expires_at > NOW()"), {"tok": session_token}
        ).fetchone()
        if not row:
            return None
        user_row = conn.execute(text("SELECT * FROM users WHERE id = :id"), {"id": user_id}).fetchone()
    return _row_to_dict(user_row) if user_row else None


def delete_session(session_token: str) -> bool:
    with engine.connect() as conn:
        result = conn.execute(text("DELETE FROM sessions WHERE session_token = :tok"), {"tok": session_token})
        conn.commit()
    return result.rowcount > 0


# ─── Knowledge Cards ─────────────────────────────────────────────────────────


def save_knowledge_cards(cards: list[dict[str, Any]], lang: str = "en") -> int:
    count = 0
    with engine.connect() as conn:
        for card in cards:
            try:
                conn.execute(
                    text("""
                    INSERT INTO knowledge_cards (chapter_title, summary, key_points, tags, topic, source_label, lang)
                    VALUES (:ct, :sm, :kp, :tg, :tp, :sl, :lang)
                """),
                    {
                        "ct": card.get("chapter_title", ""),
                        "sm": card.get("summary", ""),
                        "kp": json.dumps(card.get("key_points", []), ensure_ascii=False),
                        "tg": json.dumps(card.get("tags", []), ensure_ascii=False),
                        "tp": card.get("topic", "Training"),
                        "sl": card.get("source_label", "Uphill Athlete Podcasts"),
                        "lang": lang,
                    },
                )
                count += 1
            except Exception as e:
                print(f"Error saving knowledge card: {e}")
        conn.commit()
    return count


def get_all_knowledge_cards(topic: str | None = None, lang: str = "en") -> list[dict[str, Any]]:
    with engine.connect() as conn:
        if topic and topic.lower() != "all":
            rows = conn.execute(
                text("SELECT * FROM knowledge_cards WHERE topic = :t AND lang = :lang ORDER BY topic, chapter_title"),
                {"t": topic, "lang": lang},
            ).fetchall()
        else:
            rows = conn.execute(
                text("SELECT * FROM knowledge_cards WHERE lang = :lang ORDER BY topic, chapter_title"), {"lang": lang}
            ).fetchall()
    result = []
    for row in rows:
        d = _row_to_dict(row)
        try:
            d["key_points"] = json.loads(d.get("key_points", "[]"))
        except Exception:
            d["key_points"] = []
        try:
            d["tags"] = json.loads(d.get("tags", "[]"))
        except Exception:
            d["tags"] = []
        result.append(d)
    return result


def get_random_knowledge_cards(n: int = 3, lang: str = "en") -> list[dict[str, Any]]:
    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT * FROM knowledge_cards WHERE lang = :lang ORDER BY RANDOM() LIMIT :n"), {"n": n, "lang": lang}
        ).fetchall()
    result = []
    for row in rows:
        d = _row_to_dict(row)
        try:
            d["key_points"] = json.loads(d.get("key_points", "[]"))
        except Exception:
            d["key_points"] = []
        try:
            d["tags"] = json.loads(d.get("tags", "[]"))
        except Exception:
            d["tags"] = []
        result.append(d)
    return result


def get_knowledge_topics() -> list[str]:
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT DISTINCT topic FROM knowledge_cards ORDER BY topic")).fetchall()
    return [r[0] for r in rows]


def clear_knowledge_cards() -> None:
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM knowledge_cards"))
        conn.commit()


def get_knowledge_card_count() -> int:
    with engine.connect() as conn:
        return conn.execute(text("SELECT COUNT(*) FROM knowledge_cards")).scalar()


# ─── Workout Types ────────────────────────────────────────────────────────────


def save_workout_types(types: list[dict[str, Any]], lang: str = "en") -> int:
    """Upsert workout type entries. Returns count saved."""
    saved = 0
    with engine.connect() as conn:
        for t in types:
            conn.execute(
                text("""
                INSERT INTO workout_types (type_key, display_name, zone, color, overview, execution, benefit, warning, lang)
                VALUES (:type_key, :display_name, :zone, :color, :overview, :execution, :benefit, :warning, :lang)
                ON CONFLICT (type_key, lang) DO UPDATE SET
                    display_name = EXCLUDED.display_name,
                    zone         = EXCLUDED.zone,
                    color        = EXCLUDED.color,
                    overview     = EXCLUDED.overview,
                    execution    = EXCLUDED.execution,
                    benefit      = EXCLUDED.benefit,
                    warning      = EXCLUDED.warning
                """),
                {
                    "type_key": t["type_key"],
                    "display_name": t["display_name"],
                    "zone": t.get("zone", "moderate"),
                    "color": t.get("color", "#6b7280"),
                    "overview": t["overview"],
                    "execution": t["execution"],
                    "benefit": t["benefit"],
                    "warning": t["warning"],
                    "lang": lang,
                },
            )
            saved += 1
        conn.commit()
    return saved


def get_workout_types(lang: str = "en") -> list[dict[str, Any]]:
    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT * FROM workout_types WHERE lang = :lang ORDER BY type_key ASC"),
            {"lang": lang},
        ).fetchall()
    return [_row_to_dict(r) for r in rows]


def get_workout_type_count() -> int:
    with engine.connect() as conn:
        return conn.execute(text("SELECT COUNT(*) FROM workout_types")).scalar()
