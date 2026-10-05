# Claude handoff: scheduler release candidate

Final handoff, 2026-10-06. Codex stopped at2% remaining weekly allowance (98% used). User requested continue toward a releasable version, stopping Codex at 2% remaining weekly allowance. No release/deployment approval is implied. Preserve athlete-facing Execution/About.

## Checkout and remote

Historical original deferred items1–5 and staging step6 were completed at earlier owner checkpoints; see docs/runbooks/2026-10-fitness-snapshot-release.md. Stagingv4 remains HOLD for no-COROS next-block volume, motivating this reliability work. Do not repeat old deployments or assume the earlier snapshot experiment PASS supersedes the current HOLD.

Use the managed worktree **/Users/vietvo/.codex/worktrees/fitness-snapshot-deferred/uphill-ai**, branch **codex/fitness-snapshot-deferred**. Push to **origin claude/kind-knuth-tqdqbf**, draft [PR82](https://github.com/kylianvo/uphill-ai/pull/82). Do not switch the original checkout /Users/vietvo/Documents/antigravity/uphill-ai. Its backend/.env supplies read-only credentials. HEAD and final verification will be recorded below at handoff.

Read in full CLAUDE.md, .claude/skills/llm-change-process/SKILL.md, .claude/skills/ui-screenshot-evidence/SKILL.md, the original 2026-10-02 fitness-snapshot spec/plan, docs/superpowers/plans/2026-10-04-scheduler-reliability.md, docs/superpowers/specs/2026-10-03-scheduler-reliability-design.md, docs/research/2026-10-04-scheduler-rule-register.md, docs/superpowers/plans/2026-10-06-scheduler-structured-output.md and **docs/runbooks/2026-10-scheduler-reliability-release.md**. For Vietnamese, use .agents/skills/uphill-ai-vietnamese-copy/SKILL.md. Existing owner approvals cover synthetic paid experiments, backend corrections preserving existing constraints, commits/push and PR82 updates. Staging deployment/prompt-label promotion requires the separate owner checkpoint.

## Current decision: HOLD

Remote plan_generation: production v1 SHA a0eab967a172a094ee5b524486b643497df24fae81406a7c1d0d2cfbf309ee4e; staging and snapshot-exp v4 SHA e100c9d4269819bba19cb03e7167ab6174aca637a0f72d977d4426d4f4192fdb; scheduler-reliability-exp v15 SHA b4ca322e6a8d31a9193d31de497ca8a4bcb5c447923505ff758e5cd26e867fad. Never move production/staging labels now. V15 prompt plus changed backend is a distinct code candidate, not a new prompt version.

Completed V15 gate (followup12): 39/40 candidate observations passed. Elite/no-COROS rejected unsupported kind/setting on both attempts then used rules. Exact offending values unknown. All 16 Vietnam observations passed; no legacy regression; 245 VI workouts scanned without banned terms. Full mean candidate 10.836s vs production 20.348s, repeats13.14/13.50/14.06s vs30.84/32.00/30.96s. Known cost$1.711382,100 attempts all costs known, embeddings excluded. Evidence docs/superpowers/evidence/scheduler-reliability/v15-evals/. No full manual/UI acceptance.

Owner approved provider structured output. Commit7de735cf8d03c7ae6cb0e67f1fc67e8be9fcdbcb implemented trusted raw-template marker selection, JSON MIME/schema, local segment-presence checks, same bounded two attempts. 1,312 backend units passed, independent review approved/no findings. Does not prove live effectiveness.

Followup13 compatibility baseline was explicitly aborted after repeated120s request deadlines; candidate never dispatched. Three scored cases and fourth cancelled attempt,4 cost-unknown observations; known$0.011472. Evidence docs/superpowers/evidence/scheduler-reliability/v15-schema-interrupted-baseline/. Cancellation OTel traceback retained. Never present this as completed gate or erase failures.

Fourteen fixed-prompt schema probes: unconstrained/MIME-only produced7-days; fast minItems=1 schemas returned1workout. Flat minItems=7 produced both7-day output and504 deadline. Both response_schema and response_json_schema behaved this way; provider root cause unknown. Diagnostic30s deadline is not the production120s deadline. Known$0.091231,14 matched attempts,4 unknown costs. Evidence docs/superpowers/evidence/scheduler-reliability/v15-schema-probes/. Commit2fc0b2afca5d7333f6dad9db8c5c938f5da9cb82 retained all negative evidence.

## Latest correction and next steps

Calendar coverage correction committed **929ca391379e48a440702f60f20bcb13370998ee** (backend tree **aceff2947c906243139961f3b23e1b6940ebe21c**): omit unused nested segments from legacy scalar schema; minItems equals requested calendar-day count; validate exact week/day coverage BEFORE normalization/clamping. Keep partial week1 exclusions and legitimate double sessions. Reject missing/extra days with generic logged exception and private missing-day retry feedback. Do not pad Rest, change dose, loosen assertions, or invent race calendar rules. Short prescription accounting tests explicitly isolate calendar checking; separate unmocked coverage tests verify rejection/retry. Final full suite1,323 passed, 23 warnings in 80.71s. Independent review approved/no findings,59 targeted passed. Followup14 was interrupted at the owner cutoff with16/25 production cases and no candidate/repeats. Owned exec4406/PID3029/child3039 are stopped. All partial evidence retained.

1. Inspect the reviewed calendar correction. The final reviewer subsequently completed its review and approved/no findings,59 targeted passes; the earlier quota failure was not counted as approval.
2. Freeze reviewed code/backend tree, v15 prompt, model, KB and as-of2026-10-05. Read-only preflight /tmp/uphill-reliability-environment.py and /tmp/uphill-v15-schema-preflight.json. Original37 principles/29 vectors remain untouched; hashes in runbook/identity files.
3. Run a **fresh followup15**, all8 paired arms: full25 production+candidate, then3 paired repeat sets of5 (four Vietnam tier/access combinations + healthy completed next-block). Do not resume interrupted13. /tmp/uphill-followup13-batch.py is the template; change every run name/output to15. Wrapper /tmp/uphill-followup-eval.py reads original.env without editing it. Every --push-langfuse invocation MUST include --synthetic-only. Followup13 summary/review/cost/identity scripts in/tmp can be adapted; inspect them first. Store immutable original hashes and privacy-filter before committing generated evidence.
4. Enforce unchanged gate: zero candidate errors/rule fallbacks, all applicable arithmetic/access/intensity/volume/readiness checksTrue (None not pass), no legacy regressions, healthy next-block115–150km, separate full and repeat mean latency <=production+20%. Retain retries/outliers/cost-unknown rows. Forty observations are25distinct+15repeats, no production-confidence claim.
5. If automated gate passes, manually read all EN/VI candidate workouts and capture desktop/mobile actual evaluated rows locally. Preserve format and unknown-readiness conservative coaching; never invent advanced ME/equipment. Only then claim staging-validation eligibility. Commit evidence, push/update draft PR82, stop and ask owner at staging checkpoint.

## Runtime and scratch UI

Native scratch database **localhost:5432/uphill_ai_test**, created owned by app role via local admin, isolated from dev. DockerPG5433 was unhealthy. No integration tests run; NEVER run TRUNCATE on dev/real DB. No scratch user/plan has been seeded yet. Backend startup initialized scratch schema/default cards only. Do not drop databases unasked.

Owned frontend was npm run dev -- --webpack --port3050 (exec12786; log/tmp/uphill-v14-ui-frontend.log). Owned UI backend was python/tmp/uphill-reliability-ui-server.py, port18010 (exec12978; log/tmp/uphill-v15-schema-ui-backend.log); it loads7de code and MUST restart after calendar correction. Wrapper/tmp/uphill-reliability-ui-env.py verifies scratch dbname, disables Gemini/Langfuse/workers/goals without editing.env. Final running/stopped status below.

There are no owned seeded accounts/plans requiring deletion. Prepared but NOT run seed/cleanup: /tmp/uphill-v15-schema-ui-seed.py and/tmp/uphill-v15-schema-ui-cleanup.py. Update seed to actual accepted fresh followup15 results; source13 candidate does not exist. Exact owned IDs in/tmp/uphill-v15-schema-ui-state.json after seed, cleanup only those IDs/users/sessions (no TRUNCATE). Credentials stay local/tmp. No approved UI evidence currently.

CUA browserID2, owned tab7 aliasv15tab at localhost3050/app?api=http://localhost:18010, anonymousVI login modal open. Old owned tab6 blocked after old backend stop; no security bypass. User tabs untouched. Call cua.rewriteDocumentation before continuing UI. Browser zoom150%:1440x1200 CSS960x800 desktop;585x1266 CSS390x844 mobile. Reset viewport/close owned tabs at cleanup.

## Safety and repository hygiene

No requirements.txt/deploy-script/.env changes; no dashboards; no merge/mark-ready/production. Integration scratchdbname exactly uphill_ai_test. LANGFUSE_EXPORT_CONTENT=false; metadata-only export. Generated athlete prose never pushed to Langfuse. Reconstruct original user denylist from codepoints for diff/evidence checks; never write literal names to any file/message/object:

```python
words=[[81,117,97,110,103],[113,117,97,110,103,116,114,97,110,117,108,116,114,97],[118,118,118,105,101,116,49,50,51],[86,105,101,116,32,86,111]]
pattern=re.compile('|'.join(''.join(map(chr,w)) for w in words),re.I)
```

Run backend tests using /Users/vietvo/miniconda3/bin/python -m pytest tests/unit -q -m 'not kafka'. Repo hook .venv/bin/pytest is missing; only skip backend-unit-tests hook AFTER verified full conda suite, retain other hooks. Ruff hook may modify files; restage. One commit per coherent item, trailer Co-Authored-By: Codex <noreply@openai.com>. Explicitly stage selected files; evidence/runbook ignored needs git add -f. Untracked backend/tests/golden/runs/ are local raw evidence, never broad-add. .superpowers/sdd/2026-10-04-scheduler-reliability/progress.md is local ignored ledger.

## Final handoff checkpoint

Last backend commit **929ca391379e48a440702f60f20bcb13370998ee**, backend tree **aceff2947c906243139961f3b23e1b6940ebe21c**; pushed remote claude/kind-knuth-tqdqbf. Final documentation/evidence commit is the commit containing this handoff (discover via git log -1 after pull). Full units1,323 passed23warnings; independent review Approved/no findings59targeted passed. API98% weekly used. Followup14 explicitly interrupted at the owner cutoff: **16/25 production cases**, engines{'gemini': 7, 'gemini_retry': 3, 'rule-based-or-unknown': 6}, no candidate or repeats.34 attempts/33 matched observations,17 known costs$0.206558,16 unavailable costs,1 unmatched; no zero-cost inference. See docs/superpowers/evidence/scheduler-reliability/v15-calendar-interrupted-baseline/. Paid batchPID3029/child3039 and preview servers verified absent. Only untracked backend/tests/golden/runs/ raw artifacts remain; no outstanding backend edits. Release HOLD. PR82 remains draft. No new label moves or staging/production action.

## Gate command templates on this machine (rename to fresh followup15)

From the managed worktree backend, use /Users/vietvo/miniconda3/bin/python /tmp/uphill-followup14-batch.py as a template only, renaming every arm to followup15 before execution. Followup14 is already attempted and stopped; never overwrite it. The batch logs each arm to/tmp/uphill-reliability-followup14-<arm>-<suffix>.log; raw results stay backend/tests/golden/runs/reliability-followup14-<arm>-<suffix>/. A nonzero completed arm exit does not erase failures or stop remaining pairs; absent results.json stops the batch. Never overwrite an already attempted name; use a fresh followup number if frozen inputs/code change.

Equivalent full-arm commands (wrapper sets original read-only env, local Qdrant, metadata export off and frozen release identity):

```sh
/Users/vietvo/miniconda3/bin/python /tmp/uphill-followup-eval.py production compare --service scheduler --as-of 2026-10-05 --output-dir tests/golden/runs/reliability-followup14-production-1 --push-langfuse --synthetic-only --fail-on-regression
/Users/vietvo/miniconda3/bin/python /tmp/uphill-followup-eval.py scheduler-reliability-exp compare --service scheduler --as-of 2026-10-05 --output-dir tests/golden/runs/reliability-followup14-v15-1 --push-langfuse --synthetic-only --fail-on-regression --context-gates
```

For each repeat suffix repeat-1/repeat-2/repeat-3 append all five --fixture values: fixture_vietnam_urban_recreational_no_gym, fixture_vietnam_urban_recreational_treadmill, fixture_vietnam_urban_sub_elite_no_gym, fixture_vietnam_urban_sub_elite_treadmill, fixture_sequence_healthy_completed. Keep order production then candidate per pair. Inspect/tmp/uphill-followup14-{summary,review,costs,labels,manual-audit}.py before executing. Cost query must actually match canonical generation observations: zero traceName matches is a query problem, not zero cost; cross-check logged attempts/time/model/environment and retain unknown costs. Never expose keys.


Preview cleanup before handoff: owned tab7 closed, viewport override reset. Old owned tab6 remains unreachable and browser API refused closing it; no bypass attempted. UI backendPID 84808 and frontend npm parent PID 56811 received SIGINT; Verified both owned preview processes absent and no listeners on 3050/18010. No test accounts/plans were seeded, so no row cleanup needed. Scratch database/schema retained. Staging/production untouched.


Diagnostic direction if the fresh gate still fails: provider latency cause is unproven. Prior fixed-prompt MIME-only legacy requests produced complete7-day responses, whereas minItems=7 flat schema probes included both success and504. A separately reviewed variant could retain MIME-only production-v1 compatibility and local exact coverage while testing compact structured schemas only under the trusted candidate marker. This is a hypothesis, not an implemented correction or release recommendation. Never change the frozen gate mid-run; retain original failures and use new paired names/identities if changing request shape. Do not weaken the completeness check to accept fast single-workout outputs.

Read-only scratch verification: current_database exactly uphill_ai_test; total users2, plans0, owned v15-schema-evidence-synthetic account prefix0. Existing unrelated/default accounts retained; no row deletion or TRUNCATE.


Latest next action: review retained followup14 deadlines and decide whether to test the documented request-shape hypothesis. Any code change needs tests/review/freeze. Then a fresh complete eight-arm gate, manual EN/VI coaching review, actual responsive UI evidence, push/update draft PR82 and owner staging checkpoint. User goal remains continue until a version is releasable; this handoff is not completion of that goal.
