# Mobile app (Capacitor)

The iOS/Android apps are a Capacitor shell around this same Next.js static
export — not a separate codebase. `frontend/ios` and `frontend/android` wrap
whatever's in `frontend/out` after `npm run build`. There is no code signing
configured yet, so builds below are debug/simulator-only.

## Build & run locally

```bash
cd frontend
npm run build          # static export to /out
npx cap sync ios       # or: npx cap sync android
npx cap open ios       # or: npx cap open android
```

`cap sync` copies `/out` into the native shell and re-links Capacitor
plugins — run it after every web change, not just once. `cap open` launches
Xcode / Android Studio, where you run on a simulator/emulator normally.

**`frontend/.env.production` is gitignored (machine-local, not tracked)** —
`npm run build` reads it by default, so it's what mobile builds actually
ship with unless you override `NEXT_PUBLIC_API_URL` on the command line. It
must point at the real HTTPS backend (`https://api.uphill-ai.io.vn`), not a
plain-HTTP address — iOS ATS and Android's cleartext policy will silently
block the app from ever reaching the API otherwise. There's no committed
template for this file; if you're setting up a fresh machine, create it
by hand with at least `NEXT_PUBLIC_API_URL=https://api.uphill-ai.io.vn`.

For local backend testing (pointing the mobile shell at `localhost:8000`
instead of prod), build with `NEXT_PUBLIC_API_URL=http://localhost:8000 npm
run build` — the iOS/Android network-security exceptions below only allow
cleartext to `localhost`/`10.0.2.2`, not arbitrary HTTP hosts.

The backend's `ALLOWED_ORIGINS` also needs `capacitor://localhost` (iOS)
and `https://localhost` (Android) — the fixed origins Capacitor's
WKWebView/WebView send, in every environment, not just local dev. This is
now the default in `backend/config.py`, but any environment with
`ALLOWED_ORIGINS` explicitly set in its `.env` (including the production
server) needs those two origins added manually or the shipped app can
never reach that backend — see `backend/config.py`'s comment on
`ALLOWED_ORIGINS`.

## Notifications

`src/utils/notifications.ts` wraps `@capacitor/local-notifications` (native)
with a `Notification` API fallback (web). Two recurring local notifications
exist, both scheduled via Capacitor's `on: {hour, minute}` schedule — an
OS-persisted daily repeat, not something the app has to re-fire:

- **Workout reminder** (`DAILY_WORKOUT_REMINDER_ID`) — static copy.
- **Daily knowledge** (`DAILY_KNOWLEDGE_REMINDER_ID`) — fetches one random
  card from `/api/knowledge/cards/random` at schedule time and uses its
  title/summary as the notification body. Because the content is a
  snapshot, not live at fire time, `AppContext.tsx` re-schedules both on
  every cold start (if enabled) so the copy doesn't go stale for users who
  open the app regularly. Users who never reopen the app will keep seeing
  whatever card was captured at the last schedule call — there's no
  background refresh without push infra.

Both toggles live in Profile Settings (`ProfileSettingsModal.tsx`) and
persist to `localStorage` (`uphill_reminder_enabled`,
`uphill_knowledge_reminder_enabled`, `uphill_reminder_time`).

## CI

`.github/workflows/mobile-build.yml` runs a debug/unsigned build of both
shells (Gradle `assembleDebug`, `xcodebuild -sdk iphonesimulator`) on every
push/PR touching mobile-relevant paths — a compile sanity check, not a
release pipeline. Signed builds (Fastlane/EAS-style, TestFlight/Play
Console) aren't set up yet.

## Known gaps

- No code signing / store deployment automation.
- Android builds have not been verified against a real device, only the
  Gradle/CI compile step.
- Notifications need on-device verification — the web fallback path can
  mask native-only issues.
