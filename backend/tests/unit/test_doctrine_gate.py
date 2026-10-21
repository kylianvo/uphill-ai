from services.athlete_tier import PHASES, hard_work_banned_phases, recent_weekly_minutes


def test_measured_wide_gap_bans_hard_work_in_every_phase():
    assert hard_work_banned_phases(is_ads=True, thresholds_measured=True) == PHASES


def test_measured_healthy_gap_bans_nothing():
    assert hard_work_banned_phases(is_ads=False, thresholds_measured=True) == frozenset()


def test_estimated_thresholds_keep_the_base_phase_easy():
    assert hard_work_banned_phases(is_ads=False, thresholds_measured=False) == frozenset({"Base"})


def test_recent_weekly_minutes_uses_the_athletes_own_pace():
    assert recent_weekly_minutes(40, 6.5) == 260
    assert recent_weekly_minutes(None, 6.5) is None
    assert recent_weekly_minutes(40, None) is None
