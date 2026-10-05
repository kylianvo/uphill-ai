# Aborted structured-output compatibility run

Decision: HOLD / incomplete preflight. Frozen code 7de735c, backend91c37f3, production promptv1, candidate promptv15 unchanged. The production arm was stopped after repeated request deadlines to investigate the new provider-schema path. No candidate or repeat arm was dispatched. This is not a completed paired gate, and the later probes do not replace it.

Three partial scored cases remain: beginner primary/retry each hit the existing120-second deadline and used rules (242.8s case latency); eliteUTMB used primary (7.3s); masters primary timed out then retry succeeded (123.6s). A fourth in-flight request was cancelled. Six logged attempts match six metadata-only generations; known model cost$0.011472, four observation costs unavailable. Embeddings excluded. Preserve all negative evidence and original raw hashes. No timeout extension or score/fixture relaxation.

Operator stopped only the owned batch and child processes. The cancellation traceback is retained; no acceptance inference is made from incomplete observations. Client date2026-10-06; logs retain explicit execution-host UTC timestamps2026-10-05. No deployment or production/staging label change.
