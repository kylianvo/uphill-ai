# Scheduler reliability release record

Status: implementing offline; production HOLD. Staging awaits the separate explicit go-ahead checkpoint.

## Frozen release contract

Plan: `docs/superpowers/plans/2026-10-04-scheduler-reliability.md`.
Source register: `docs/research/2026-10-04-scheduler-rule-register.md`.
Owner authorized execution after requiring the Vietnamese-copy skill. Apply R1–R6 to every changed/generated VI sample.

- One candidate plus at most one refinement. Stop after a failed refinement.
- All 19 existing scheduler fixtures plus invented sequential cases, same code/model/date/KB for each paired arm.
- Fixed evaluation date: 2026-10-05; keep named partial-start cases.
- Repeat four Vietnam cases and healthy sequential blocker three times per arm.
- Preserve healthy volume/tier bands and existing references. Report unavailable metrics explicitly.
- Zero new-output structure/access failures; no rule-based golden fallback; retries reported; no regression in applicable existing checks.
- Paired mean latency increase ≤20%, full suite and repeated subset reported separately.
- Long-run shares are diagnostics with explicit units; new caps are not verified or introduced.
- No lost EN/VI caveats, added claims, banned new VI wording or visible overflow.
- Every external eval push includes `--synthetic-only`; metadata-only Langfuse export.

## Execution evidence

2026-10-04: source register and plan contract created. Environment labels and live KB unchanged. Run identity (code SHA, model, prompt versions, seed hash, retrieval snapshot) will be recorded from verified values before paid execution; no guessed versions are accepted.

## Results and decisions

No candidate has run yet. Historical fitness-snapshot results are in the separate fitness release runbook and do not establish this release's gate.

2026-10-04 Task 2 diagnosis: synthetic next-block core reproduced `Actual 0.0km/0.0h` for missing logs and no watch data. Changed to `Known logged volume`, explicit unknown/missed counts, calendar coverage and override/readiness distinction. Four failing regressions became green; original gate behavior stayed green. This establishes misleading context, not proof that it alone caused the historical stochastic 110.2 km result. The paired sequential evaluation remains required.
