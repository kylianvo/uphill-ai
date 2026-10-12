import math
from datetime import date
from typing import Any
from urllib.parse import urlsplit


def normalize_manual_result(data: dict[str, Any]) -> dict[str, Any]:
    value = dict(data)
    for key, limit in {"race_name": 200, "location": 200, "bib": 100, "result_url": 2048, "user_note": 2000}.items():
        text = value.get(key)
        if text is not None and not isinstance(text, str):
            raise ValueError(f"Invalid {key}")
        text = text.strip() if text is not None else None
        if text and len(text) > limit:
            raise ValueError(f"Invalid {key}")
        value[key] = text or None
    if not value["race_name"] or value.get("discipline") not in ("road", "trail"):
        raise ValueError("Race name and discipline are required")
    try:
        date.fromisoformat(value["race_date"])
    except (KeyError, TypeError, ValueError):
        raise ValueError("Invalid race date") from None
    km = value.get("distance_km")
    if not isinstance(km, int | float) or not math.isfinite(km) or not 0 < km <= 1000:
        raise ValueError("Invalid race distance")
    gain = value.get("elevation_gain_m")
    if gain is not None and (not isinstance(gain, int | float) or not math.isfinite(gain) or gain < 0):
        raise ValueError("Invalid elevation gain")
    for group in ("overall", "gender", "age_group"):
        rank, total = value.get(f"rank_{group}"), value.get(f"total_{group}")
        if any(x is not None and (type(x) is not int or x < 1) for x in (rank, total)):
            raise ValueError(f"Invalid {group} rank")
        if rank is not None and total is not None and rank > total:
            raise ValueError(f"Invalid {group} rank")
    if value.get("is_dnf"):
        value["finish_time_sec"] = None
    elif type(value.get("finish_time_sec")) is not int or value["finish_time_sec"] <= 0:
        raise ValueError("Finish time is required for a finish")
    if value["result_url"]:
        try:
            url = urlsplit(value["result_url"])
            if url.scheme not in ("http", "https") or not url.hostname or url.username or url.password:
                raise ValueError("Result URL must be an absolute HTTP(S) URL without credentials")
        except ValueError:
            raise ValueError("Result URL must be an absolute HTTP(S) URL without credentials") from None
    return value
