# Vietnam course sources — verified 13 October 2026

The active catalog remains `../race_courses.json`. This directory preserves the
12 user-supplied GPXs and their parsed checkpoints as curation evidence. Loading
the race seed does **not** activate these archived profiles.

## Current catalog updates

| Race / edition | Categories | Source |
| --- | --- | --- |
| Vietnam Highlands by UTMB / 2027 | 10K, 20K Pinhatt, 50K Elephant, 100K Langbiang | [Organizer overview](https://vietnamhighlands.utmb.world/overview) and the four individual course pages recorded in the seed |
| Vietnam Trail Marathon / 2027 | 5km, 10km, 21km, 50km, 70km | [Organizer](https://vietnamtrailseries.com/trail-marathon/); 50km replaces 42km for this edition |
| Prenn Trail / December 2026 | 3km, 10km, 25km, 55km, 75km, 100km, 100 miles, 250km | [Current distance page](https://prenntrailchallenge.vn/en/distance); numeric figures and start dates were read from its linked 2026 course images |
| Lamdong Trail / November 2026 | 5km, 5km Kids Trail, 15km, 25km, 55km, 85km | [Organizer distance page](https://lamdongtrail.vn/en/distance/); numeric figures were read from the linked 2026 maps |

Category labels and actual route lengths differ. For example, the current
Prenn 55KM map gives 52km, while the Lamdong 85KM map gives 83.6km.
The seed stores the label separately from `distance_km`.

Historical `results` and previously active `course_profiles` are unchanged.
The added `edition_year`, `event_dates`, `verified_at`, `source_urls`, and
per-distance provenance describe the current catalog. Dates and start times
are local to the race in Vietnam. They do not introduce automatic edition
selection or new behavior in the matcher.

## GPX archive

- `vietnam_courses_2026-10-13.zip` contains the original bytes under
  `prenn_2025/` and `vietnam_highlands_2027/`.
  The ZIP (7.9MB) is a regular Git file; its SHA-256 is recorded in the JSON below.
- `vietnam_courses_2026-10-13.json` records the archive checksum, individual
  file checksums, edition, parser summaries, horizontal distance, and
  approximately 1km checkpoints. `source_url` identifies the corresponding
  organizer page; the files themselves came from the user's Downloads folder.
- Prenn's eight GPXs were explicitly confirmed by the user as **2025** routes.
  Their status is `historical_only`. The 103km and 187km files do not establish
  current 100km or 100-mile routes.
- Highlands' four files match the September 20 revision names on the 2027
  organizer pages. Their status is `needs_elevation_review` because their raw
  calculations differ substantially from the published totals.

| Highlands category | Published km / gain m | Parser 3D km / raw gain m |
| --- | --- | --- |
| 10K | 11.3 / 486 | 10.895 / 693.0 |
| 20K | 24.1 / 1,113 | 24.891 / 2,324.0 |
| 50K | 56.4 / 2,946 | 57.929 / 4,306.0 |
| 100K | 104.2 / 5,533 | 110.898 / 10,263.0 |

The archive uses the existing `GpxParser.parse(..., 1000)` calculation:
unsmoothed elevation differences and 3D distances. A zero-distance Start
checkpoint is added. Accumulated gain/loss is recomputed from the segment
totals because the existing parser repeats the final total at every checkpoint.
No smoothing, scaling to organizer totals, or fabricated checkpoints are used.

These records are deliberately outside `payload.course_profiles`: existing
consumers select the most recently curated profile without requiring a target
edition. Activating the 2025 Prenn tracks there would apply historical routes
to the current catalog. Review route equivalence and resolve Highlands'
elevation discrepancy before promoting any archive entry through the existing
course-profile curation workflow.

## Remaining source conflicts

- Pinhatt's page headline gives 24.1km/+1,113m, while its detail table still
  gives 22.8km/+1,100m. The catalog uses the headline and records the conflict.
- Prenn's introduction still mentions 103KM; the current distance page and
  dated map identify the category as 100KM. The map is used for this refresh.
- Highlands' 100K terrain percentages add to 90%; no remaining percentage is
  inferred. Some page logistics still use 2026 timestamps and are excluded.
- No VTM or Lamdong GPXs were supplied. Lamdong's page states that its GPX map
  is being updated.

This is a repository seed update. It has not been imported into a running
database or deployed.
