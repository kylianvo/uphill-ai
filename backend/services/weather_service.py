"""Per-segment race-day weather for Pace Strategy (Open-Meteo, no API key).

Checkpoints are annotated in place with an apparent temperature at each
checkpoint's estimated arrival hour (from a first pacing pass) plus an
after-sunset flag for headlamp planning. The engine's heat multiplier
(PacingCalculator.weather_multiplier) then picks up ``temp_c``.
Weather must never break pacing: any failure leaves checkpoints untouched.
"""

import logging
from collections.abc import Callable
from datetime import datetime, timedelta
from typing import Any

import httpx

logger = logging.getLogger(__name__)

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
FORECAST_MAX_DAYS = 16  # Open-Meteo horizon

# (lat_rounded, lon_rounded, start_date, end_date) -> forecast payload
_forecast_cache: dict[tuple, dict[str, Any] | None] = {}

Fetcher = Callable[[float, float, str, str], dict[str, Any] | None]


class WeatherService:
    @staticmethod
    def apparent_temp_c(temp_c: float, humidity_pct: float) -> float:
        """Humidity-adjusted temperature: above ~20°C, high humidity blocks
        evaporative cooling, so each 10% RH above 60% feels ~+0.6°C."""
        if temp_c <= 20.0 or humidity_pct <= 60.0:
            return temp_c
        return round(temp_c + 0.06 * (humidity_pct - 60.0), 1)

    @staticmethod
    def fetch_forecast(lat: float, lon: float, start_date: str, end_date: str) -> dict[str, Any] | None:
        key = (round(lat, 1), round(lon, 1), start_date, end_date)
        if key in _forecast_cache:
            return _forecast_cache[key]
        try:
            response = httpx.get(
                OPEN_METEO_URL,
                params={
                    "latitude": round(lat, 3),
                    "longitude": round(lon, 3),
                    "hourly": "temperature_2m,relative_humidity_2m,precipitation",
                    "daily": "sunset",
                    "timezone": "auto",
                    "start_date": start_date,
                    "end_date": end_date,
                },
                timeout=8.0,
            )
            response.raise_for_status()
            forecast = response.json()
        except Exception as e:
            logger.warning("Open-Meteo fetch failed for (%s, %s): %s", lat, lon, e)
            forecast = None
        _forecast_cache[key] = forecast
        return forecast

    @staticmethod
    def _hour_iso(moment: datetime) -> str:
        return moment.strftime("%Y-%m-%dT%H:00")

    @classmethod
    def _sunset_for(cls, forecast: dict[str, Any], date_str: str) -> datetime | None:
        daily = forecast.get("daily") or {}
        for day, sunset in zip(daily.get("time") or [], daily.get("sunset") or []):
            if day == date_str:
                try:
                    return datetime.fromisoformat(sunset)
                except ValueError:
                    return None
        return None

    @classmethod
    def annotate_checkpoints(
        cls,
        checkpoints: list[dict[str, Any]],
        paced: list[dict[str, Any]],
        race_start: datetime,
        fetcher: Fetcher | None = None,
    ) -> dict[str, Any]:
        """Sets temp_c / after_sunset on checkpoints from their ETA-hour forecast.

        ``paced`` supplies cumulative_time_mins per checkpoint (a first pacing
        pass without weather). Returns {"applied": bool}.
        """
        fetch = fetcher or cls.fetch_forecast
        start_date = race_start.strftime("%Y-%m-%d")
        applied = False

        for cp, split in zip(checkpoints, paced):
            lat = cp.get("latitude")
            lon = cp.get("longitude")
            if lat is None or lon is None:
                continue
            eta = race_start + timedelta(minutes=split.get("cumulative_time_mins") or 0.0)
            end_date = eta.strftime("%Y-%m-%d")
            forecast = fetch(lat, lon, start_date, end_date)
            if not forecast:
                continue
            hourly = forecast.get("hourly") or {}
            times = hourly.get("time") or []
            hour_iso = cls._hour_iso(eta)
            if hour_iso not in times:
                continue
            idx = times.index(hour_iso)
            try:
                temp = float(hourly["temperature_2m"][idx])
                humidity = float((hourly.get("relative_humidity_2m") or [50.0] * len(times))[idx])
            except (KeyError, IndexError, TypeError, ValueError):
                continue
            cp["temp_c"] = cls.apparent_temp_c(temp, humidity)
            try:
                cp["rain_mm"] = float((hourly.get("precipitation") or [0.0] * len(times))[idx])
            except (IndexError, TypeError, ValueError):
                cp["rain_mm"] = 0.0
            sunset = cls._sunset_for(forecast, eta.strftime("%Y-%m-%d"))
            cp["after_sunset"] = bool(sunset and eta > sunset)
            applied = True

        return {"applied": applied}
