"""Reviewed bilingual templates; every number comes from the athlete's current data (spec 2026-10-24)."""

import math
from zoneinfo import ZoneInfo

from services.notification_rules import actionable, dated_workouts

# (en, vi). VI follows .claude/skills/uphill-ai-vietnamese-copy: English running terms, no exclamation marks.
PURPOSE = {
    "taper": ("Taper week: less is more. Stay fresh.", "Tuần Taper: tập ít lại để giữ sức."),
    "easy": (
        "Keep it truly easy. This is the base everything else stands on.",
        "Chạy thật nhẹ. Đây là nền cho mọi buổi khác.",
    ),
    "long": (
        "Time on feet for {race}. Easy is the point.",
        "Tích lũy thời gian trên chân cho {race}. Chạy nhẹ là đúng.",
    ),
    "quality": (
        "Today's key session. Warm up well, hit the targets, no more.",
        "Buổi chính của tuần. Warm-up kỹ, chạy đúng target, không hơn.",
    ),
    "hill": ("Climbing strength for {race}'s {d_plus} m D+.", "Sức leo cho {d_plus} m D+ của {race}."),
    "hill_plain": ("Climbing strength for race day.", "Sức leo cho ngày race."),
    "strength": ("Strong legs hold your form late in the race.", "Chân khỏe giữ được form ở cuối race."),
}

TEMPLATES = {
    "race_day": ("race day", "ngày race"),
    "todays_workout": ("Today's workout", "Buổi tập hôm nay"),
    "in_your_plan": ("Today's session is in your plan.", "Buổi tập hôm nay có trong plan."),
    "brief_title": ("Week {n} of {total}: {phase}", "Tuần {n}/{total}: {phase}"),
    "brief_title_plain": ("Week {n}", "Tuần {n}"),
    "brief_body": ("{count} sessions, {hours} h.", "{count} buổi, {hours} giờ."),
    "brief_key": ("Key session: {title} on {weekday}.", "Buổi chính: {title} ({weekday})."),
    "brief_today": ("Today: {title}, {duration}.", "Hôm nay: {title}, {duration}."),
    "recognition_title": ("Nice work on {title}", "Hoàn thành tốt {title}"),
    "recognition_title_plain": ("Nice work today", "Hoàn thành tốt buổi hôm nay"),
    "recognition_facts": (
        "{distance} km and {d_plus} m D+ in {duration}.",
        "{distance} km, {d_plus} m D+ trong {duration}.",
    ),
    "recognition_facts_flat": ("{distance} km in {duration}.", "{distance} km trong {duration}."),
    "climb": ("Your biggest climb of this plan so far.", "Leo nhiều nhất từ đầu plan."),
    "longest": ("Your longest run of this plan so far.", "Bài chạy dài nhất từ đầu plan."),
    "log_it": ("Tap to log how it felt.", "Chạm để ghi RPE."),
    "missed_title": ("Missed {weekday}'s {title}?", "Lỡ buổi {title} hôm {weekday}?"),
    "missed_title_plain": ("Missed a session?", "Lỡ một buổi tập?"),
    "missed_body": ("No stress. Tap to adjust this week around it.", "Không sao. Chạm để chỉnh lại tuần này."),
    "planning": ("Plan next week", "Lên plan tuần tới"),
    "planning_body": (
        "Your next week is empty. Tap to build it in a minute.",
        "Tuần tới chưa có buổi nào. Chạm để tạo trong một phút.",
    ),
    "checklist": ("Make your plan more personal", "Plan sát với bạn hơn"),
    "checklist_body": (
        "Add one missing detail to help your next plan fit you better.",
        "Bổ sung một thông tin để plan tiếp theo sát với bạn hơn.",
    ),
    "insight": ("Training insight", "Kiến thức chạy bộ"),
    "plan_ready": ("Your plan is ready", "Plan đã sẵn sàng"),
    "plan_ready_body": ("Tap to see your new week.", "Chạm để xem tuần mới."),
}

WEEKDAYS_VI = {
    "Monday": "Thứ Hai",
    "Tuesday": "Thứ Ba",
    "Wednesday": "Thứ Tư",
    "Thursday": "Thứ Năm",
    "Friday": "Thứ Sáu",
    "Saturday": "Thứ Bảy",
    "Sunday": "Chủ Nhật",
}


def family(workout):
    kind = (workout.get("type") or "").lower()
    if "taper" in (workout.get("phase") or "").lower():
        return "taper"
    if kind in ("easy", "easy run", "recovery", "recovery run"):
        return "easy"
    if kind == "long run":
        return "long"
    if kind in ("tempo", "threshold", "interval", "intervals", "fartlek"):
        return "quality"
    if "hill" in kind or "climb" in kind:
        return "hill"
    if kind in ("strength", "me", "muscular endurance"):
        return "strength"
    return None


def minutes_text(minutes, vi):
    minutes = int(round(minutes))
    if minutes >= 60:
        return f"{minutes // 60}h{minutes % 60:02d}"
    return f"{minutes} {'phút' if vi else 'min'}"


def render_notification(candidate, context):
    vi = context["preferences"].get("language") == "vi"

    def t(key, **values):
        return TEMPLATES[key][vi].format(**values)

    plan = context.get("plan") or {}
    workouts = {w["id"]: w for w in context.get("workouts") or []}
    source = candidate.get("source") or {}

    def weekday(w):
        return WEEKDAYS_VI.get(w["day_of_week"], w["day_of_week"]) if vi else w["day_of_week"]

    kind = candidate["kind"]

    if kind == "workout":
        w = workouts[source["workout_id"]]
        facts = []
        if w.get("duration_minutes"):
            facts.append(f"{w['duration_minutes']:g} " + ("phút" if vi else "min"))
        if w.get("target_zone"):
            facts.append(w["target_zone"])
        if w.get("distance_km"):
            miles = context["preferences"].get("distance_unit") == "mi"
            facts.append(f"{w['distance_km'] / 1.609344:.1f} mi" if miles else f"{w['distance_km']:g} km")
        purpose = ""
        fam = family(w)
        race = plan.get("race_name") or t("race_day")
        if fam == "hill" and not (plan.get("race_name") and plan.get("course_elevation_gain_m")):
            purpose = PURPOSE["hill_plain"][vi]
        elif fam:
            purpose = PURPOSE[fam][vi].format(race=race, d_plus=f"{plan.get('course_elevation_gain_m') or 0:g}")
        body = " ".join(part for part in (" · ".join(facts) + "." if facts else "", purpose) if part)
        return w.get("title") or t("todays_workout"), body or t("in_your_plan")

    if kind == "week_brief":
        n = source["week_number"]
        week = [w for w in context.get("workouts") or [] if w["week_number"] == n and actionable(w)]
        phase = next((w["phase"] for w in week if w.get("phase")), None)
        title = (
            t("brief_title", n=n, total=plan["total_weeks"], phase=phase)
            if phase and plan.get("total_weeks")
            else t("brief_title_plain", n=n)
        )
        hours = math.floor(sum(w.get("duration_minutes") or 0 for w in week) / 60 * 2 + 0.5) / 2
        parts = [t("brief_body", count=len(week), hours=f"{hours:g}")]
        key = max(week, key=lambda w: (bool(w.get("is_priority")), w.get("duration_minutes") or 0), default=None)
        if key and key.get("title"):
            parts.append(t("brief_key", title=key["title"], weekday=weekday(key)))
        if candidate.get("due_at") and context["preferences"].get("timezone"):
            today = candidate["due_at"].astimezone(ZoneInfo(context["preferences"]["timezone"])).date()
            now_w = next(
                (w for w, d in dated_workouts(context) if d == today and actionable(w) and w.get("title")), None
            )
            if now_w:
                parts.append(
                    t("brief_today", title=now_w["title"], duration=minutes_text(now_w["duration_minutes"], vi))
                )
        return title, " ".join(parts)

    if kind == "recognition":
        w = workouts.get(source["workout_id"]) or {}
        acts = context.get("activities") or []
        a = next(x for x in acts if x["id"] == source["activity_id"])
        title = t("recognition_title", title=w["title"]) if w.get("title") else t("recognition_title_plain")
        duration = minutes_text((a.get("duration_seconds") or 0) / 60, vi)
        distance = f"{a.get('distance_km') or 0:g}"
        if a.get("elevation_gain_m"):
            parts = [t("recognition_facts", distance=distance, d_plus=f"{a['elevation_gain_m']:g}", duration=duration)]
        else:
            parts = [t("recognition_facts_flat", distance=distance, duration=duration)]
        mine = [x for x in acts if x.get("matched_workout_id") in workouts]
        if a.get("elevation_gain_m") and a["elevation_gain_m"] >= max(x.get("elevation_gain_m") or 0 for x in mine):
            parts.append(t("climb"))
        elif (a.get("distance_km") or 0) >= max(x.get("distance_km") or 0 for x in mine) > 0:
            parts.append(t("longest"))
        parts.append(t("log_it"))
        return title, " ".join(parts)

    if kind == "unlogged":
        w = workouts.get(source.get("workout_id"))
        title = (
            t("missed_title", weekday=weekday(w), title=w["title"]) if w and w.get("title") else t("missed_title_plain")
        )
        return title, t("missed_body")

    if kind in ("planning", "checklist"):
        return t(kind), t(f"{kind}_body")

    if kind in ("knowledge", "taper", "race"):
        card = next(c for c in context["cards"] if c["id"] == source["card_id"])
        return card.get("chapter_title") or t("insight"), (card.get("summary") or "")[:240]

    return t("plan_ready"), t("plan_ready_body")
