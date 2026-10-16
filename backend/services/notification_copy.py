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
    return (
        "Plan đã sẵn sàng" if vi else "Your plan is ready",
        "Xem lịch tập mới của bạn." if vi else "Take a look at your new training plan.",
    )
