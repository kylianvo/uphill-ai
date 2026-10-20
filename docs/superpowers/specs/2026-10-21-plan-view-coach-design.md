# Plan view for the training loop: Today, journey, coach message, built around you

Owner answers 2026-10-21: Today goes above the carousel; milestones as recommended; the coach message is model-generated (with a rule-based safety net).

## Job
A trail runner opens the plan once or twice a day. Most days: "what do I do today, and am I on track?" Less often: after a sync, after a bad week (adapt), at a block boundary. Mode: Operate (platform conventions outrank expression). iOS first, web after.

## What the screen shows, top to bottom
1. **Today** — the next session as one card: type, duration, zone, climb, state (to do / done / missed). Tap opens the existing workout detail.
2. **Journey strip** — a thin line from now to race day: phase segments, "you are here", milestones (done / next). Milestones (my recommendation, owner accepted): first long run of 3 h or more; first recovery week completed; peak week; taper starts; race week. Computed deterministically from the plan.
3. **Coach message** — at most one, tone `encourage | push | heads_up`, 1–2 sentences, model-worded from deterministic facts, rule-based text when the model is unavailable. Silent when there is nothing worth saying.
4. **Built around you** — one line: days a week, long-run day, mountain; shows a deviation when the plan breaks one (plan_lint preference codes), linking to the schedule editor.
5. Existing: goal pill/sheet (with the feasibility notice), summary carousel, week brief, day rows.

## Backend
- `services/plan_journey.py` (pure): phases, milestones, days to race, preference deviations. `GET /api/plans/{id}/journey`.
- `services/coach_nudge.py`: deterministic facts + tone, Gemini wording (`coach_nudge` prompt, Langfuse prompt of the same name, metadata-only observability), rule-based fallback EN/VI. Cache `coach_nudges(plan_id, day, facts_hash, tone, text)` (init_db + Alembic): at most one generation per plan per day unless the facts change. `GET /api/plans/{id}/coach-nudge?lang=`.

## Guardrails (anti-goals)
No streaks, badges or guilt. No medical advice. Never state a number that is not in the facts. A push names a way forward (move a session, adapt the week), never blame. One message at a time. EN and VI in the same change. Nothing asks for input twice.

## Facts the coach may use
Adherence last 7 days and last completed week, consistent-week count, missed sessions with reasons, readiness (HRV/resting HR), goal status (on path / plan support / feasibility verdict), next session, milestone just reached, days to race.

## Open for the builder
Exact thresholds for tone (start: adherence < 60% last completed week -> push; ≥ 80% or a milestone reached -> encourage; feasibility unsupported or a readiness flag -> heads_up), nudge text length limit (220 chars), visual details within existing tokens.
