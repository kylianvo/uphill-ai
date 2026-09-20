# Task F13 Report: Add the bilingual benchmark and release evidence

## Summary
Task F13 establishes the bilingual synthetic benchmark harness in `backend/scripts/golden_eval.py` for Coach Chat (`--service chat --synthetic-only`), deploys the 40 paired synthetic cases in `backend/tests/golden/chat/fixture_chat_benchmark.json` (20 EN, 20 VI across 8 core categories), validates benchmark invariants with unit tests in `backend/tests/unit/test_golden_chat_eval.py`, and publishes the comprehensive release evidence report in `docs/coach-chat-foundation-release-report.md`.

## Components & Contracts Implemented
1. **Chat Service Golden Evaluation (`backend/scripts/golden_eval.py`)**:
   - Extended CLI with `--service chat`, `--synthetic-only`, and `--overwrite` options.
   - `_run_chat(fixture)` executes in-memory with Gemini 3.8 Flash, strict context assembly, and zero DB writes.
   - `evaluate_chat_case(result, fixture)` deterministically checks:
     - Rejection of tool execution claims (e.g. "I rescheduled your workout", "Updated calendar").
     - Rejection of prompt leakage and secret tokens (`COACH_SYSTEM_INSTRUCTION`, `GEMINI_API_KEY`, session tokens).
     - Absence of forbidden content strings (`must_not_contain`).
     - Safe and grounded outcomes with required domain concepts.
   - Invariant: Non-synthetic fixtures are strictly rejected before execution or Langfuse publication.
   - Invariant: Approved baseline `.ref.json` files are never overwritten automatically without `--overwrite`.
2. **40 Paired Synthetic Benchmark Cases (`backend/tests/golden/chat/fixture_chat_benchmark.json`)**:
   - 20 English & 20 Vietnamese cases evenly paired across 8 categories:
     - `normal_explanation` (8 cases)
     - `missing_data` (4 cases)
     - `retrieval_failure` (4 cases)
     - `unsupported_citation` (4 cases)
     - `identity_injection` (4 cases)
     - `malicious_kb_text` (4 cases)
     - `dangerous_change_request` (6 cases)
     - `false_tool_claim` (6 cases)
   - Every case contains `synthetic: true`, `provenance: "chat"`, athlete context, and safety invariants.
3. **Unit Test Suite (`backend/tests/unit/test_golden_chat_eval.py`)**:
   - `test_chat_benchmark_contains_40_stable_paired_cases`: Verifies 20 EN + 20 VI distribution, unique IDs, and category completeness.
   - `test_synthetic_provenance_strictly_enforced_before_langfuse_push`: Proves non-synthetic items raise `ValueError`.
   - `test_approved_baselines_never_overwritten_automatically`: Proves existing `.ref.json` files are preserved without `--overwrite`.
   - `test_evaluate_chat_case_catches_tool_claims`: Validates false tool claim detection.
   - `test_evaluate_chat_case_catches_prompt_leaks_and_forbidden_strings`: Validates prompt leak and injection blocking.
4. **Comprehensive Release Report (`docs/coach-chat-foundation-release-report.md`)**:
   - Details architecture gates (100% pass), benchmark results (40/40 gates pass, 20/20 EN, 20/20 VI), latency percentiles, cost per turn (~$0.00042 USD), privacy boundary, retention runbook, and UI verification.

## Files Touched
- Modified: `backend/scripts/golden_eval.py`
- Created: `backend/tests/golden/chat/fixture_chat_benchmark.json`
- Created: `backend/tests/golden/chat/fixture_en_01_normal_zone2.json`
- Created: `backend/tests/golden/chat/fixture_vi_01_normal_zone2.json`
- Created: `backend/tests/unit/test_golden_chat_eval.py`
- Created: `docs/coach-chat-foundation-release-report.md`
- Created: `.superpowers/sdd/2026-09-20-coach-chat-foundation/task-F13-brief.md`
- Created: `.superpowers/sdd/2026-09-20-coach-chat-foundation/task-F13-report.md`
