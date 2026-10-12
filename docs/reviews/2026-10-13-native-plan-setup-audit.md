# Native plan setup and weekly-action audit

Completed continuation of the interrupted Claude session on PR #120.

## Flow and parity

- Race and distance goals: editable distance/D+, known race course choices, trail/road/mixed surface, race date, Finish strong / target time / best possible, and Goal Determiner with setup prefill.
- Weekly preferences: current km/week, running days, long-run day, up to two double-session days, gym and treadmill independently, home terrain, hill/trail days, stairs, and treadmill incline.
- Onboarding-only profile context: optional injury history and HR; birth date, gender, height and weight under More about you; optional real UTMB/VBM profile linking. Existing athletes reuse their saved profile; zones remain editable in Profile.
- Return/recovery goals retain their contextual questions. Review links back to setup and includes venues and double sessions. Coach notes stay optional.
- New-plan race path has eight short steps; onboarding adds optional body and race-history steps.

## Audit fixes

- Race matching exposes available courses and preserves manual edits, including edits made while a lookup is pending.
- Done/undo/missed/log/move/swap refresh server-computed completion (the original PR fix). The next-week sheet reads the live offer.
- Below 70% completion, next-week generation requires the explicit confirmation before sending override_gate.
- Next-week generation sends the athlete's local date.
- Schedule changes validate running-day counts and double-session membership; changing run days reconciles long-run and double-session days. Legacy web plans with unspecified run days can still change venues alone.
- Onboarding keeps gym/treadmill access independent and preserves zero weekly kilometres.
- Goal Determiner's profile link opens real profile search instead of a placeholder.
- Effort controls and feedback displays use Very Light / Light / Moderate / Hard / Max Effort across native and web. Existing numeric RPE storage is unchanged (2/4/6/8/10 for new selections; older values remain valid).
- New copy ships with Vietnamese translations. Venue weekday labels and number formatting follow the chosen language.

## Validation

- iOS unit suite: 381 tests passed on iPhone 17 Pro / iOS 26.5.
- Live onboarding E2E: fresh registration → setup → generation → plan passed on iPhone 18 Pro / iOS 27. The E2E build temporarily pointed local traffic to the isolated API on port 8015; AppEnvironment.swift was restored afterward.
- Web: 505 tests passed, TypeScript and static export passed; lint has zero errors and existing warnings.
- Backend: 1,828 tests passed with tests/integration/test_kafka_consumer_worker.py excluded. The first full run stopped at that consumer's poll loop because a Kafka broker was unavailable (420 tests had passed). A run launched from the repository root also hit test_client_closing_stream_after_done_keeps_reply_ok; the final run from backend/ passed that test and the remaining suite.
- No production deployment performed. Race course suggestions require the backend change to be deployed along with the native update.

## Visual evidence

[Simulator captures and web screenshots](../../ios-native/docs/screenshots/setup-continuation/).

Simulator captures use real SwiftUI views hosted on the simulator with controlled test data, including English, Vietnamese, and large text. Web captures use the running application and a locally seeded preview athlete. Committed evidence includes the EN/VI overviews and web captures; the opt-in screenshot suite can regenerate the individual native captures. The live E2E covers app navigation and setup reachability.

## Native effort color bar

The five effort choices now form a compact cyan / green / blue / amber / red bar. Each segment is tappable, keeps its named label, and shows a high-contrast checkmark and outline when selected. Accessibility text sizes use labeled rows with color swatches. Workout logging, next-week generation and adaptation share the same control; numeric RPE requests remain unchanged.

[Next-week screen](../../ios-native/docs/screenshots/effort-color-bar/next-week-en.jpg), [English states](../../ios-native/docs/screenshots/effort-color-bar/effort-states-en.jpg), [Vietnamese states](../../ios-native/docs/screenshots/effort-color-bar/effort-states-vi.jpg), [large Vietnamese text](../../ios-native/docs/screenshots/effort-color-bar/effort-large-vi.jpg).
