"""Curated training mountains and their long-run climbing rates."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Mountain:
    key: str
    area: str
    name_en: str
    name_vi: str
    climb_rate: float
    repeats_only: bool
    default_min_minutes: int | None


# Sources: Viet's Núi Dinh/Chứa Chan/Châu Thới data, Bà Đen/Hàm Lợn routes, and Dalat/VMM seeds.
MOUNTAINS: dict[str, Mountain] = {
    "nui_dinh": Mountain("nui_dinh", "hcmc", "Núi Dinh", "Núi Dinh", 60, False, 180),
    "chau_thoi": Mountain("chau_thoi", "hcmc", "Núi Châu Thới", "Núi Châu Thới", 28, False, 180),
    "chua_chan": Mountain("chua_chan", "hcmc", "Núi Chứa Chan", "Núi Chứa Chan", 85, False, 180),
    "ba_den": Mountain("ba_den", "hcmc", "Núi Bà Đen", "Núi Bà Đen", 176, True, 180),
    "ham_lon": Mountain("ham_lon", "hanoi", "Núi Hàm Lợn", "Núi Hàm Lợn", 45, False, 180),
    "dalat": Mountain("dalat", "dalat", "Dalat trails", "Trail Đà Lạt", 47, False, None),
    "sapa": Mountain("sapa", "sapa", "Sapa trails", "Trail Sa Pa", 56, False, None),
}


def long_run_climb_rate(key: str | None) -> float | None:
    mountain = MOUNTAINS.get(key)
    if mountain is None:
        return None
    if mountain.repeats_only:
        return MOUNTAINS["nui_dinh"].climb_rate
    return mountain.climb_rate


def default_min_minutes(key: str | None) -> int | None:
    mountain = MOUNTAINS.get(key)
    return mountain.default_min_minutes if mountain else None
