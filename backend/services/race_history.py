"""Claimed race results, source adapters, and athlete-scoped calculations."""

from __future__ import annotations

import hashlib
import json
import logging
import re
import time
import unicodedata
from datetime import UTC, date, datetime, timedelta
from typing import Any

import httpx
from sqlalchemy import text

from config import settings
from db import engine

_HEADERS = {"User-Agent": "UphillAI/1.0 (+https://uphill-ai.io.vn)"}
_VBM_URL = "https://bestmarathon.vn/wp-admin/admin-ajax.php"
_UTMB_URL = "https://api.utmb.world"
_VBM_EVENTS = ("fmm", "fmf", "hmm", "hmf", "road100", "trail100")
_VBM_KM = {"FMM": 42.195, "FMF": 42.195, "HMM": 21.0975, "HMF": 21.0975}
logger = logging.getLogger(__name__)
_WORKER_LOCK_ID = 521749231
_RESULT_COLUMNS = (
    "source_key",
    "discipline",
    "race_name",
    "event_name",
    "race_date",
    "country_code",
    "distance_km",
    "elevation_gain_m",
    "utmb_category",
    "finish_time_sec",
    "is_dnf",
    "rank_overall",
    "total_overall",
    "rank_gender",
    "total_gender",
    "rank_age_group",
    "total_age_group",
    "bib",
    "result_url",
    "source_race_uri",
    "is_pr",
    "raw",
)


def normalize_name(value: str) -> str:
    value = value.replace("đ", "d").replace("Đ", "D")
    value = "".join(c for c in unicodedata.normalize("NFKD", value) if not unicodedata.combining(c))
    return " ".join(sorted(re.findall(r"[A-Z0-9]+", value.upper())))


def _fetch(url: str, params: dict[str, Any] | None = None, utmb: bool = False) -> dict[str, Any]:
    headers = {**_HEADERS, **({"x-tenant-id": "worldseries"} if utmb else {})}
    with httpx.Client(timeout=10, headers=headers, follow_redirects=False) as client:
        response = client.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, dict):
            raise ValueError("Unexpected source response")
        return data


def _seconds(value: Any) -> int | None:
    if value is None or value == "":
        return None
    if isinstance(value, int):
        return value if value > 0 else None
    parts = str(value).split(":")
    if len(parts) not in (2, 3) or any(not p.isdigit() for p in parts):
        return None
    numbers = [int(p) for p in parts]
    return numbers[0] * 3600 + numbers[1] * 60 + (numbers[2] if len(numbers) == 3 else 0)


def _race_date(value: Any) -> str | None:
    if not value:
        return None
    value = str(value)
    try:
        return date.fromisoformat(value[:10]).isoformat()
    except ValueError:
        match = re.search(r"(\d{1,2})/(\d{1,2})/(20\d{2})", value)
        if not match:
            return None
        try:
            return date(int(match[3]), int(match[2]), int(match[1])).isoformat()
        except ValueError:
            return None


def normalize_utmb(raw: dict[str, Any]) -> dict[str, Any] | None:
    race_date = _race_date(raw.get("dateIso"))
    distance = float(raw.get("distance") or 0)
    key = raw.get("raceYearId")
    if not race_date or distance <= 0 or key is None:
        return None
    dnf = bool(raw.get("isDnf"))
    finish_time = None if dnf else _seconds(raw.get("time"))
    if not dnf and not finish_time:
        return None
    return {
        "source_key": str(key),
        "discipline": "trail",
        "race_name": raw.get("race") or raw.get("raceName") or "Race",
        "event_name": raw.get("eventName"),
        "race_date": race_date,
        "country_code": raw.get("countryCode"),
        "distance_km": distance,
        "elevation_gain_m": raw.get("elevationGain"),
        "utmb_category": raw.get("piCategory"),
        "finish_time_sec": finish_time,
        "is_dnf": dnf,
        "rank_overall": raw.get("rank"),
        "total_overall": raw.get("totalRanked"),
        "rank_gender": raw.get("rankGender"),
        "total_gender": raw.get("totalRankedGender"),
        "rank_age_group": None,
        "total_age_group": None,
        "bib": None,
        "result_url": None,
        "source_race_uri": raw.get("uri"),
        "is_pr": False,
        "raw": raw,
    }


def normalize_vbm(parent: dict[str, Any], result: dict[str, Any]) -> dict[str, Any] | None:
    event = str(parent.get("event") or "").upper()
    distance = _VBM_KM.get(event) or float(parent.get("distance_km") or 0)
    race_name = result.get("race") or parent.get("race_full_name") or parent.get("race") or "Race"
    race_date = _race_date(result.get("race_day")) or _race_date(race_name)
    seconds = _seconds(result.get("total_sec") or result.get("mark_sec") or result.get("time") or result.get("mark"))
    if not race_date or distance <= 0 or not seconds:
        return None
    bib = str(result.get("bib") or "").strip() or None
    stable = "|".join((event, normalize_name(race_name), race_date, bib or "", str(seconds)))
    key = hashlib.sha256(stable.encode()).hexdigest()[:32]
    return {
        "source_key": key,
        "discipline": "trail" if "TRAIL" in event else "road",
        "race_name": race_name,
        "event_name": None,
        "race_date": race_date,
        "country_code": "VN",
        "distance_km": distance,
        "elevation_gain_m": None,
        "utmb_category": None,
        "finish_time_sec": seconds,
        "is_dnf": False,
        "rank_overall": result.get("rank"),
        "total_overall": result.get("total"),
        "rank_gender": None,
        "total_gender": None,
        "rank_age_group": None,
        "total_age_group": None,
        "bib": bib,
        "result_url": parent.get("result_url"),
        "source_race_uri": None,
        "is_pr": bool(result.get("is_pr", result is parent)),
        "raw": {"parent": parent, "result": result},
    }


def search_utmb(name: str) -> list[dict[str, Any]]:
    data = _fetch(
        f"{_UTMB_URL}/search/runners",
        {"category": "general", "nationality": "VN", "search": name, "limit": 15, "offset": 0},
        True,
    )
    return [
        {
            "external_id": row["uri"],
            "display_name": row.get("fullname"),
            "age_group": row.get("ageGroup"),
            "index": row.get("ip"),
            "sex": row.get("sex"),
            "source": "utmb",
        }
        for row in data.get("runners", [])
        if row.get("uri")
    ]


def search_vbm(name: str) -> list[dict[str, Any]]:
    norm = normalize_name(name)
    if not norm:
        return []
    with engine.connect() as conn:
        rows = (
            conn.execute(
                text("SELECT vbm_id, full_name, sex_band, events FROM vbm_athletes WHERE name_norm LIKE :q LIMIT 20"),
                {"q": f"%{norm}%"},
            )
            .mappings()
            .all()
        )
    if not rows:
        found: dict[str, dict[str, Any]] = {}
        for event in _VBM_EVENTS:
            data = _fetch(_VBM_URL, {"action": "jp_bxh_list", "event": event, "page": 1, "per_page": 15, "q": name})
            for row in data.get("data", []):
                if row.get("vbm_id"):
                    found[row["vbm_id"]] = row
        rows = [
            {"vbm_id": k, "full_name": v.get("full_name"), "sex_band": v.get("sex"), "events": {}}
            for k, v in found.items()
        ]
    return [
        {"external_id": r["vbm_id"], "display_name": r["full_name"], "age_group": r.get("sex_band"), "source": "vbm"}
        for r in rows
    ]


def _row_dict(row: Any) -> dict[str, Any]:
    data = dict(row)
    for key, value in data.items():
        if isinstance(value, date | datetime):
            data[key] = value.isoformat()
    return data


def get_claim(claim_id: int, user_id: int | None = None) -> dict[str, Any] | None:
    with engine.connect() as conn:
        row = (
            conn.execute(
                text("SELECT * FROM race_profile_claims WHERE id=:id AND (:uid IS NULL OR user_id=:uid)"),
                {"id": claim_id, "uid": user_id},
            )
            .mappings()
            .first()
        )
    return _row_dict(row) if row else None


def create_claim(user_id: int, source: str, external_id: str) -> dict[str, Any]:
    if source not in ("utmb", "vbm") or not external_id or len(external_id) > 250:
        raise ValueError("Invalid source profile")
    with engine.begin() as conn:
        row = (
            conn.execute(
                text("""
            INSERT INTO race_profile_claims (user_id, source, external_id, display_name)
            VALUES (:uid, :source, :external, :name) RETURNING *
        """),
                {"uid": user_id, "source": source, "external": external_id, "name": external_id},
            )
            .mappings()
            .one()
        )
    return _row_dict(row)


def list_claims(user_id: int) -> list[dict[str, Any]]:
    with engine.connect() as conn:
        rows = (
            conn.execute(
                text("SELECT * FROM race_profile_claims WHERE user_id=:uid ORDER BY created_at DESC"), {"uid": user_id}
            )
            .mappings()
            .all()
        )
    return [_row_dict(r) for r in rows]


def list_results(user_id: int, include_unselected: bool = True) -> list[dict[str, Any]]:
    with engine.connect() as conn:
        rows = (
            conn.execute(
                text("""
            SELECT r.* FROM race_results r WHERE r.user_id=:uid
              AND (:all OR r.selected) ORDER BY r.race_date DESC, r.id DESC
        """),
                {"uid": user_id, "all": include_unselected},
            )
            .mappings()
            .all()
        )
    return [_row_dict(r) for r in rows]


def delete_claim(claim_id: int, user_id: int | None = None) -> bool:
    with engine.begin() as conn:
        result = conn.execute(
            text("DELETE FROM race_profile_claims WHERE id=:id AND (:uid IS NULL OR user_id=:uid)"),
            {"id": claim_id, "uid": user_id},
        )
    return result.rowcount > 0


def queue_refresh(claim_id: int, user_id: int | None = None, hourly_limit: bool = True) -> bool:
    with engine.begin() as conn:
        result = conn.execute(
            text("""
            UPDATE race_profile_claims SET sync_status='pending', sync_error=NULL,
              sync_attempts=0, sync_requested_at=NOW()
            WHERE id=:id AND (:uid IS NULL OR user_id=:uid)
              AND (:unlimited OR last_synced_at IS NULL OR last_synced_at < NOW() - INTERVAL '1 hour')
        """),
            {"id": claim_id, "uid": user_id, "unlimited": not hourly_limit},
        )
    return result.rowcount > 0


def queue_all_claims() -> int:
    with engine.begin() as conn:
        result = conn.execute(
            text("""
            UPDATE race_profile_claims SET sync_status='pending', sync_error=NULL,
              sync_attempts=0, sync_requested_at=NOW()
        """)
        )
    return result.rowcount


def mirror_status() -> dict[str, Any]:
    with engine.connect() as conn:
        row = (
            conn.execute(text("SELECT COUNT(*) AS count, MAX(refreshed_at) AS refreshed_at FROM vbm_athletes"))
            .mappings()
            .one()
        )
    return _row_dict(row)


def set_verified_bib(claim_id: int, user_id: int, bib: str) -> None:
    with engine.begin() as conn:
        conn.execute(
            text("""
            UPDATE race_profile_claims SET meta=jsonb_set(meta, '{verified_bib}', to_jsonb(CAST(:bib AS text)))
            WHERE id=:id AND user_id=:uid AND source='vbm'
        """),
            {"bib": bib, "id": claim_id, "uid": user_id},
        )
    verify_results(user_id)


def create_manual(user_id: int, data: dict[str, Any]) -> dict[str, Any]:
    import uuid

    params = dict(data)
    params.update({"uid": user_id, "key": str(uuid.uuid4()), "raw": "{}"})
    with engine.begin() as conn:
        row = (
            conn.execute(
                text("""
            INSERT INTO race_results (user_id, source, source_key, discipline, race_name, race_date,
              distance_km, elevation_gain_m, finish_time_sec, is_dnf, rank_overall, total_overall, raw)
            VALUES (:uid, 'manual', :key, :discipline, :race_name, :race_date,
              :distance_km, :elevation_gain_m, :finish_time_sec, :is_dnf, :rank_overall, :total_overall, CAST(:raw AS jsonb))
            RETURNING *
        """),
                params,
            )
            .mappings()
            .one()
        )
    return _row_dict(row)


_EDITABLE_IMPORTED = {"selected", "hidden", "user_note"}
_EDITABLE_MANUAL = _EDITABLE_IMPORTED | {
    "discipline",
    "race_name",
    "race_date",
    "distance_km",
    "elevation_gain_m",
    "finish_time_sec",
    "is_dnf",
    "rank_overall",
    "total_overall",
}


def update_result(result_id: int, user_id: int, changes: dict[str, Any]) -> dict[str, Any] | None:
    existing = get_result(result_id, user_id)
    if not existing:
        return None
    allowed = _EDITABLE_MANUAL if existing["source"] == "manual" else _EDITABLE_IMPORTED
    if existing["source"] != "vbm":
        allowed = allowed - {"selected"}
    if not changes or any(key not in allowed for key in changes):
        raise ValueError("Unsupported result field")
    assignments = ", ".join(f"{key}=:{key}" for key in changes)
    with engine.begin() as conn:
        row = (
            conn.execute(
                text(
                    f"UPDATE race_results SET {assignments}, updated_at=NOW() WHERE id=:id AND user_id=:uid RETURNING *"
                ),
                {**changes, "id": result_id, "uid": user_id},
            )
            .mappings()
            .one()
        )
    if "selected" in changes:
        verify_results(user_id)
    return _row_dict(row)


def delete_manual(result_id: int, user_id: int) -> bool:
    with engine.begin() as conn:
        result = conn.execute(
            text("DELETE FROM race_results WHERE id=:id AND user_id=:uid AND source='manual'"),
            {"id": result_id, "uid": user_id},
        )
    return result.rowcount > 0


def get_result(result_id: int, user_id: int) -> dict[str, Any] | None:
    with engine.connect() as conn:
        row = (
            conn.execute(
                text("SELECT * FROM race_results WHERE id=:id AND user_id=:uid"), {"id": result_id, "uid": user_id}
            )
            .mappings()
            .first()
        )
    return _row_dict(row) if row else None


def _upsert_result(conn: Any, claim: dict[str, Any], data: dict[str, Any]) -> None:
    params = {k: data.get(k) for k in _RESULT_COLUMNS if k != "raw"}
    params.update(
        {
            "uid": claim["user_id"],
            "claim": claim["id"],
            "source": claim["source"],
            "raw": json.dumps(data["raw"]),
            "selected": claim["source"] == "utmb",
        }
    )
    conn.execute(
        text("""
        INSERT INTO race_results (user_id, claim_id, source, source_key, discipline, race_name, event_name,
          race_date, country_code, distance_km, elevation_gain_m, utmb_category, finish_time_sec, is_dnf,
          rank_overall, total_overall, rank_gender, total_gender, rank_age_group, total_age_group, bib,
          result_url, source_race_uri, is_pr, raw, selected)
        VALUES (:uid, :claim, :source, :source_key, :discipline, :race_name, :event_name,
          :race_date, :country_code, :distance_km, :elevation_gain_m, :utmb_category, :finish_time_sec, :is_dnf,
          :rank_overall, :total_overall, :rank_gender, :total_gender, :rank_age_group, :total_age_group, :bib,
          :result_url, :source_race_uri, :is_pr, CAST(:raw AS jsonb), :selected)
        ON CONFLICT (claim_id, source_key) DO UPDATE SET
          discipline=EXCLUDED.discipline, race_name=EXCLUDED.race_name, event_name=EXCLUDED.event_name,
          race_date=EXCLUDED.race_date, country_code=EXCLUDED.country_code, distance_km=EXCLUDED.distance_km,
          elevation_gain_m=EXCLUDED.elevation_gain_m, utmb_category=EXCLUDED.utmb_category,
          finish_time_sec=EXCLUDED.finish_time_sec, is_dnf=EXCLUDED.is_dnf,
          rank_overall=EXCLUDED.rank_overall, total_overall=EXCLUDED.total_overall,
          rank_gender=EXCLUDED.rank_gender, total_gender=EXCLUDED.total_gender,
          bib=EXCLUDED.bib, result_url=EXCLUDED.result_url, source_race_uri=EXCLUDED.source_race_uri,
          is_pr=EXCLUDED.is_pr, raw=EXCLUDED.raw, updated_at=NOW()
    """),
        params,
    )


def sync_claim(claim_id: int) -> int:
    claim = get_claim(claim_id)
    if not claim:
        return 0
    source = claim["source"]
    if not getattr(settings, f"RACE_HISTORY_{source.upper()}_ENABLED", True):
        raise ValueError(f"{source} import is disabled")
    with engine.begin() as conn:
        conn.execute(
            text("UPDATE race_profile_claims SET sync_status='pending', sync_attempts=sync_attempts+1 WHERE id=:id"),
            {"id": claim_id},
        )
    try:
        if source == "utmb":
            uri = claim["external_id"]
            if not re.fullmatch(r"[\w.-]{3,250}", uri):
                raise ValueError("Invalid UTMB profile")
            profile = _fetch(f"{_UTMB_URL}/runners/{uri}", {"lang": "en"}, True)
            items: list[dict[str, Any]] = []
            offset = 0
            while offset < 500:
                page = _fetch(
                    f"{_UTMB_URL}/runners/{uri}/results", {"lang": "en", "limit": 100, "offset": offset}, True
                )
                batch = page.get("results") or []
                items.extend(x for raw in batch if (x := normalize_utmb(raw)))
                if len(batch) < 100:
                    break
                offset += 100
                time.sleep(1)
            meta = {
                "ageGroup": profile.get("ageGroup"),
                "sex": profile.get("gender"),
                "indexes": profile.get("performanceIndexes") or [],
                "club": profile.get("club"),
            }
            name = profile.get("fullname") or claim["external_id"]
        else:
            data = _fetch(_VBM_URL, {"action": "jp_bxh_athlete", "vbm_id": claim["external_id"]})
            parents = [
                x for x in data.get("data", []) if str(x.get("event") or "").upper() not in ("TRI70", "TRI140", "IRON")
            ]
            items = []
            for parent in parents:
                candidates = parent.get("other_results_full") or [parent]
                for raw in candidates:
                    if normal := normalize_vbm(parent, raw):
                        items.append(normal)
            meta = {
                "sex_band": parents[0].get("sex") if parents else None,
                "clubs": parents[0].get("clubs") if parents else [],
            }
            name = parents[0].get("full_name") if parents else claim["external_id"]
            if (claim.get("meta") or {}).get("verified_bib"):
                meta["verified_bib"] = claim["meta"]["verified_bib"]
        with engine.begin() as conn:
            for item in items:
                _upsert_result(conn, claim, item)
            conn.execute(
                text("""
                UPDATE race_profile_claims SET display_name=:name, meta=CAST(:meta AS jsonb),
                  sync_status='ok', sync_error=NULL, last_synced_at=NOW() WHERE id=:id
            """),
                {"name": name, "meta": json.dumps(meta), "id": claim_id},
            )
        verify_results(claim["user_id"])
        return len(items)
    except Exception as exc:
        with engine.begin() as conn:
            conn.execute(
                text("UPDATE race_profile_claims SET sync_status='error', sync_error=:error WHERE id=:id"),
                {"error": str(exc)[:500], "id": claim_id},
            )
        raise


def run_pending_claims(limit: int = 20) -> int:
    # The session advisory lock is held across source requests. If a worker
    # dies, Postgres releases it and another process picks up pending claims.
    with engine.connect() as lock_conn:
        if not lock_conn.execute(text("SELECT pg_try_advisory_lock(:key)"), {"key": _WORKER_LOCK_ID}).scalar():
            return 0
        try:
            ids = (
                lock_conn.execute(
                    text("""
                SELECT id FROM race_profile_claims WHERE sync_status='pending'
                  OR (sync_status='error' AND sync_attempts < 3 AND sync_requested_at < NOW() - INTERVAL '10 minutes')
                ORDER BY sync_requested_at LIMIT :limit
            """),
                    {"limit": limit},
                )
                .scalars()
                .all()
            )
            for claim_id in ids:
                try:
                    sync_claim(claim_id)
                except Exception:
                    logger.exception("race claim sync failed", extra={"claim_id": claim_id})
            return len(ids)
        finally:
            lock_conn.execute(text("SELECT pg_advisory_unlock(:key)"), {"key": _WORKER_LOCK_ID})


def run_worker(stop_event: Any) -> None:
    """Process-local scheduler; durable state and advisory lock live in Postgres."""
    while not stop_event.is_set():
        try:
            run_pending_claims()
            if settings.RACE_HISTORY_WEEKLY_REFRESH_ENABLED:
                with engine.connect() as lock_conn:
                    key = _WORKER_LOCK_ID + 1
                    if lock_conn.execute(text("SELECT pg_try_advisory_lock(:key)"), {"key": key}).scalar():
                        try:
                            due = lock_conn.execute(
                                text("""
                                SELECT NOT EXISTS (
                                  SELECT 1 FROM vbm_athletes WHERE refreshed_at > NOW() - INTERVAL '7 days'
                                )
                            """)
                            ).scalar()
                            if due:
                                refresh_vbm_mirror()
                                queue_all_claims()
                        finally:
                            lock_conn.execute(text("SELECT pg_advisory_unlock(:key)"), {"key": key})
        except Exception:
            logger.exception("race history worker failed")
        stop_event.wait(60)


def refresh_vbm_mirror() -> int:
    count = 0
    for event in _VBM_EVENTS:
        page = 1
        while True:
            data = _fetch(_VBM_URL, {"action": "jp_bxh_list", "event": event, "page": page, "per_page": 500, "q": ""})
            rows = data.get("data") or []
            with engine.begin() as conn:
                for row in rows:
                    if not row.get("vbm_id"):
                        continue
                    conn.execute(
                        text("""
                        INSERT INTO vbm_athletes (vbm_id, full_name, name_norm, sex_band, events, clubs)
                        VALUES (:id, :name, :norm, :sex, CAST(:events AS jsonb), CAST(:clubs AS jsonb))
                        ON CONFLICT (vbm_id) DO UPDATE SET full_name=EXCLUDED.full_name,
                          name_norm=EXCLUDED.name_norm, sex_band=EXCLUDED.sex_band,
                          events=vbm_athletes.events || EXCLUDED.events, clubs=EXCLUDED.clubs,
                          refreshed_at=NOW()
                    """),
                        {
                            "id": row["vbm_id"],
                            "name": row.get("full_name") or row["vbm_id"],
                            "norm": normalize_name(row.get("full_name") or row["vbm_id"]),
                            "sex": row.get("sex"),
                            "events": json.dumps({str(row.get("event")): row}),
                            "clubs": json.dumps(row.get("clubs") or []),
                        },
                    )
                    count += 1
            if not rows or page >= int(data.get("total_pages") or 1):
                break
            page += 1
            time.sleep(1)
    return count


def verify_results(user_id: int) -> None:
    with engine.begin() as conn:
        claim_rows = (
            conn.execute(text("SELECT id, meta FROM race_profile_claims WHERE user_id=:uid"), {"uid": user_id})
            .mappings()
            .all()
        )
        verified_bibs = {row["id"]: (row["meta"] or {}).get("verified_bib") for row in claim_rows}
        results = (
            conn.execute(text("SELECT * FROM race_results WHERE user_id=:uid AND selected"), {"uid": user_id})
            .mappings()
            .all()
        )
        for result in results:
            methods: set[str] = set()
            if result["source"] == "vbm" and result["bib"] and result["bib"] == verified_bibs.get(result["claim_id"]):
                methods.add("bib")
            activity_id = None
            if not result["is_dnf"] and result["finish_time_sec"]:
                tolerance = 0.10 if result["discipline"] == "road" else 0.15
                activity_id = conn.execute(
                    text("""
                    SELECT id FROM activities WHERE user_id=:uid AND source_provider='coros'
                      AND start_time::date BETWEEN :day - 1 AND :day + 1
                      AND distance_km BETWEEN :min_dist AND :max_dist
                      AND ABS(duration_seconds - :duration) <= :duration * 0.05
                    ORDER BY ABS(duration_seconds - :duration) LIMIT 1
                """),
                    {
                        "uid": user_id,
                        "day": result["race_date"],
                        "min_dist": result["distance_km"] * (1 - tolerance),
                        "max_dist": result["distance_km"] * (1 + tolerance),
                        "duration": result["finish_time_sec"],
                    },
                ).scalar()
            if activity_id:
                methods.add("coros")
            else:
                methods.discard("coros")
            conn.execute(
                text("""
                UPDATE race_results SET verified=:verified, verification_methods=:methods,
                  matched_activity_id=:activity WHERE id=:id
            """),
                {"verified": bool(methods), "methods": sorted(methods), "activity": activity_id, "id": result["id"]},
            )
        conn.execute(
            text("""
            UPDATE race_results SET verified=FALSE, verification_methods='{}', matched_activity_id=NULL
            WHERE user_id=:uid AND NOT selected
        """),
            {"uid": user_id},
        )
        conn.execute(
            text("""
            UPDATE race_profile_claims c SET verified=EXISTS(
                SELECT 1 FROM race_results r WHERE r.claim_id=c.id AND r.selected AND r.verified),
              verification_methods=ARRAY(
                SELECT DISTINCT unnest(r.verification_methods) FROM race_results r
                WHERE r.claim_id=c.id AND r.selected)
            WHERE c.user_id=:uid
        """),
            {"uid": user_id},
        )


def _dedupe(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in sorted(results, key=lambda r: (r["source"] == "manual", r.get("elevation_gain_m") is None)):
        key = (row["race_date"], round(row["distance_km"], 1), row["finish_time_sec"], row["is_dnf"])
        row_tokens = set(normalize_name(row["race_name"]).split())
        duplicate = any(
            key == (other["race_date"], round(other["distance_km"], 1), other["finish_time_sec"], other["is_dnf"])
            and len(row_tokens & set(normalize_name(other["race_name"]).split()))
            / max(1, len(row_tokens | set(normalize_name(other["race_name"]).split())))
            >= 0.5
            for other in output
        )
        if not duplicate:
            output.append(row)
    return sorted(output, key=lambda r: r["race_date"], reverse=True)


def build_summary(user_id: int, as_of: date | None = None, prompt: bool = False) -> dict[str, Any]:
    today = as_of or date.today()
    rows = _dedupe([r for r in list_results(user_id, False) if not (prompt and r["hidden"])])
    finished = [r for r in rows if not r["is_dnf"] and r["finish_time_sec"]]
    trail = [r for r in finished if r["discipline"] == "trail"]
    road = [r for r in finished if r["discipline"] == "road"]

    def road_pr(km: float) -> dict[str, Any] | None:
        candidates = [r for r in road if abs(r["distance_km"] - km) < 0.5]
        if not candidates:
            return None
        best = min(candidates, key=lambda r: r["finish_time_sec"])
        return {
            "result_id": best["id"],
            "time_sec": best["finish_time_sec"],
            "date": best["race_date"],
            "stale": (today - date.fromisoformat(best["race_date"])).days > 730,
        }

    return {
        "trail_finishes": len(trail),
        "trail_dnfs": sum(r["discipline"] == "trail" and r["is_dnf"] for r in rows),
        "ultras": sum(r["distance_km"] > 42.195 for r in trail),
        "longest_finish": max(trail, key=lambda r: r["distance_km"], default=None),
        "road_hm_pr": road_pr(21.0975),
        "road_fm_pr": road_pr(42.195),
        "last_race_date": rows[0]["race_date"] if rows else None,
        "races_12m": sum((today - date.fromisoformat(r["race_date"])).days <= 365 for r in rows),
        "recent": rows[:8],
    }


def prompt_summary(user_id: int, lang: str = "en") -> str:
    summary = build_summary(user_id, prompt=True)
    rows = summary["recent"]
    if not rows:
        return ""
    title = "RACE HISTORY" if lang != "vi" else "LỊCH SỬ RACE"
    lines = [title]
    if any(row["source"] == "vbm" for row in rows):
        lines.append("VBM includes qualifying results only." if lang != "vi" else "VBM chỉ gồm kết quả đạt chuẩn.")
    for row in rows:
        label = "self-reported" if row["source"] == "manual" else row["source"].upper()
        time_label = (
            "DNF" if row["is_dnf"] else f"{row['finish_time_sec'] // 3600}:{row['finish_time_sec'] % 3600 // 60:02d}"
        )
        note = f" ({row['user_note'][:80]})" if row.get("user_note") else ""
        lines.append(
            f"{row['race_date']} {row['race_name'][:60]} {row['distance_km']:.1f}km {time_label} [{label}]{note}"
        )
    return "\n".join(lines)[:800]


def tier_distance(user_id: int) -> float | None:
    since = date.today() - timedelta(days=1095)
    rows = _dedupe(
        [
            r
            for r in list_results(user_id, False)
            if r["source"] != "manual" and not r["is_dnf"] and r["race_date"] >= since.isoformat()
        ]
    )
    return max((r["distance_km"] for r in rows), default=None)


def scenarios(user_id: int, plan_id: int | None = None) -> dict[str, Any]:
    from services.race_estimator import IMPROVEMENT_CAP, IMPROVEMENT_PER_WEEK, RaceEstimator

    with engine.connect() as conn:
        plan = (
            conn.execute(
                text("""
            SELECT id, race_name, race_date, course_distance_km, course_elevation_gain_m, total_weeks,
              prediction FROM plans WHERE user_id=:uid AND
              ((:plan_id IS NOT NULL AND id=:plan_id) OR (:plan_id IS NULL AND plan_status='active'))
            ORDER BY created_at DESC LIMIT 1
        """),
                {"uid": user_id, "plan_id": plan_id},
            )
            .mappings()
            .first()
        )
    if not plan:
        return {}
    summary = build_summary(user_id)
    trail = [r for r in _dedupe(list_results(user_id, False)) if r["discipline"] == "trail" and r["finish_time_sec"]]
    target = None
    if trail and plan["course_distance_km"]:
        ref = min(trail, key=lambda r: abs(r["distance_km"] - plan["course_distance_km"]))
        target = RaceEstimator.estimate(
            distance_km=plan["course_distance_km"],
            elevation_gain_m=plan["course_elevation_gain_m"] or 0,
            reference={
                "distance_km": ref["distance_km"],
                "elevation_gain_m": ref["elevation_gain_m"] or 0,
                "finish_time_mins": ref["finish_time_sec"] / 60,
            },
            weeks_to_race=plan["total_weeks"],
        )
        target["baseline_result_id"] = ref["id"]
    improvement = min(IMPROVEMENT_CAP, plan["total_weeks"] * IMPROVEMENT_PER_WEEK)
    road = {}
    for label, key in (("hm", "road_hm_pr"), ("fm", "road_fm_pr")):
        pr = summary[key]
        if pr and not pr["stale"]:
            road[label] = {
                "baseline_sec": pr["time_sec"],
                "scenario_sec": round(pr["time_sec"] * (1 - improvement)),
                "baseline_result_id": pr["result_id"],
            }
    return {
        "plan_id": plan["id"],
        "weeks": plan["total_weeks"],
        "improvement_pct": round(improvement * 100, 1),
        "target": target,
        "road": road,
        "stored": plan["prediction"],
    }


def store_plan_scenario(user_id: int, plan_id: int) -> None:
    snapshot = scenarios(user_id, plan_id)
    if not snapshot or not (snapshot.get("target") or snapshot.get("road")):
        return
    snapshot.pop("stored", None)
    snapshot["created_at"] = datetime.now(UTC).isoformat()
    baseline_id = (snapshot.get("target") or {}).get("baseline_result_id")
    if baseline_id:
        baseline = get_result(baseline_id, user_id)
        snapshot["baseline"] = {
            k: baseline[k] for k in ("race_date", "distance_km", "elevation_gain_m", "finish_time_sec")
        }
    with engine.begin() as conn:
        conn.execute(
            text("UPDATE plans SET prediction=CAST(:data AS jsonb) WHERE id=:id AND user_id=:uid"),
            {"data": json.dumps(snapshot), "id": plan_id, "uid": user_id},
        )
