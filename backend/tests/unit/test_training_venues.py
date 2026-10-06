"""Training venues: where each session type can happen for this athlete."""

from services.plan_generator import PlanGenerator
from services.training_venues import Venues, parse_days

CITY_WEEKENDS = Venues(environment="flat", mountain_days=("Saturday", "Sunday"))


def test_parse_days_accepts_stored_json_and_lists_and_drops_junk():
    assert parse_days('["Sunday", "Saturday"]') == ("Saturday", "Sunday")
    assert parse_days(["Saturday", "Funday"]) == ("Saturday",)
    assert parse_days(None) == ()
    assert parse_days("not json") == ()


def test_from_race_info_defaults_to_a_flat_standard_treadmill():
    v = Venues.from_race_info({})
    assert v.environment == "flat" and v.mountain_days == () and not v.stair_access
    assert v.treadmill_max_incline == 15


def test_treadmill_incline_is_clamped_to_a_real_machine_range():
    assert Venues.from_race_info({"treadmill_max_incline": 5}).treadmill_max_incline == 15
    assert Venues.from_race_info({"treadmill_max_incline": 99}).treadmill_max_incline == 40


def test_weekend_mountains_give_hills_only_on_those_days():
    assert CITY_WEEKENDS.hills_on("Saturday")
    assert not CITY_WEEKENDS.hills_on("Tuesday")
    assert CITY_WEEKENDS.hills_only_some_days


def test_hilly_or_mixed_home_terrain_means_hills_every_day():
    for env in ("hilly", "mixed"):
        assert Venues(environment=env).hills_on("Tuesday")


def test_hill_sprint_venue_ladder():
    assert CITY_WEEKENDS.hill_sprint_venue("Saturday") == "hill"
    assert CITY_WEEKENDS.hill_sprint_venue("Tuesday") is None
    stairs = Venues(mountain_days=("Saturday",), stair_access=True, use_treadmill=True)
    assert stairs.hill_sprint_venue("Tuesday") == "stairs"
    assert Venues(use_treadmill=True).hill_sprint_venue("Tuesday") == "treadmill"
    assert not Venues().hill_sprints_possible


def test_prompt_block_for_a_city_runner_with_weekend_mountains_and_stairs():
    v = Venues(
        environment="flat",
        mountain_days=("Saturday", "Sunday"),
        stair_access=True,
        use_treadmill=True,
        treadmill_max_incline=15,
        has_gym_access=True,
    )
    block = v.prompt_block(allows_intensity=True, allows_me=True)
    assert "ONLY on Saturday, Sunday" in block
    assert "steep stairs taken two at a time" in block
    assert "NEVER set `treadmill_incline` above 15%" in block
    assert "treadmill at 15% with a 5-15% BW vest or pack" in block
    assert "Long run with vertical and any back-to-back overreach go on Saturday, Sunday" in block


def test_weekend_only_hills_without_stairs_or_treadmill_pin_sprints_to_those_days():
    block = CITY_WEEKENDS.prompt_block(allows_intensity=True, allows_me=True)
    assert "Schedule Hill Sprints ONLY on Saturday, Sunday" in block


def test_incline_trainer_unlocks_25_percent_me():
    block = Venues(use_treadmill=True, treadmill_max_incline=25).prompt_block(allows_intensity=True, allows_me=True)
    assert "treadmill at 25% (incline trainer)" in block


def test_no_venue_at_all_forbids_hill_sessions():
    block = Venues().prompt_block(allows_intensity=True, allows_me=False)
    assert "NEVER prescribe a Hill Sprint" in block


def test_beginners_never_get_hill_sessions_or_me_venues():
    block = Venues(environment="hilly", stair_access=True).prompt_block(allows_intensity=False, allows_me=False)
    assert "NEVER prescribe a Hill Sprint" in block
    assert "Muscular Endurance" not in block


def test_hill_sprint_treadmill_incline_follows_the_athletes_machine():
    wo = {"title": "Hill Sprint Repeats", "treadmill_incline": 1.0}
    assert PlanGenerator.resolve_treadmill_settings(wo, "6:00 /km")[0] == "15"
    assert PlanGenerator.resolve_treadmill_settings(wo, "6:00 /km", max_incline=25.0)[0] == "25"
    run = {"title": "Steep Trail Run", "treadmill_incline": 22.0}
    assert PlanGenerator.resolve_treadmill_settings(run, "6:00 /km")[0] == "14-15"
    assert PlanGenerator.resolve_treadmill_settings(run, "6:00 /km", max_incline=25.0)[0] == "21-23"


def test_never_offers_substitutes_the_athlete_does_not_have():
    sunday_only = Venues(mountain_days=("Sunday",)).prompt_block(allows_intensity=True, allows_me=True)
    assert "treadmill incline blocks" not in sunday_only and "stair laps" not in sunday_only
    trainer = Venues(use_treadmill=True, treadmill_max_incline=25).prompt_block(allows_intensity=True, allows_me=True)
    assert "from treadmill incline blocks." in trainer and "stair laps" not in trainer
    assert "where available" not in trainer
