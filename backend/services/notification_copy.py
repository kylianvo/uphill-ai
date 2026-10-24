"""Reviewed bilingual templates; workout facts always come from current data."""


def render_notification(candidate, context):
    vi = context["preferences"].get("language") == "vi"
    if candidate["kind"] == "workout":
        workout = next(w for w in context["workouts"] if w["id"] == candidate["source"]["workout_id"])
        details = [workout.get("title") or ("Buổi tập hôm nay" if vi else "Today's workout")]
        if workout.get("duration_minutes"):
            details.append(f"{workout['duration_minutes']:g} " + ("phút" if vi else "min"))
        if workout.get("target_zone"):
            details.append(workout["target_zone"])
        if workout.get("distance_km"):
            miles = context["preferences"].get("distance_unit") == "mi"
            distance = workout["distance_km"] / 1.609344 if miles else workout["distance_km"]
            details.append(f"{distance:g} {'mi' if miles else 'km'}" if not miles else f"{distance:.1f} mi")
        return ("Buổi tập hôm nay" if vi else "Today's workout", " · ".join(details))
    kind = candidate["kind"]
    copy = {
        "planning": (
            "Plan next week",
            "Review your availability and build your next training block.",
            "Lên plan tuần tới",
            "Xem lịch rảnh và tạo block tập tiếp theo.",
        ),
        "unlogged": (
            "Check in on your training",
            "A couple of sessions are still unlogged. Log them or adjust your plan.",
            "Xem lại lịch tập",
            "Vài buổi tập chưa được ghi lại. Bạn có thể cập nhật hoặc chỉnh plan.",
        ),
        "recovery": (
            "How did that run feel?",
            "Log your effort and how you feel after your priority run.",
            "Buổi chạy vừa rồi thế nào?",
            "Ghi lại RPE và cảm nhận sau buổi chạy quan trọng.",
        ),
        "checklist": (
            "Make your plan more personal",
            "Add one missing detail to help your next plan fit you better.",
            "Plan sát với bạn hơn",
            "Bổ sung một thông tin để plan tiếp theo sát với bạn hơn.",
        ),
    }
    if kind in copy:
        en_title, en_body, vi_title, vi_body = copy[kind]
        return (vi_title, vi_body) if vi else (en_title, en_body)
    if kind in ("knowledge", "taper", "race"):
        card = next(c for c in context["cards"] if c["id"] == candidate["source"]["card_id"])
        return card.get("chapter_title") or ("Kiến thức chạy bộ" if vi else "Training insight"), (
            card.get("summary") or ""
        )[:240]
    return (
        "Plan đã sẵn sàng" if vi else "Your plan is ready",
        "Xem lịch tập mới của bạn." if vi else "Take a look at your new training plan.",
    )
