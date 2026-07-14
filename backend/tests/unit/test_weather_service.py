"""Tests for WeatherService — forecast annotation for pace-strategy checkpoints.
No network: the Open-Meteo fetcher is injected."""

from datetime import datetime

from services.weather_service import WeatherService


def make_forecast(temps_by_hour: dict[str, float], humidity: float = 50.0, sunset: str = "2026-07-20T18:30"):
    times = sorted(temps_by_hour)
    return {
        "hourly": {
            "time": times,
            "temperature_2m": [temps_by_hour[t] for t in times],
            "relative_humidity_2m": [humidity] * len(times),
        },
        "daily": {"time": [times[0][:10]], "sunset": [sunset]},
    }


def make_checkpoints():
    return [
        {"name": "Start", "distance_meters": 0, "latitude": 22.3, "longitude": 103.8},
        {"name": "KM 10", "distance_meters": 10_000, "latitude": 22.35, "longitude": 103.85},
        {"name": "KM 20", "distance_meters": 20_000, "latitude": 22.4, "longitude": 103.9},
    ]


def make_paced():
    return [
        {"cumulative_time_mins": 0.0},
        {"cumulative_time_mins": 120.0},
        {"cumulative_time_mins": 300.0},
    ]


class TestApparentTemp:
    def test_dry_conditions_return_air_temperature(self):
        assert WeatherService.apparent_temp_c(20.0, 40.0) == 20.0

    def test_humidity_raises_apparent_temperature(self):
        assert WeatherService.apparent_temp_c(28.0, 90.0) > 28.0

    def test_humidity_has_no_effect_when_cool(self):
        assert WeatherService.apparent_temp_c(10.0, 95.0) == 10.0


class TestAnnotateCheckpoints:
    def test_sets_temp_from_forecast_at_each_eta_hour(self):
        forecast = make_forecast({f"2026-07-20T{h:02d}:00": 15.0 + h for h in range(5, 12)})
        cps = make_checkpoints()
        info = WeatherService.annotate_checkpoints(
            cps, make_paced(), datetime(2026, 7, 20, 5, 0), fetcher=lambda lat, lon, d0, d1: forecast
        )
        assert info["applied"] is True
        # start 05:00 -> 20°C; +120min = 07:00 -> 22°C; +300min = 10:00 -> 25°C
        assert cps[0]["temp_c"] == 20.0
        assert cps[1]["temp_c"] == 22.0
        assert cps[2]["temp_c"] == 25.0

    def test_marks_checkpoints_after_sunset(self):
        forecast = make_forecast({f"2026-07-20T{h:02d}:00": 20.0 for h in range(15, 23)}, sunset="2026-07-20T18:30")
        cps = make_checkpoints()
        WeatherService.annotate_checkpoints(
            cps, make_paced(), datetime(2026, 7, 20, 15, 0), fetcher=lambda *a: forecast
        )
        # ETAs: 15:00, 17:00, 20:00 -> only the last is after 18:30 sunset
        assert cps[0]["after_sunset"] is False
        assert cps[1]["after_sunset"] is False
        assert cps[2]["after_sunset"] is True

    def test_failed_fetch_leaves_checkpoints_untouched(self):
        cps = make_checkpoints()
        info = WeatherService.annotate_checkpoints(
            cps, make_paced(), datetime(2026, 7, 20, 5, 0), fetcher=lambda *a: None
        )
        assert info["applied"] is False
        assert "temp_c" not in cps[0]

    def test_checkpoints_without_coordinates_are_skipped(self):
        cps = make_checkpoints()
        del cps[1]["latitude"]
        forecast = make_forecast({f"2026-07-20T{h:02d}:00": 20.0 for h in range(5, 12)})
        WeatherService.annotate_checkpoints(cps, make_paced(), datetime(2026, 7, 20, 5, 0), fetcher=lambda *a: forecast)
        assert "temp_c" not in cps[1]
        assert cps[2]["temp_c"] == 20.0
