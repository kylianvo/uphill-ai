"""Unit tests for the COROS prose parsers.

Fixtures are verbatim responses captured from a live COROS account on
2026-09-04. If COROS changes its output format these tests fail, which is the
point -- the alternative is silently ingesting nulls.
"""

import json
from datetime import date

import pytest

from services.providers import coros_parsers as p

SPORT_RECORDS = """Sport Records — 2026-08-29 to 2026-09-02 (2 records)
========================

1. Indoor Run — 2026-09-02
   Location: Indoor Run
   Time Window: startTimestamp=1788318848 | endTimestamp=1788322570
   Duration: 1:00:05 | Distance: 10.92 km
   Average Pace: 5:30 /km | Avg HR: 157 bpm | Calories: 555 kcal
   LabelId: 480049189982601318 | SportType: 101

2. Outdoor Run — 2026-08-29
   Location: Sydney Run
   Start Coordinates: -33.876999, 151.108002
   Time Window: startTimestamp=1787982317 | endTimestamp=1787988291
   Duration: 1:30:34 | Distance: 15.03 km
   Average Pace: 6:02 /km | Avg HR: 148 bpm | Calories: 1040 kcal
   LabelId: 479959465976692837 | SportType: 100"""

ACTIVITY_DETAIL = """🏃 Outdoor Run Activity Details
========================================

Workout Time: 1:30:34
Distance: 15.03 km
Total Time: 1:39:34
Average Pace: 6:02 /km
Adjusted Pace: 5:55 /km
Average Heart Rate: 148 bpm
Average Cadence: 167 spm
Elevation Gain / Loss: 98 m / 117 m
Calories: 1040 kcal
Training Load: 161
Aerobic TE: 3.4
Anaerobic TE: 0.4
Training Focus: Base
Performance: Good"""

RESTING_HR = """Resting Heart Rate — Last 3 days
========================

2026-09-04: 57 bpm
2026-09-03: 59 bpm
2026-09-02: 59 bpm"""

SLEEP_HRV = """Sleep HRV — 2026-09-02 to 2026-09-04
========================
Note: dates are wake-up days (each value comes from the night that ended that morning).

HRV Assessment — Last 7 days
========================

2026-09-04:
  HRV Avg: 60 ms — Normal
  Normal Range: 52 - 72 ms
  Baseline: 62 ms
2026-09-02:
  HRV Avg: 49 ms — Below normal
  Normal Range: 53 - 73 ms
  Baseline: 63 ms"""

TRAINING_LOAD = """Training Load Assessment
========================

2026-09-04
Comment: Optimized
Short-Term Load: 77
Long-Term Load: 71
Load Ratio: 1.08

2026-09-03
Comment: Optimized
Short-Term Load: 90
Long-Term Load: 73
Load Ratio: 1.23"""

# --- Fix-round-1 fixtures ------------------------------------------------
# The five fixtures above are the verbatim captures and are never edited.
# Everything below is a new fixture built for a specific defect found in
# review: an ordinary vendor addition (a footer sentence) that must not
# corrupt real data, and truncated/malformed responses that must raise
# instead of silently looking like "no data".

# CRITICAL 1: a trailing sentence that happens to start with a date must not
# be mistaken for a new per-date block and overwrite the real 2026-09-04 row.
TRAINING_LOAD_WITH_FOOTER = (
    TRAINING_LOAD + "\n\n2026-09-04 data last refreshed at 06:00 local time. Figures may lag by up to 15 minutes."
)

# CRITICAL 2: header claims 2 records but the body was truncated before any
# record entries -- must raise, not silently return [].
SPORT_RECORDS_HEADER_COUNT_MISMATCH = "Sport Records — 2026-08-29 to 2026-09-02 (2 records)\n========================\n"

# CRITICAL 2: header present but body has neither data rows nor anything else
# left over -- a legitimate "no data for this athlete" answer, must not raise.
RESTING_HR_EMPTY_BODY = "Resting Heart Rate — Last 3 days\n========================\n"

# CRITICAL 2: header present, body has leftover content that isn't a data row
# -- the response shape was not recognised, must raise.
RESTING_HR_GARBAGE_BODY = (
    "Resting Heart Rate — Last 3 days\n========================\n\nService temporarily unavailable."
)

# CRITICAL 2: same two cases for training load.
TRAINING_LOAD_EMPTY_BODY = "Training Load Assessment\n========================\n"
TRAINING_LOAD_GARBAGE_BODY = "Training Load Assessment\n========================\n\n[no data]"

# CRITICAL 2: same two cases for sleep HRV -- note both header sections
# ("Sleep HRV" and "HRV Assessment") must be stripped for the empty case to
# be recognised as genuinely empty.
SLEEP_HRV_EMPTY_BODY = """Sleep HRV — 2026-09-02 to 2026-09-04
========================
Note: dates are wake-up days (each value comes from the night that ended that morning).

HRV Assessment — Last 7 days
========================
"""
SLEEP_HRV_GARBAGE_BODY = """Sleep HRV — 2026-09-02 to 2026-09-04
========================
Note: dates are wake-up days (each value comes from the night that ended that morning).

HRV Assessment — Last 7 days
========================

Service temporarily unavailable."""

# CRITICAL 2 worst case: a response carrying only the (much longer) time
# series section, no assessment section at all. "Sleep HRV" alone as a guard
# would pass here because it's a substring of "Sleep HRV Time Series".
SLEEP_HRV_TIME_SERIES_ONLY = """Sleep HRV — 2026-09-02 to 2026-09-04
========================

Sleep HRV Time Series
========================

00:00 42 ms
00:05 43 ms"""

# --- Fix-round-2 fixtures --------------------------------------------------
# Round 1's guards over-corrected: they raised on a *recognised* shape that
# legitimately has no data for one date (as opposed to a body that is
# unrecognised/truncated). Both scenarios below are plausible real responses
# -- a brand-new athlete with too little history, or a night the watch
# couldn't compute HRV -- and must return an empty result, not raise.

# A real date header with no numeric fields at all (just a Comment line).
TRAINING_LOAD_INSUFFICIENT_HISTORY = (
    "Training Load Assessment\n========================\n\n"
    "2026-09-04\nComment: Insufficient training history to compute load ratio"
)

# A real date header in the assessment section with no "HRV Avg:" line.
SLEEP_HRV_INSUFFICIENT_DATA = (
    "Sleep HRV — 2026-09-02 to 2026-09-04\n========================\n\n"
    "HRV Assessment — Last 7 days\n========================\n\n"
    "2026-09-04:\nInsufficient sleep data to compute HRV for this night."
)

# IMPORTANT 3 (+ addendum): a record missing LabelId, Duration, or its Time
# Window startTimestamp cannot be identified, stored, or timed -- each must
# raise rather than silently coming back as None.
SPORT_RECORD_MISSING_LABEL_ID = """Sport Records — 2026-09-02 to 2026-09-02 (1 records)
========================

1. Indoor Run — 2026-09-02
   Location: Indoor Run
   Time Window: startTimestamp=1788318848 | endTimestamp=1788322570
   Duration: 1:00:05 | Distance: 10.92 km
   Average Pace: 5:30 /km | Avg HR: 157 bpm | Calories: 555 kcal
   SportType: 101"""

SPORT_RECORD_MISSING_DURATION = """Sport Records — 2026-09-02 to 2026-09-02 (1 records)
========================

1. Indoor Run — 2026-09-02
   Location: Indoor Run
   Time Window: startTimestamp=1788318848 | endTimestamp=1788322570
   Distance: 10.92 km
   Average Pace: 5:30 /km | Avg HR: 157 bpm | Calories: 555 kcal
   LabelId: 480049189982601318 | SportType: 101"""

SPORT_RECORD_MISSING_TIME_WINDOW = """Sport Records — 2026-09-02 to 2026-09-02 (1 records)
========================

1. Indoor Run — 2026-09-02
   Location: Indoor Run
   Duration: 1:00:05 | Distance: 10.92 km
   Average Pace: 5:30 /km | Avg HR: 157 bpm | Calories: 555 kcal
   LabelId: 480049189982601318 | SportType: 101"""


class TestDurationAndPace:
    def test_parses_hour_minute_second_duration(self):
        assert p.parse_duration("1:30:34") == 5434.0

    def test_parses_minute_second_duration(self):
        assert p.parse_duration("19:31") == 1171.0

    def test_parses_pace_into_seconds_per_km(self):
        assert p.parse_pace("5:30 /km") == 330.0


class TestSportRecords:
    def test_returns_one_entry_per_record(self):
        assert len(p.parse_sport_records(SPORT_RECORDS)) == 2

    def test_extracts_label_id_and_sport_type(self):
        first = p.parse_sport_records(SPORT_RECORDS)[0]
        assert first["label_id"] == "480049189982601318"
        assert first["sport_type"] == 101

    def test_extracts_timestamps_as_integers(self):
        first = p.parse_sport_records(SPORT_RECORDS)[0]
        assert first["start_timestamp"] == 1788318848
        assert first["end_timestamp"] == 1788322570

    def test_extracts_distance_duration_hr_and_calories(self):
        first = p.parse_sport_records(SPORT_RECORDS)[0]
        assert first["distance_km"] == 10.92
        assert first["duration_seconds"] == 3605.0
        assert first["avg_hr"] == 157
        assert first["calories"] == 555

    def test_handles_records_with_and_without_coordinates(self):
        records = p.parse_sport_records(SPORT_RECORDS)
        assert records[0]["start_lat"] is None
        assert records[1]["start_lat"] == -33.876999

    def test_returns_empty_list_when_there_are_no_records(self):
        assert p.parse_sport_records("Sport Records — none (0 records)\n========================") == []

    def test_missing_label_id_raises(self):
        # LabelId is the cross-provider dedup key -- a record we can't
        # identify must not be silently returned with label_id=None.
        with pytest.raises(p.CorosParseError):
            p.parse_sport_records(SPORT_RECORD_MISSING_LABEL_ID)

    def test_missing_duration_raises(self):
        # activities.duration_seconds is REAL NOT NULL -- a record we can't
        # time must not be silently returned with duration_seconds=None.
        with pytest.raises(p.CorosParseError):
            p.parse_sport_records(SPORT_RECORD_MISSING_DURATION)

    def test_missing_time_window_raises(self):
        # activities.start_time is TIMESTAMPTZ NOT NULL, and to_utc(None)
        # would otherwise raise a confusing bare TypeError far from here.
        with pytest.raises(p.CorosParseError):
            p.parse_sport_records(SPORT_RECORD_MISSING_TIME_WINDOW)


class TestActivityDetail:
    def test_extracts_elevation_gain_and_loss_separately(self):
        detail = p.parse_activity_detail(ACTIVITY_DETAIL)
        assert detail["elevation_gain_m"] == 98.0
        assert detail["elevation_loss_m"] == 117.0

    def test_extracts_training_effect_and_load(self):
        detail = p.parse_activity_detail(ACTIVITY_DETAIL)
        assert detail["training_load"] == 161.0
        assert detail["aerobic_te"] == 3.4
        assert detail["anaerobic_te"] == 0.4

    def test_extracts_adjusted_pace_which_is_coros_grade_adjusted_pace(self):
        assert p.parse_activity_detail(ACTIVITY_DETAIL)["adjusted_pace_sec_per_km"] == 355.0

    def test_missing_optional_fields_are_none_not_an_error(self):
        detail = p.parse_activity_detail("🏃 Outdoor Run Activity Details\n\nDistance: 5.00 km")
        assert detail["distance_km"] == 5.0
        assert detail["training_load"] is None


class TestDailyMetrics:
    def test_parses_resting_heart_rate_by_date(self):
        assert p.parse_resting_hr(RESTING_HR)[date(2026, 9, 4)] == 57

    def test_parses_sleep_hrv_average_baseline_and_status(self):
        row = p.parse_sleep_hrv(SLEEP_HRV)[date(2026, 9, 2)]
        assert row["hrv_ms"] == 49.0
        assert row["hrv_baseline_ms"] == 63.0
        assert row["hrv_status"] == "Below normal"

    def test_parses_training_load_ratio(self):
        row = p.parse_training_load(TRAINING_LOAD)[date(2026, 9, 4)]
        assert row["training_load_short"] == 77.0
        assert row["training_load_long"] == 71.0
        assert row["load_ratio"] == 1.08

    def test_trailing_disclaimer_line_does_not_overwrite_real_date_row(self):
        # A vendor footer sentence that happens to start with a date (e.g.
        # "2026-09-04 data last refreshed at ...") must not be mistaken for a
        # second block keyed to the same date, silently nulling out the real
        # 77 / 71 / 1.08 row for 2026-09-04.
        row = p.parse_training_load(TRAINING_LOAD_WITH_FOOTER)[date(2026, 9, 4)]
        assert row["training_load_short"] == 77.0
        assert row["training_load_long"] == 71.0
        assert row["load_ratio"] == 1.08


class TestContractGuard:
    def test_unrecognisable_sport_records_output_raises_rather_than_returning_nothing(self):
        # Silently returning [] on a format change would look like "no activities"
        # and quietly stop syncing. Fail loudly instead.
        with pytest.raises(p.CorosParseError):
            p.parse_sport_records("<html>maintenance</html>")

    def test_sport_records_header_claims_records_but_body_has_none_raises(self):
        # The header's own "(N records)" count says 2 but the body was cut
        # off before any record entries -- must not look like "no activities".
        with pytest.raises(p.CorosParseError):
            p.parse_sport_records(SPORT_RECORDS_HEADER_COUNT_MISMATCH)

    def test_resting_hr_header_with_garbage_body_raises(self):
        with pytest.raises(p.CorosParseError):
            p.parse_resting_hr(RESTING_HR_GARBAGE_BODY)

    def test_resting_hr_header_with_genuinely_empty_body_returns_empty(self):
        # A brand-new athlete with no resting-HR history is a real, legitimate
        # case and must not raise.
        assert p.parse_resting_hr(RESTING_HR_EMPTY_BODY) == {}

    def test_training_load_header_with_garbage_body_raises(self):
        with pytest.raises(p.CorosParseError):
            p.parse_training_load(TRAINING_LOAD_GARBAGE_BODY)

    def test_training_load_header_with_genuinely_empty_body_returns_empty(self):
        assert p.parse_training_load(TRAINING_LOAD_EMPTY_BODY) == {}

    def test_sleep_hrv_header_with_garbage_body_raises(self):
        with pytest.raises(p.CorosParseError):
            p.parse_sleep_hrv(SLEEP_HRV_GARBAGE_BODY)

    def test_sleep_hrv_header_with_genuinely_empty_body_returns_empty(self):
        assert p.parse_sleep_hrv(SLEEP_HRV_EMPTY_BODY) == {}

    def test_sleep_hrv_time_series_only_response_raises(self):
        # "Sleep HRV" alone would wrongly pass as a guard here since it's a
        # substring of the "Sleep HRV Time Series" section heading -- the
        # assessment section itself must be required.
        with pytest.raises(p.CorosParseError):
            p.parse_sleep_hrv(SLEEP_HRV_TIME_SERIES_ONLY)

    def test_training_load_recognised_date_with_no_numeric_fields_returns_empty(self):
        # A real date header (e.g. a brand-new athlete with too little
        # training history to compute a load ratio yet) is a recognised
        # shape with legitimately nothing to record -- must not raise.
        assert p.parse_training_load(TRAINING_LOAD_INSUFFICIENT_HISTORY) == {}

    def test_sleep_hrv_recognised_date_with_no_avg_line_returns_empty(self):
        # A real date header for a night the watch couldn't compute HRV for
        # is a recognised shape with legitimately nothing to record -- must
        # not raise.
        assert p.parse_sleep_hrv(SLEEP_HRV_INSUFFICIENT_DATA) == {}

    def test_parsers_handle_json_encoded_strings(self):
        records = p.parse_sport_records(json.dumps(SPORT_RECORDS))
        assert len(records) == 2
        assert records[0]["label_id"] == "480049189982601318"

        detail = p.parse_activity_detail(json.dumps(ACTIVITY_DETAIL))
        assert detail["duration_seconds"] == 5434.0

        rhr = p.parse_resting_hr(json.dumps(RESTING_HR))
        assert rhr[date(2026, 9, 2)] == 59

        hrv = p.parse_sleep_hrv(json.dumps(SLEEP_HRV))
        assert hrv[date(2026, 9, 2)]["hrv_ms"] == 49.0

        load = p.parse_training_load(json.dumps(TRAINING_LOAD))
        assert load[date(2026, 9, 3)]["training_load_short"] == 90.0

    def test_parse_fitness_overview_extracts_metrics(self):
        text = """Fitness Assessment Overview
========================

VO2max: 57
Running Level: 85
Threshold Pace: 4:34 /km
5 km Prediction: 21:56
10 km Prediction: 45:37
Half Marathon Prediction: 1:41:12
Marathon Prediction: 3:31:18"""
        res = p.parse_fitness_overview(text)
        assert res["vo2max"] == 57.0
        assert res["running_level"] == 85.0
        assert res["threshold_pace"] == "4:34"
        assert res["threshold_pace_sec_per_km"] == 274.0
        assert res["prediction_5k_sec"] == 1316.0
        assert res["prediction_10k_sec"] == 2737.0
        assert res["prediction_half_marathon_sec"] == 6072.0
        assert res["prediction_marathon_sec"] == 12678.0

    def test_parse_fitness_overview_missing_header_raises(self):
        with pytest.raises(p.CorosParseError):
            p.parse_fitness_overview("Some random text with no header")

    def test_strength_sport_records_extracts_sets(self):
        text = """Sport Records — 2026-09-06 to 2026-09-06 (1 records)
========================

1. Strength — 2026-09-06
   Location: Strength
   Time Window: startTimestamp=1788694984 | endTimestamp=1788699050
   Duration: 1:07:46 | Sets: 3 | Avg HR: 92 bpm | Calories: 257 kcal
   LabelId: 480150249229287632 | SportType: 402"""
        records = p.parse_sport_records(text)
        assert len(records) == 1
        assert records[0]["sets"] == 3
        assert records[0]["sport_type"] == 402

    def test_strength_activity_detail_extracts_sets(self):
        text = """🏋️ Strength Activity Details
========================================

Workout Time: 1:07:46
Total Time: 1:07:46
Sets: 4
Average Heart Rate: 92 bpm
Calories: 257 kcal
Training Load: 8
Aerobic TE: 0.7
Anaerobic TE: 0.0"""
        detail = p.parse_activity_detail(text)
        assert detail["sets"] == 4
        assert detail["training_load"] == 8.0
        assert detail["aerobic_te"] == 0.7
