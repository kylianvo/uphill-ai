from datetime import date, datetime, timedelta

from services import fitness_tracking

MONDAY = date(2026, 8, 3)


class FakeDb:
    def __init__(self, activities):
        self.activities, self.saved = activities, {}

    def get_activities_for_pace(self, user_id, since, until):
        return [a for a in self.activities if since <= a["start_time"] < until]

    def upsert_fitness_checkpoint(self, plan_id, week, pace, n):
        self.saved[week] = (round(pace, 2), n)


def runs(week, pace_s):
    return [{"start_time": datetime.combine(MONDAY + timedelta(weeks=week - 1, days=d), datetime.min.time()),
             "duration_seconds": 2700, "avg_hr": 143, "distance_km": 7, "activity_type": "running",
             "adjusted_pace_sec_per_km": pace_s} for d in range(3)]  # fmt: skip


PLAN = {"id": 1, "user_id": 1, "start_date": "2026-08-03", "total_weeks": 16}


def test_refresh_stores_points_and_returns_the_path(monkeypatch):
    acts = [r for w in range(1, 7) for r in runs(w, 360 - 4 * w)]
    fake = FakeDb(acts)
    monkeypatch.setattr(fitness_tracking, "db", fake)
    status = fitness_tracking.refresh(PLAN, {"aet_hr": 145}, today=MONDAY + timedelta(weeks=6, days=2))
    assert sorted(fake.saved) == [1, 2, 3, 4, 5, 6, 7][:6] and status is not None and status.weeks == 5


def test_no_aet_or_no_history_means_no_path(monkeypatch):
    monkeypatch.setattr(fitness_tracking, "db", FakeDb([]))
    assert fitness_tracking.refresh(PLAN, {"aet_hr": None}) is None
    assert fitness_tracking.refresh(PLAN, {"aet_hr": 145}, today=MONDAY + timedelta(weeks=3)) is None


def test_a_failure_never_raises(monkeypatch):
    class Boom:
        def get_activities_for_pace(self, *a):
            raise RuntimeError("db down")

    monkeypatch.setattr(fitness_tracking, "db", Boom())
    assert fitness_tracking.refresh(PLAN, {"aet_hr": 145}, today=MONDAY + timedelta(weeks=6)) is None
