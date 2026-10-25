# Coach weekly review card

## Why
The Plan screen's coach card showed one long paragraph in the planner's voice ("we've incorporated your requested
Tuesday double session…"). The athlete wants what a coach would text on Monday: how last week went, what this week
is about and what it builds, one thing to watch, and the session to nail. Warm, encouraging, with a push.

## What the athlete sees (iOS Plan screen, current week)
- **Closed by default, always.** One row: coach badge, "Coach Uphill · Week N", a one-line preview (message 1), a chevron.
- **Tap to open:** three short chat-style messages, then a highlighted "session to nail" box, then "Read the full
  review" (the existing week brief sheet). Tap again to close.
- Other weeks, or a backend without the new fields, keep today's card (week brief "why", welcome, priority pick).
- Web has no coach card on the Plan screen today; not added here.

## Messages
1. **Last week** — what was actually done (sessions completed, missed reasons, milestones). Week 1: a welcome.
2. **This week** — the focus in plain words (ME week, first Zone 3 week, recovery week, taper, race week, base) and
   the key sessions by day, plus what it builds for this race.
3. **Watch out** — one rule the athlete can check themselves.
- **Nail** — the priority session, else the long run: day, title, minutes.

## Rules (unchanged principle from coach_nudge)
- Facts are computed in code (`coach_nudge.facts_for`, now also this week's focus and key sessions, race distance and
  D+); the tone is chosen by rules (encourage / push / heads_up, and `steady` when none applies, so the card always
  speaks for the current week); the model only words it.
- Every number in the model's text must appear in the facts (`grounded`), each message ≤ 200 chars, exactly three.
  Otherwise a rule-written version with the same structure is used (EN + VI).
- The response keeps `text` (the three messages joined) so the shipped iOS build keeps working; new fields
  `messages` and `nail`. Stored in `coach_nudges.messages` (JSONB) and `coach_nudges.nail`.
- Prompt `coach_review` is a Langfuse text prompt with the in-code fallback; golden check on the small-callers script.
