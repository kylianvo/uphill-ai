# Goal-specific fallback UI evidence — 2026-10-05

The running local frontend displays the actual Start Running fallback resolved by c1f4834, in the existing Execution/About format. The synthetic profile has typed 20 km/week; the goal contract takes priority and authors three non-consecutive 20-minute walk/run sessions. Every displayed one-minute walking and running segment is explicit; 10 pairs sum to 20 minutes. These are conservative fallback app choices, not universal book doses.

- [English desktop](walk-run-en-desktop.png)
- [English mobile](walk-run-en-mobile.png)
- [Vietnamese desktop](walk-run-vi-desktop.png)
- [Vietnamese mobile](walk-run-vi-mobile.png)

Verified EN/VI 20 minutes, Zone 1, walking 15:00/km and running 10:02/km; the same units and quantities appear in both stored outputs. Existing timeline wraps on mobile without horizontal overflow. Desktop CSS viewport 960×800, mobile 390×844; browser 150% zoom explains screenshot scaling. Viewport reset after capture.

Scratch uphill_ai_test only, localhost:5433; seeded through the backend data-access layer after real fallback resolution, with no model calls. Disposable users 15/16, plans 9/10 and sessions deleted by exact identity; no integration tests/TRUNCATE. Signed out, tab closed, owned 18010/3050 servers stopped. Next.js development issue badge is unrelated. Existing English formatter uses plural minutes for a one-minute segment; no quantities are ambiguous.
