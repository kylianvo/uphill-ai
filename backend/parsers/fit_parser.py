import math
from datetime import datetime
from typing import Any

import fitparse


class FitParser:
    SEMICIRCLE_CONVERSION = 180.0 / (2**31)

    @staticmethod
    def semicircles_to_degrees(semicircles: int | None) -> float | None:
        if semicircles is None:
            return None
        # Fit files use semicircles for lat/lon representation.
        return semicircles * FitParser.SEMICIRCLE_CONVERSION

    @classmethod
    def parse(cls, file_bytes: bytes) -> dict[str, Any]:
        """
        Parses FIT file bytes and returns a dictionary containing
        summary metrics and downsampled time-series data.
        """
        try:
            fit_file = fitparse.FitFile(file_bytes)
        except Exception as e:
            raise ValueError(f"Failed to parse FIT file structure: {str(e)}")

        summary: dict[str, Any] = {
            "start_time": None,
            "total_distance_meters": 0.0,
            "total_duration_seconds": 0.0,
            "avg_heart_rate": None,
            "max_heart_rate": None,
            "total_elevation_gain_meters": 0.0,
            "total_elevation_loss_meters": 0.0,
            "avg_speed_mps": 0.0,
            "max_speed_mps": 0.0,
            "avg_cadence": None,
            "calories": 0,
        }

        records: list[dict[str, Any]] = []

        # 1. Gather all records and extract session summary if available
        for message in fit_file.get_messages():
            if message.name == "session":
                values = message.get_values()
                summary["total_distance_meters"] = values.get("total_distance", 0.0)
                summary["total_duration_seconds"] = values.get(
                    "total_timer_time", values.get("total_elapsed_time", 0.0)
                )
                summary["avg_heart_rate"] = values.get("avg_heart_rate")
                summary["max_heart_rate"] = values.get("max_heart_rate")
                summary["total_elevation_gain_meters"] = values.get("total_ascent", 0.0)
                summary["total_elevation_loss_meters"] = values.get("total_descent", 0.0)
                summary["avg_speed_mps"] = values.get("avg_speed", 0.0)
                summary["max_speed_mps"] = values.get("max_speed", 0.0)
                summary["avg_cadence"] = values.get("avg_cadence")
                summary["calories"] = values.get("total_calories", 0)
                if "start_time" in values and isinstance(values["start_time"], datetime):
                    summary["start_time"] = values["start_time"].isoformat()

            elif message.name == "record":
                values = message.get_values()
                # Semicircles conversion
                lat = cls.semicircles_to_degrees(values.get("position_lat"))
                lon = cls.semicircles_to_degrees(values.get("position_long"))

                record_time = values.get("timestamp")
                timestamp_str = record_time.isoformat() if isinstance(record_time, datetime) else None

                records.append(
                    {
                        "timestamp": timestamp_str,
                        "latitude": lat,
                        "longitude": lon,
                        "altitude_meters": values.get("enhanced_altitude", values.get("altitude")),
                        "heart_rate": values.get("heart_rate"),
                        "speed_mps": values.get("enhanced_speed", values.get("speed")),
                        "distance_meters": values.get("distance"),
                        "cadence": values.get("cadence"),
                    }
                )

        # 2. Backfill start time and check aggregates if 'session' was missing
        if not summary["start_time"] and records:
            summary["start_time"] = records[0]["timestamp"]

        if summary["total_distance_meters"] == 0.0 and records:
            summary["total_distance_meters"] = records[-1].get("distance_meters") or 0.0

        if summary["total_duration_seconds"] == 0.0 and records:
            # Estimate from timestamps
            t_start = records[0]["timestamp"]
            t_end = records[-1]["timestamp"]
            if t_start and t_end:
                try:
                    dt_start = datetime.fromisoformat(t_start)
                    dt_end = datetime.fromisoformat(t_end)
                    summary["total_duration_seconds"] = (dt_end - dt_start).total_seconds()
                except Exception:
                    pass

        # Calculate max/avg heart rate if missing from session
        if records and (summary["avg_heart_rate"] is None or summary["max_heart_rate"] is None):
            hrs = [r["heart_rate"] for r in records if r["heart_rate"] is not None]
            if hrs:
                summary["avg_heart_rate"] = sum(hrs) / len(hrs)
                summary["max_heart_rate"] = max(hrs)

        # 3. Downsample records for visualization (target ~600 points max to avoid blowing up payloads)
        downsampled_records = records
        max_points = 600
        if len(records) > max_points:
            step = math.ceil(len(records) / max_points)
            downsampled_records = records[::step]

        return {"summary": summary, "records": downsampled_records, "total_raw_points": len(records)}
