---
name: ui-screenshot-evidence
description: Use whenever a change touches anything rendered in the frontend (frontend/src/components, frontend/src/views, frontend/src/app, CSS, layout, copy that's visible on screen). Before declaring the work done, run the app locally and capture a screenshot of the changed state as evidence — never claim a UI change works from reading the code or from passing unit tests alone.
---

# UI screenshot evidence

Passing `tsc`/`eslint`/`vitest` proves the code compiles and the component
logic is correct in isolation. It does not prove the page actually looks
right, that layout doesn't break, or that the change is reachable from the
real app. For any change to `frontend/src/**` that affects what a user sees,
**capture a real screenshot of it running before saying the task is done.**

This is not optional polish — it's the last step of the task, same as running
the test suite. If you cannot get a screenshot (e.g. the environment has no
Postgres available), say so explicitly instead of claiming the change is
verified.

## Workflow

### 1. Get a local Postgres up

```bash
docker compose up -d db
```

This project's compose file exposes Postgres on host port `5433` (see
`docker-compose.yml`). It's a persistent volume — data from previous sessions
is still there unless something explicitly truncated it.

### 2. Start the backend against it, on a free port

Port `8000` is frequently already occupied by an unrelated container from
another worktree/session (`docker ps` to check — look for anything mapping
`->8000/tcp`). Don't fight over it; run the dev backend on a scratch port
instead, e.g. `8010`.

Add (or reuse) a spawn entry in **this session's own** `.claude/launch.json`
(note: that file is read from the session's current working directory, which
may not be this repo if you started somewhere else — `pwd` first). A plain
`url`-only entry only *attaches* to an already-running process; to have the
tool start the server itself, give it a real command:

```json
{
  "name": "uphill-backend-dev",
  "runtimeExecutable": "bash",
  "runtimeArgs": ["-c", "DATABASE_URL=postgresql://uphill:uphill_secret@localhost:5433/uphill_ai ENVIRONMENT=development python3 -m uvicorn main:app --host 0.0.0.0 --port 8010 --app-dir backend"],
  "port": 8010
}
```

(If `bash -c` with inline env vars doesn't work in the tool's arg-parsing,
write a two-line wrapper script in your scratchpad and point
`runtimeExecutable` at that instead — see prior sessions for the exact
pattern.) Then:

```
preview_start(name: "uphill-backend-dev")
```

Sanity check before moving on: `GET http://localhost:8010/api/health` should
return `{"status":"healthy",...}`.

### 3. Start the frontend

The repo's own `.claude/launch.json` already defines `uphill-frontend` on
port `3050`. Just:

```
preview_start(name: "uphill-frontend")
```

### 4. Authenticate

`mock-login` only exists outside production (`ENVIRONMENT != production`,
which step 2 sets), so use it instead of the real OAuth/password flow:

```bash
curl -s -X POST http://localhost:8010/api/auth/mock-login \
  -H "Content-Type: application/json" \
  -d '{"email":"<some-test-email>@uphill.ai"}'
```

Take the `session_token` from the response, navigate the Browser pane to
`http://localhost:3050/?api=http://localhost:8010`, then set it via
`javascript_tool`:

```js
localStorage.setItem("uphill_session_token", "<token>");
localStorage.setItem("UPHILL_API_URL_OVERRIDE", "http://localhost:8010");
```

Navigate to that same URL again (a fresh load, not just `history.pushState`)
so the app picks up the token on boot.

### 5. Get to the changed state

If the real flow to reach the changed UI is slow or non-deterministic (e.g.
plan generation calls Gemini for real), don't wait on it — seed the data
directly with the backend's own data-access layer instead of hand-rolled SQL,
so you get realistic rows through the same validation the app relies on:

```bash
cd backend && DATABASE_URL="postgresql://uphill:uphill_secret@localhost:5433/uphill_ai" ENVIRONMENT=development python3 -c "
from db import create_or_get_user, save_workouts, update_workout_log, ...
# build exactly the scenario your change needs
"
```

Then navigate the Browser pane to the relevant tab/view.

### 6. Screenshot

The app's scrollable content lives inside a `.content-panel` element, **not**
`document.body` — a plain `computer{action:"screenshot"}` after a coordinate
scroll can silently show the wrong region, and a full-page Playwright
screenshot will only capture one viewport-height because `document.body`
itself doesn't scroll. Scroll the real container explicitly first:

```js
document.querySelector('.content-panel').scrollTop = <value>;
```

Take one screenshot per meaningfully distinct state the change introduces
(e.g. collapsed vs. expanded, or light vs. dark data scenario) — not just the
first thing that renders.

### 7. Hand it to the user

Save the screenshot to a file and send it with `SendUserFile` (or attach it
inline if the harness renders tool-result images directly to the user — when
unsure, send the file explicitly; a screenshot only visible in your own tool
trace is not evidence the user can see). Do this *before* the message that
claims the UI change is done, not as an afterthought.

### 8. Clean up

Stop the preview servers (`preview_stop`) when you're done verifying, unless
mid-session iteration means you'll need them again shortly. Don't leave
scratch/demo data in the shared dev database unless the user has asked you to
keep it around for the next round of changes.

## Anti-patterns this skill exists to stop

- Declaring a frontend change "done" or "verified" on the strength of
  `tsc`/`eslint`/`vitest` passing alone — those check logic, not appearance.
- Reading the JSX and reasoning "this should render fine" instead of actually
  rendering it.
- Screenshotting only the viewport that happened to be visible on load and
  never scrolling to check content below the fold, especially for this app's
  non-standard `.content-panel` scroll container.
- Capturing a screenshot but never actually surfacing it to the user (leaving
  it buried in tool-call output only you can see).
