# iOS notifications: draft rollout runbook

Delivery is disabled by default. This implementation has not sent a real APNs notification.

## Before enabling a test account

1. Finish the remaining implementation and acceptance checks recorded in the implementation plan, especially coach draft and Coach Chat rebuild routing.
2. Deploy the schema migration before enabling the worker. The new Alembic revision is `a6f2c8d9e104`; validate the upgrade on a scratch database before production.
3. Enable Push Notifications for the app identifier and regenerate matching provisioning profiles. Confirm the signed bundle identifier matches `APNS_TOPIC`. Debug builds use sandbox; Release/TestFlight builds use production.
4. Mount the APNs .p8 key as a private server secret. Configure `APNS_PRIVATE_KEY_PATH`, `APNS_KEY_ID`, `APNS_TEAM_ID`, and `APNS_TOPIC`. Never commit the key or device tokens.
5. Set `APNS_ALLOWED_ENVIRONMENTS` to the environments being tested. Set `NOTIFICATION_ALLOWLIST` to explicit comma-separated test account IDs. An empty list sends to nobody.
6. Review actual server knowledge content in both languages before setting `knowledge_cards.notification_reviewed=true`. Missing eligible content suppresses knowledge/taper/race messages.
7. Only for an arranged test, set both `NOTIFICATION_WORKER_ENABLED=true` and `NOTIFICATION_DELIVERY_ENABLED=true`, restart the process, and opt in through the app's notification settings.

## Device acceptance record

Status: not run; credentials and a user-owned physical test device have not been provided.

Record build, device, account, APNs environment and observed outcome for sandbox and TestFlight:
- Permission grant/deny/revoke and settings return.
- Foreground, background and terminated-app taps to exact workout/card/week.
- Completion before delivery; quiet hours, timezone changes, pause and resume.
- Token rotation, account switching, logout and offline logout reconciliation.
- Coach view exit and unavailable/deleted content.
- English/Vietnamese settings, Dynamic Type and VoiceOver.

APNs acceptance is not proof of display. A completion or logout that has not reached the server can race a push; pending local logout removal is retried when that account authenticates again. Unknown transport outcomes consume the slot and are not retried.

## Observe and stop

Inspect `uphill_notification_outcomes_total`, `uphill_notification_worker_last_tick_seconds`, and `uphill_notification_pending_age_seconds` through the existing metrics endpoint. Heartbeat does not advance while delivery is disabled or the allowlist is empty. Candidate/suppression telemetry still needs broader acceptance coverage.

To stop new delivery, set `NOTIFICATION_DELIVERY_ENABLED=false` and restart the process. Keep preferences and event history intact. This cannot retract a push already accepted by APNs.

For key rotation, mount the replacement secret, update its key ID, restart workers to clear the cached provider token, verify an allowlisted test device, then revoke the old key.

Terminal payload/error metadata is stripped after 90 days. Minimal deduplication rows remain for account lifetime; account deletion cascades notification state. Source-specific tombstone deletion is deferred.
