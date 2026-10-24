# Notification content v2: one switch, coach-voiced, rarely

Date: 2026-10-24 (Australia/Sydney)
Status: Draft for review. Builds on `2026-10-16-ios-notifications-design.md` (PR #143, live for allowlisted accounts). Depends on PR #189 (tap crash fix).

## Why

The seven notifications shipped in #143 are correct but read like a to-do app. The workout reminder is a spec sheet, three others are chores ("log", "fill in", "plan"), and none says why a session matters or notices good work. Athletes keep notifications that sound like their coach and switch off the ones that nag. The settings screen also asks too much: three category toggles, four time pickers and a units picker.

Goal: fewer settings, warmer copy, and a hard budget so the app never becomes noise.

## Decisions

1. **One switch.** Settings shows "Notifications" (on/off), "Pause for a week", and a list of anything muted. We decide what is sent and when.
2. **"Less like this" on the notification.** Long-pressing a coaching notification offers it. It mutes that kind for that account. Workout reminders and requested results don't have it; the main switch covers those.
3. **We choose the times**, learned from when the athlete actually runs.
4. **No model call per notification.** Every sentence is a reviewed template filled with numbers from the athlete's own data. The existing week brief (AI-written) is where a Monday push leads, not its text.

## Budget and anti-nag rules

| Rule | Detail |
|---|---|
| Daily | At most 1 proactive notification per local day (existing rule, kept). |
| Weekly | New: at most 4 proactive in any 7 days. Requested results (plan ready) don't count. |
| Rest days | No proactive notification on a day with no workout, except the Monday brief and Sunday planning. |
| Back-off | New: when 3 notifications of one coaching kind in a row are delivered but not opened, skip that kind for 14 days. Workout reminders are exempt: people read them on the lock screen without tapping. |
| Mute | "Less like this" adds the kind to `muted_kinds`. Removable from settings. |
| Priority | When several are due the same day, keep the existing order: race > planning > missed session > taper > recognition > workout > checklist > knowledge. The Monday brief sits just above the workout reminder and absorbs it (see B). |

## Timing

- **Workout reminder**: 75 minutes before the athlete's usual start. "Usual" = median local start time of their activities in the last 28 days, computed separately for weekdays and weekends from `activities.start_time`, needing at least 4 activities in the group. Clamp to 06:00–20:00 and to outside quiet hours. Fallback: 07:00.
- **Monday brief**: 07:30 local.
- **Sunday planning, missed session, checklist, knowledge**: 18:00 local.
- **Recognition**: first allowed minute at least 30 minutes after the activity syncs, within 24 hours.
- **Quiet hours**: fixed 21:00–07:00. No longer user-editable.

The stored `workout_time`, `coaching_time` and quiet-hour columns stay (back-compat, existing tests) but are no longer written by the app; the server ignores them in favour of the rules above.

## Content

Placeholders come from current data at send time. Any value that is missing drops its clause; a message never shows an empty slot. Copy follows the repo's Vietnamese-copy rules: English running terms stay English, `bạn`, no exclamation marks, VI no longer than EN.

### A. Today's workout (rewrite of `workout`)

Title is the session title. Body is the facts line, then one purpose sentence picked by session type (phase override first).

Facts line: `{duration} · {zone} · {distance}`, unchanged.

| Picked when | EN purpose | VI purpose |
|---|---|---|
| Phase is Taper | Taper week: less is more. Stay fresh. | Tuần Taper: tập ít lại để giữ sức. |
| Easy Run, Recovery Run | Keep it truly easy. This is the base everything else stands on. | Chạy thật nhẹ. Đây là nền cho mọi buổi khác. |
| Long Run | Time on feet for {race}. Easy is the point. | Tích lũy thời gian trên chân cho {race}. Chạy nhẹ là đúng. |
| Tempo, Threshold, Interval, Fartlek | Today's key session. Warm up well, hit the targets, no more. | Buổi chính của tuần. Warm-up kỹ, chạy đúng target, không hơn. |
| Hill Repeat, Hill Sprint, climbing runs | Climbing strength for {race}'s {d_plus} m D+. | Sức leo cho {d_plus} m D+ của {race}. |
| Strength, ME | Strong legs hold your form late in the race. | Chân khỏe giữ được form ở cuối race. |
| Anything else | (no purpose sentence) | (none) |

`{race}` is `plans.race_name`. Without it, Long Run reads "Time on feet for race day." / "Tích lũy thời gian trên chân cho ngày race." `{d_plus}` is the race's elevation gain from its course KB entry. Without it, the hill line reads "Climbing strength for race day." / "Sức leo cho ngày race."

Example: **Mountain Trail Long Aerobic Run & Hill Sprints**
*150 min · Zone 2 · 18 km. Time on feet for UTMB 100K. Easy is the point.*

### B. Monday brief (new kind `week_brief`)

Sent Monday 07:30 when the current plan week has workouts. Tapping it opens that week, where the existing week brief explains the why.

| | EN | VI |
|---|---|---|
| Title | Week {n} of {total}: {phase} | Tuần {n}/{total}: {phase} |
| Body | {count} sessions, {hours} h. Key session: {key_title} on {weekday}. | {count} buổi, {hours} giờ. Buổi chính: {key_title} ({weekday_vi}). |
| Suffix when Monday has a workout | Today: {title}, {duration}. | Hôm nay: {title}, {duration}. |

`{key_title}` is the week's priority session, else its longest. On Mondays the brief replaces the workout reminder, which is why it carries "Today:".

### C. Recognition after a key session (new kind `recognition`, replaces `recovery`)

Triggered when an activity from a watch or Apple Health is matched to a priority session or a Long Run within the last 24 hours. Manually ticked sessions get nothing: no data means no praise, and no chore either.

| | EN | VI |
|---|---|---|
| Title | Nice work on {title} | Hoàn thành tốt {title} |
| Body | {distance} km and {d_plus} m D+ in {duration}. {highlight} Tap to log how it felt. | {distance} km, {d_plus} m D+ trong {duration}. {highlight_vi} Chạm để ghi RPE. |

`{highlight}` is included only when it's true, checked against the activities matched to this plan's current block:

| Condition | EN | VI |
|---|---|---|
| Most D+ in the block | Your biggest climb this block. | Leo nhiều nhất trong block này. |
| Else longest distance in the block | Your longest run this block. | Bài chạy dài nhất trong block này. |
| Else | (omitted) | (omitted) |

### D. Missed session (rewrite of `unlogged`)

Same trigger as today (2+ unlogged sessions, oldest at least 2 days old, sync healthy). It now names the most important missed session and offers the fix instead of the chore. Tapping it opens Adapt week.

| | EN | VI |
|---|---|---|
| Title | Missed {weekday}'s {title}? | Lỡ buổi {title} hôm {weekday_vi}? |
| Body | No stress. Tap to adjust this week around it. | Không sao. Chạm để chỉnh lại tuần này. |

### E. Kept, lightly edited

| Kind | EN | VI | Change |
|---|---|---|---|
| planning | Plan next week / Your next week is empty. Tap to build it in a minute. | Lên plan tuần tới / Tuần tới chưa có buổi nào. Chạm để tạo trong một phút. | warmer, shorter |
| plan_ready | Your plan is ready / Tap to see your new week. | Plan đã sẵn sàng / Chạm để xem tuần mới. | names the week |
| checklist | unchanged copy | unchanged | at most once per 30 days (was 14) |
| knowledge, taper, race | unchanged (card title + summary) | unchanged | still need `notification_reviewed` cards |

## Settings screen (iOS)

```
Notifications                    [on/off]
  Workout reminders, a Monday week brief and the occasional coaching note.
  At most one a day, never at night.

Pause for a week                  (button)        Resume notifications (when paused)

Muted                             (only if any)
  Monday briefs                    ✕
```

| EN | VI |
|---|---|
| Notifications | Thông báo |
| Workout reminders, a Monday week brief and the occasional coaching note. At most one a day, never at night. | Nhắc buổi tập, tóm tắt tuần vào thứ Hai và đôi khi một lời nhắn từ Coach. Tối đa một lần mỗi ngày, không gửi ban đêm. |
| Muted | Đã tắt |
| Less like this | Bớt loại này |
| Monday briefs / Coaching notes / Session recognition / Missed sessions / Profile tips / Knowledge tips | Tóm tắt tuần / Lời nhắn từ Coach / Ghi nhận buổi tập / Buổi bị lỡ / Gợi ý hồ sơ / Kiến thức |

The switch writes `workouts_enabled = coaching_enabled = results_enabled = <switch>`. Existing accounts with mixed values show "on" if any is on; the first save makes them uniform.

## Change surface

**Backend**
- `notification_preferences`: add `muted_kinds TEXT[] NOT NULL DEFAULT '{}'` (init_db + Alembic, per the db-migration skill).
- `notification_rules.py`: usual-start computation; `week_brief` and `recognition` candidates; `recovery` retired; weekly cap and back-off, both read from `notification_events` history already loaded in context; mute filter.
- `notification_copy.py`: templates above. Keep them in one table so EN/VI review is a single diff.
- `routers/notifications.py`: `POST /api/notifications/{id}/feedback` with body `{"less": true}`. Owner-checked like `/opened`; it appends the event's kind to `muted_kinds`. `PATCH /preferences` accepts `muted_kinds` (only shrinking it, for un-mute).
- `apns.py`: set `category` in the payload (`coaching` or `plain`) so iOS shows "Less like this" only where allowed.

**iOS**
- `NotificationSettingsView`: one switch, pause, muted list.
- Register a `UNNotificationCategory` "coaching" with action "Less like this" (no foreground launch). The delegate posts feedback, then calls the completion handler on the main thread (same rule as the #189 fix).
- `Localizable.xcstrings`: new strings above; remove the retired time and units labels.

## Acceptance

- Frozen-clock rules: usual start with fewer than 4 activities → 07:00; weekday vs weekend medians; clamp to 06:00; quiet-hours clamp.
- Weekly cap: 5th proactive in 7 days suppressed; plan_ready still sent.
- Back-off: 3 unopened `week_brief` → none for 14 days; 3 unopened `workout` → still sent.
- Mute: muted kind never selected; un-mute restores it.
- Monday: brief replaces the workout reminder and includes "Today:".
- Recognition: requires a matched device activity; highlight only when true against the block; none for manual ticks.
- Copy: every template renders with each optional value missing, in EN and VI; VI length ≤ EN for titles; banned-word grep clean.
- Delegate: "Less like this" action completes on the main thread (extend `NotificationDelegateTests`).
- Device: switch on/off, pause, long-press action mutes, Monday brief tap opens the week.

## Rollout

Same allowlist path as #143: user 5 first, then small batches. Ship after #189 is on TestFlight.

## Not in this batch

Milestones (longest run ever, first full week, block complete), race countdown at 4 weeks / 1 week / 2 days with gear and fuel links, HRV easy-day suggestion, skipping the reminder when the workout was already opened in the app. Each fits the same budget later.

## Decisions to confirm

1. Monday brief at 07:30, or at the usual start time like workout reminders?
2. Recognition only with watch or Apple Health data (no praise for manual ticks): OK?
3. Mute is permanent until removed in settings: OK, or should it expire after 90 days?
