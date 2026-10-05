# Explicit hold targets — 2026-10-05

The existing Execution/About workout timeline displays explicit seconds per hold and rest between sets in EN/VI, at desktop and mobile breakpoints. No frontend format change. These synthetic values (two holds of 38.5 seconds, 47 seconds between sets in a three-minute Strength segment) exercise units and layout; they are not a universal training dose. The sum of holds and between-set rest is 124 seconds, within the 180-second segment.

- [English desktop](hold-en-desktop.png)
- [English mobile](hold-en-mobile.png)
- [Vietnamese desktop](hold-vi-desktop.png)
- [Vietnamese mobile](hold-vi-mobile.png)

Captured from the running worktree frontend on localhost:3050 and backend on localhost:18010 at code c4aa357. Scratch database uphill_ai_test only. Seeded through the backend data-access layer after resolving prescriptions. Desktop used the default viewport; mobile CSS viewport was 390 pixels wide. Temporary viewport reset, test accounts/plans removed, session signed out, tab and owned servers closed. No integration tests or table truncation. Local Next.js development issue badge is unrelated to the changed prescription.
