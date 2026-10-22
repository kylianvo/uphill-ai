# Haiku plan generation: free evaluation (2026-10-22)

No paid calls. Plan: `docs/superpowers/plans/2026-10-23-haiku-plan-generation.md`, Tasks 5–6.

## 1. Gemini baseline, replayed through today's post-processing

Saved Gemini rows from the 2026-10-21 paid run (`/tmp/personas`), replayed on a scratch DB. The 5 new personas have no saved rows, so they ran entirely on the rules (marked "rules only").

| Persona | Quality | Persona-check fails |
|---|---|---|
| novice_trail_half | 9/10 | 0 |
| recreational_50k | 8/10 | progression (325 → 350 min) |
| elite_100k | 10/10 | 0 |
| ultra_100_miles | 10/11 | ladder: QUALITY_COUNT wk 5–11 |
| road_marathon | 8/9 | 0 |
| busy_3day_50k | 10/11 | progression |
| quang_aptrc80 | 6/10 | ladder: QUALITY_COUNT wk 1–7 |
| vn_hcmc_chau_thoi_50k_vi | 9/12 | 0 |
| vn_hanoi_ham_lon_100k_vi | 8/11 | 0 |
| vn_flat_city_treadmill_only | 10/12 | 0 |
| vn_masters_100k_gated_vi (rules only) | 10/12 | 0 |
| sub_elite_100mi_mountain (rules only) | 8/10 | ladder: WEEKDAY_SHORT wk 4, QUALITY_COUNT wk 10–15 |
| low_base_50k_mountain_10wk (rules only) | 6/11 | DAYS_SHORT wk 4 |
| short_8wk_100k_mountain (rules only) | 8/10 | 0 |
| vi_beginner_10k_road (rules only) | 9/9 | DAYS_SHORT wk 1, 2, 4 |

### Gaps the new personas surfaced (from #171 or older, not caused by this branch)

- **Wrong quality count, rules-only plan:** `sub_elite_100mi_mountain` is built entirely by the rules. It still gets the wrong number of quality sessions in weeks 10–15, and week 4 has a weekday run below the minimum.
- **Uphill-interval step minutes don't add up:** in `quang_aptrc80`, `vn_hcmc`, `vn_hanoi` and `low_base`, the steps sum to 38 min against a 61 min session.
- **`plan_quality` disagrees with the ultra rules:**
  - "No Zone 3–5 work while the aerobic base is deficient" flags the 1 Zone 3 session a week that gated runners get by decision.
  - "No long Zone 3 over 75 min" flags quality sessions of up to 90 min, which the ultra rules allow.
- **DAYS_SHORT on short plans:** the rules don't fill the athlete's days in `vi_beginner_10k_road` and `low_base_50k_mountain_10wk`.

## 2. Haiku, prompt only (Claude Code subagent on `haiku`, week 1)

| Persona | JSON | Week 1 after post-processing | Notes |
|---|---|---|---|
| quang_aptrc80 | valid, 7 rows | ME, Easy 60, Zone 3 intervals 60, Easy 60, Sat 85, Sun Long Run 180 | 180 min long run is correct. QUALITY_COUNT is flagged because the coach's window starts later; the prompt's week 1 line allowed Zone 3 |
| vn_masters_100k_gated_vi | valid, 7 rows | Easy 60 ×3, ME 45, Sat Long Run 180, Sun Recovery 60 | Weekdays 60 min, matching the ladder. No Zone 3 outside the window. Vietnamese copy |
| vi_beginner_10k_road | valid, 7 rows | Walk/Run 25, 25, 30 | Correct type for a beginner. No ultra rules leaked in |

All three answers were valid JSON on the first try. In both mountain plans Haiku put the long run on the mountain day at 180 min. Haiku also reported that the prompt contradicts itself: "other weekend day ≤ 90 min" against "no back-to-back weekend". This is not the gate, because the subagent had its own system prompt and no effort setting.

## 3. Claude prompt draft

`backend/prompts/plan_generation.claude.txt` has the same rules and `{{variables}}` (a test pins this). The changes:
- the all-caps MUST/NEVER wording is softened;
- each rule now says why it exists (the app parses the JSON; the app renders one step per segment).

It goes to Langfuse as `claude-development` in Task 6.

## Next (paid; needs a go-ahead)

Task 6:
- Gemini runs for the 5 new personas.
- Claude runs at low, then medium (then high if budget remains), $5 cap.
- Golden gate.
- Coach review packs.
