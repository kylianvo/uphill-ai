"""Coach Quang's rules (2026-10-22) for ultras trained on a weekly mountain day (Núi Dinh): a fixed long-run ladder
in hours, longer weekday runs, and quality sessions only in the final 8 weeks before the taper. They deviate from
the book's 4-5 h session ceiling, 25% long-run share and 7-10% weekly growth on purpose; the spec records why
(docs/superpowers/specs/2026-10-23-ultra-rules-design.md). Pure functions, no I/O."""

from collections.abc import Sequence
from typing import Literal

from services.athlete_tier import taper_shift, taper_weeks

Band = Literal["50k", "100k", "100mi"]

LONG_SHARE_CAP = 0.60
STEP_CAP_MIN = 60  # a ladder week is never more than an hour above the last two weeks' longest run
QUALITY_MAX_MIN = 90
QUALITY_WINDOW_WEEKS = 8
ME_FREE_LONG_RUN_MIN = 360
ME_MAX_SHARE = 0.10
ELITE_DOSE_WEEK_MIN = 900  # the 2 x 40-60 min Zone 3 dose needs an elite engine AND 15-20+ h weeks (KB 2026-10-25)
ZONE3_SHARE = 0.09  # 100 km runners keep Zone 3 at 7-9% of weekly time (KB)

# (start steps, filler, end steps ending at the peak, recovery-week long run), in minutes
_LADDERS: dict[tuple[Band, bool], tuple[list[int], int, list[int], int]] = {
    ("50k", False): ([180, 180, 180, 180], 240, [270, 300], 180),
    ("100k", False): ([180, 180, 240, 240], 300, [360, 420], 240),
    ("100mi", False): ([180, 180, 240, 240], 300, [360, 420], 240),
    ("100mi", True): ([180, 180, 240, 240], 300, [360, 420, 480], 240),
}


def band_for(km: float | None) -> Band | None:
    """Bands start about 10% below the round number, so a 98 km "100K" gets the 100 km rules."""
    if not km or km < 45:
        return None
    return "50k" if km < 90 else "100k" if km < 140 else "100mi"


def applies(km: float | None, mountain_days: Sequence[str]) -> Band | None:
    return band_for(km) if mountain_days else None


def is_advanced(tier_key: str) -> bool:
    return tier_key in ("sub_elite", "elite")


def session_cap(band: Band, advanced: bool) -> int:
    return {"50k": 300, "100k": 420}.get(band, 480 if advanced else 420)


def weekday_minutes(band: Band, advanced: bool) -> tuple[int, int]:
    if band == "50k":
        return (45, 90)
    return (60, 150) if band == "100mi" and advanced else (60, 90)


def quality_dose(advanced: bool, gated: bool, week_minutes: float) -> tuple[int, int, int]:
    """(sessions, reps, minutes per rep) of Zone 3 for a week in the window. The double dose needs an ungated elite
    and a 15 h+ week; reps then drop (to 2 at least, the 20 min minimum) until Zone 3 is <= 9% of the week."""
    elite = advanced and not gated and week_minutes >= ELITE_DOSE_WEEK_MIN
    n, reps, rep = (2, 4, 12) if elite else (1, 3, 10)
    while reps > 2 and n * reps * rep > ZONE3_SHARE * week_minutes:
        reps -= 1
    return n, reps, rep


def quality_per_week(advanced: bool, gated: bool) -> int:
    return 2 if advanced and not gated else 1


def quality_work_minutes(advanced: bool, gated: bool) -> tuple[int, int]:
    return (40, 60) if advanced and not gated else (20, 30)


def other_day_minutes(long_run_min: float) -> int:
    """The weekend day that is not the mountain day: shorter after a longer mountain day."""
    return 90 if long_run_min <= 240 else 60 if long_run_min <= 300 else 45


def peak_week(total_weeks: int) -> int:
    """The last build week, as in goal_demands.long_run_ask."""
    return total_weeks - 3 - taper_shift(total_weeks)


def is_deload(week: int, total_weeks: int) -> bool:
    """Same rule as PlanGenerator.is_deload_week (kept here to avoid an import cycle; a test pins the two)."""
    last_build = total_weeks - 3 - (taper_weeks(total_weeks) - 1)
    return week > 1 and week % 4 == 0 and week < last_build


def ladder(band: Band, advanced: bool, total_weeks: int) -> dict[int, int]:
    start, filler, end, recovery = _LADDERS[(band, advanced and band == "100mi")]
    peak = peak_week(total_weeks)
    n = sum(1 for w in range(1, peak + 1) if not is_deload(w, total_weeks))
    steps = start + end
    seq = start + [filler] * (n - len(steps)) + end if n >= len(steps) else steps[-n:] if n > 0 else []
    out: dict[int, int] = {}
    it = iter(seq)
    for w in range(1, peak + 1):
        out[w] = recovery if is_deload(w, total_weeks) else next(it)
    return out


def long_run_target(
    band: Band, advanced: bool, week: int, total_weeks: int, recent_longest: float | None
) -> int | None:
    target = ladder(band, advanced, total_weeks).get(week)
    if target is None:
        return None
    return int(min(target, recent_longest + STEP_CAP_MIN)) if recent_longest else target


def quality_weeks(total_weeks: int) -> frozenset[int]:
    peak = peak_week(total_weeks)
    return frozenset(
        w for w in range(max(1, peak - QUALITY_WINDOW_WEEKS + 1), peak + 1) if not is_deload(w, total_weeks)
    )


def prompt_block(
    band: Band, advanced: bool, weeks: dict[int, int], total_weeks: int, aet_gated: bool, lang: str
) -> str:
    """Rule lines for the generator: this block's ladder long runs and quality sessions. Technical terms stay in
    English in Vietnamese, like goal_demands.prompt_block."""
    lo, hi = weekday_minutes(band, advanced)
    n = quality_per_week(advanced, aet_gated)
    work_lo, work_hi = quality_work_minutes(advanced, aet_gated)
    window = quality_weeks(total_weeks)
    vi = lang == "vi"
    lines = [
        "MOUNTAIN-DAY ULTRA RULES (coach's ladder; they override the long-run share and growth rules):"
        if not vi
        else "LUẬT ULTRA CÓ NGÀY LÊN NÚI (ladder của coach; thay cho luật tỉ lệ và tăng trưởng Long Run):"
    ]
    for week, minutes in sorted(weeks.items()):
        other = other_day_minutes(minutes)
        if week in window:
            quality = (
                f"{n} session{'s' if n > 1 else ''} a week of uphill or rolling intervals in Zone 3 ({work_lo}-{work_hi} min "
                f"of work, 8-12% treadmill, stairs or an overpass where there are no hills; breathing-limited, never "
                f"ME; no Zone 4; at most {QUALITY_MAX_MIN} min in all; 48 h from the long run and ME)"
                if not vi
                else f"{n} buổi interval leo dốc hoặc lên xuống Zone 3 ({work_lo}-{work_hi} phút làm việc; máy chạy "
                f"8-12%, cầu thang hoặc cầu vượt nếu không có dốc; giới hạn bởi hơi thở, không phải ME; không Zone 4; "
                f"tối đa {QUALITY_MAX_MIN} phút cả buổi; cách Long Run và ME 48 h)"
            )
        else:
            quality = (
                "no Zone 3+ sessions: hill sprints, strides and ME only"
                if not vi
                else "không có buổi Zone 3+: chỉ hill sprints, strides và ME"
            )
        lines.append(
            f"- Week {week}: Long Run {minutes} min on the mountain day; the other weekend day at most {other} min "
            f"easy; {quality}."
            if not vi
            else f"- Tuần {week}: Long Run {minutes} phút vào ngày lên núi; ngày cuối tuần còn lại tối đa {other} "
            f"phút nhẹ; {quality}."
        )
    lines.append(
        f"Weekday easy runs {lo}-{hi} min; extra volume goes on weekdays, never on the long run. No back-to-back "
        f"weekend. No ME in a week with a Long Run of {ME_FREE_LONG_RUN_MIN // 60} h or more."
        if not vi
        else f"Easy run ngày thường {lo}-{hi} phút; khối lượng thêm đặt vào ngày thường, không cộng vào Long Run. "
        f"Không chạy back-to-back cuối tuần. Không tập ME trong tuần có Long Run từ {ME_FREE_LONG_RUN_MIN // 60} h trở lên."
    )
    return "\n".join(lines)
