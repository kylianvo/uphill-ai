# Native plan setup and weekly-action audit

Completed continuation of the interrupted Claude session on PR #120.

## Flow and parity

- Race and distance goals: editable distance/D+, known race course choices, trail/road/mixed surface, race date, Finish strong / target time / best possible, and Goal Determiner with setup prefill.
- Weekly preferences: current km/week, running days, long-run day, up to two double-session days, gym and treadmill independently, home terrain, hill/trail days, stairs, and treadmill incline.
- Onboarding-only profile context: optional injury history, HR thresholds and pace; birth date, gender, height and weight under More about you; optional real UTMB/VBM profile linking. Existing athletes reuse their saved profile; zones remain editable in Profile.
- Goal choices are Race (trail or road), A distance, and Getting started in native and web. Return-from-break and post-race recovery are no longer offered; existing plans remain supported. Review links back to setup and includes venues and double sessions. Coach notes stay optional.
- New-plan race path has eight short steps; onboarding adds optional body, training-zone and race-history steps (11 steps on the race path).

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


## Onboarding training zones

Onboarding now asks optional Max HR and Resting HR (moved from Body), AeT, AnT, easy running pace (slow/fast bounds), and Threshold Pace. Values persist before the first plan is generated; the existing generator receives the saved physiology and pace anchors. App-generated profile defaults are left blank instead of appearing as measurements. Unknown zones or an unconfirmed threshold source require an explicit “Continue with estimates” confirmation, with “Review values” to return to the inputs.

The training-zone step has Heart Rate and Paces tabs. Its HR bar scales from resting to maximum when all four anchors are valid; incomplete inputs and the shared guide use a schematic. Both use the Training Zones tab's blue/green/amber/orange/red palette. The pace tab previews all five ranges with colored ladders, matching the generator's formulas and Threshold Pace precedence. AeT marks the end of Zone 2 and AnT the end of Zone 3 in the app's model; the diagram labels schematic widths when no complete HR scale is available. Watch estimates, field tests, lab tests, and an unknown source are separate choices. The guide retains the web's watch-brand instructions, adds pace guidance, and links to [Evoke's assessment protocol](https://evokeendurance.com/resources/our-latest-thinking-on-aerobic-assessment-for-the-mountain-athlete/). Both onboarding and Profile use the same guide.

Threshold Pace previously was dropped by the onboarding endpoint; it is now accepted and saved to the existing users column. Format/order validation rejects invalid pace and threshold inputs. Missing HR anchors and a missing easy-pace bound remain ordered around supplied values. No schema or generation-prompt changes.

Validation for this addition: 390 native tests passed; 23 focused backend tests passed, including persistence, first-plan context, optional inputs and validation. Simulator screenshots cover English, Vietnamese, empty/filled values and large text in [the training-zone captures](../../ios-native/docs/screenshots/onboarding-training-zones/).

## Fresh-account flow audit

Audited registration → welcome → goal → schedule/venues → profile/zones → race history → start date → review → generation → first plan for the three supported goals. Race and distance also collect course/date/goal context. New-plan setup reuses saved physiology and injury context.

Fixed three inputs that could mislead generation: untouched fresh-account 30 km/week seeds are now blank and require an answer (including an explicit “No running yet” choice); time targets start unset and accept short-race finishes below 30 minutes; event plans start at least two weeks before the goal date. Submission revalidates the full draft and returns to any missing/invalid step. Changing from race to a distance goal no longer sends the previous race name.

Required starting context: goal, event course/date when relevant, current weekly volume, running-day count and days, long-run day, start date. Defaults for schedule and training venues remain visible and editable. Optional context: injury history, DOB/body data, measured or estimated HR/pace anchors with source, race history, double sessions and coach notes. Unknown zones require confirmation and are estimated; they are not represented as measured values. Imported history only informs generation once its sync is complete. Watch connection and later profile updates enrich subsequent generations.

Remaining operational limits: generation jobs live in server memory, so a backend restart can interrupt a job; a new runner with no measured zones or imported history necessarily begins from estimates and self-reported volume. These are existing constraints, not promises of complete physiological context.

Latest validation: 393 native unit tests and 23 focused backend tests passed. Fresh registration → Getting started → explicit zero running volume → unknown-zone warning → first-plan generation passed on iOS 27. Screenshots verify the three web goal choices in both onboarding and new-plan setup; native captures cover all 11 race-onboarding steps, HR/pace tabs, guides, estimate warning, EN/VI, and large text.

[All onboarding steps](../../ios-native/docs/screenshots/onboarding-training-zones/all-steps-en.jpg), [HR and pace preview](../../ios-native/docs/screenshots/onboarding-training-zones/overview-en.jpg), [estimate warning](../../ios-native/docs/screenshots/onboarding-training-zones/estimate-warning-en.jpg), [web goal choices](../../ios-native/docs/screenshots/onboarding-training-zones/web-onboarding-goals.jpg).
