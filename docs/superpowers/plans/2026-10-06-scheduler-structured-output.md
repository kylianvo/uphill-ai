# Scheduler structured-output correction

Owner approved this correction after the completed v15 gate on 2026-10-06. V15 passed 39/40 candidate observations but elite/no-COROS rejected an unsupported segment kind or setting on both attempts and fell back to rules. Exact rejected values were not retained. This is a structural failure; no claim is made that structured output guarantees valid coaching.

## Design

Use Gemini JSON structured output for the existing workout array. Constrain segment kind/setting/role enums and primitive field shapes using the existing resolver contract. Keep optional fields optional; do not introduce nulls or defaults that change resolver behavior. Keep Race fueling, double-session slots and legacy scalar fields available. Preserve Execution/About, persisted historical workouts, language meaning and every existing contextual validator.

Select the structured contract once from the exact STRUCTURED PRESCRIPTION header line in the trusted raw loaded prompt template. Compiled athlete notes cannot select it. Require nonempty segments both in the provider schema and locally under that contract. Production v1 remains a legacy scalar contract; the experiment and local fallback carry the structured header. Primary and reduced retry use the same schema and unchanged attempt/cancellation budget. No schema decoding that coerces values, drops fields or inserts defaults.

The marker is part of prompt versioning: structured templates must retain the exact header. There is no new environment flag. This is a compatibility bridge, not readiness evidence. Schema-valid doses still require arithmetic, hold timing, volume, access, intensity, readiness and phase validation; no thresholds or fixture assertions change.

## Execution and verification

1. Add failing boundary tests for legacy/candidate/local contract selection, identical primary/retry schemas, local omission rejection, and compiled-input trust boundary.
2. Add the compact provider schema and local contract enforcement. Preserve existing valid resolver behavior and bounded retry/privacy tests; make legacy test fixtures explicitly load a legacy template.
3. Run focused prescription/snapshot/deadline tests, then all backend units with `-m "not kafka"`. Independent review before freezing the next gate. No integration tests against dev or real databases.
4. Freeze code, prompt, model, KB and as-of date. Run all eight paired arms with synthetic-only metadata exports; retain every failure and original score. Compare latency, legacy checks and all applicable contextual gates. No selective reruns or acceptance of unavailable precision.
5. If automated gates pass, manually review EN/VI coaching and capture actual evaluated rows locally, preserving Execution/About. Use only isolated uphill_ai_test. Commit evidence, update draft PR82, then stop at the owner staging checkpoint.

Production/staging labels and deployment remain owner-controlled. No requirements, deploy-script, environment-file or dashboard changes.

Provider reference: [Google structured-output documentation](https://ai.google.dev/gemini-api/docs/generate-content/structured-output?hl=en). The installed SDK supports JSON MIME type and response_json_schema. Schema support does not replace semantic validation.
