---
name: uphill-ai-vietnamese-copy
description: Use when writing, reviewing, or translating any Vietnamese (vi) UI copy, strings, or LLM prompt output for the Uphill AI trail-running app — including every new feature that ships a VI version.
---

# Vietnamese copy for Uphill AI

Uphill AI is bilingual EN / VI. **English is the source of truth.** Every new feature
ships both. This skill is the contract for the VI side.

Audience: Vietnamese trail and ultra runners. They code-switch constantly and expect
English for technical terms. Vietnamese-ifying a word the community says in English is
the single biggest tell that copy was machine-written.

## Where VI copy lives

| Location | What |
|---|---|
| `frontend/src/app/translations.ts` | `vi: { }` key/value block |
| `frontend/src/data/landingFeatures.ts` | per-feature `vi: {}` blocks (tagline, cardBlurb, overview, howItWorks, personalizedNote, chips, alwaysUpdated) |
| `frontend/src/data/glossary.ts` | `vi` term definitions |
| `frontend/src/app/privacy/content.ts` | VI legal copy |
| inline `{lang === "en" ? EN : VI}` ternaries | the bulk — concentrated in `views/PlannerView.tsx`, `views/OnboardingWizard.tsx`, `views/CoachDashboardView.tsx`, `components/WorkoutCard.tsx`, `views/ProfileSettingsModal.tsx` |
| `backend/services/plan_generator.py` | `lang_rule` block + `lang_instruction` — governs generated VI coaching text |
| `backend/services/knowledge_extractor.py` | VI knowledge-card translation prompt |
| `backend/routers/integrations.py` | VI number/date formatting rules |

Never edit `.bak` files, `node_modules`, `.venv`, `.claude/worktrees/`, or
`_pre_pull_backup_*`.

## R1 — Keep in English, never translate

`Pace`, `Easy Run`, `Long Run`, `Tempo`, `Threshold`, `Interval`, `Fartlek`, `Surges`,
`Recovery Run`, `Hill Repeat`, `Hill Sprint`, `Hill Bound`, `Muscular Endurance` / `ME`,
`Strength`, `Zone 1`–`Zone 5`, `AeT`, `AnT`, `HR`, `Max HR`, `Resting HR`, `RPE`,
`Cadence`, `Deload`, `Taper`, `Block`, `Split`, `Checkpoint`, `CP`, `Cutoff` / `COT`,
`DNF`, `Elevation Gain` / `D+`, `GPX`, `Race`, `Ultra`, `Trail`, `Road`, `Treadmill`,
`Gel`, `Chews`, `Carbs`, `Sodium`, `Electrolytes`, `Fueling`, `Gut training`,
`Stack Height`, `Drop`, `Carbon Plate`, `Lug Depth`, `Foam Rolling`, `Warm-up`,
`Cool-down`, `Strides`, `Plan`, `Coach`, `Aerobic`, `Anaerobic`, `Aerobic decoupling`.

Gloss in parentheses **only on first use in a form field label** —
`Resting HR (nhịp tim lúc nghỉ)`. Never gloss the same term twice on one screen.

## R2 — Fixed term mappings

| English | ❌ Never | ✅ Use |
|---|---|---|
| Volume / weekly volume | `thể tích` | `khối lượng`, `khối lượng tuần` |
| Physiology / physiological | `sinh lý` | `thể chất`, `chỉ số thể chất` |
| Pace | `tốc độ` | `pace` (tốc độ = km/h, different thing) |
| Fueling | `tiếp nhiên liệu` | `fueling`, `dinh dưỡng thi đấu` |
| Training plan | `giáo án` | `plan`, `lịch tập`, `kế hoạch tập` |
| Workout / session | `bài tập thể dục` | `buổi tập`, `bài chạy` |
| Generate a plan | `kiến tạo` | `tạo plan`, `lên plan` |
| Knowledge base | `kho tri thức` | `kho kiến thức`, `thư viện kiến thức` |
| Grounded / traceable | `bảo chứng` | `dựa trên`, `truy được về nguồn` |
| Curated catalog | `danh mục chính hãng` | `danh mục đã tuyển chọn` |
| How it works | `Hệ thống vận hành như thế nào?` | `Cách hoạt động` |

## R3 — Ban list

Delete on sight and rewrite the sentence:
`kiến tạo`, `bảo chứng`, `chinh phục đỉnh cao`, `bứt phá`, `nâng tầm`, `vượt trội`,
`tối ưu hóa`, `toàn diện`, `chuyên sâu`, `độc quyền`, `đột phá`, `mạnh mẽ`, `tuyệt vời`,
`uy tín hàng đầu`, `chuẩn mực thế giới`, `đắm chìm`, `hành trình` (as metaphor),
`giải pháp`, `thấu hiểu`, `đồng hành cùng bạn`, `vận hành` (for software),
`kiểm toán` (for 80/20 checks — say `kiểm tra tỷ lệ 80/20`), `tri thức`, `hệ sinh thái`.

Also ban: three-deep em-dash parallel constructions, and the `không chỉ X — mà là Y`
pattern. One idea per sentence.

## R4 — Meaning parity

Each VI string says **exactly what the EN string says** — no added superlatives, no
added product claims, no dropped caveats. VI is a translation, not a rewrite, and never
a sales pitch.

Bad: EN "The full distilled catalog is injected for every query, so nothing gets missed
to a semantic-search near-miss." → VI "Nạp toàn bộ danh mục sản phẩm vào ngữ cảnh xử lý,
đảm bảo tìm ra đôi giày phù hợp nhất với đặc tính của bạn." (invented a different claim)

Good: "Toàn bộ danh mục được nạp vào mỗi lần hỏi, nên không mẫu nào bị bỏ sót vì tìm
kiếm gần đúng."

## R5 — Register

Write like a coach talking to a runner in a club Zalo group: plain, direct, second person
`bạn`, short sentences, active verbs. No exclamation marks except on genuine success
toasts. No rhetorical questions in headings. Sentence case for body copy.

## R6 — Mechanical

- Change only the VI side of a ternary; never touch the EN string or the object key.
- Preserve `{{term:...}}` / `{{/term}}` pairs and template interpolations (`${...}`).
- VI must be no longer than the EN — buttons and chips overflow. Chips/labels: max 3 words.
- New user-facing string ⇒ VI added in the same commit. No English fallback shipped.

## Checklist for a new feature

1. Write the EN copy first and get it right.
2. Add the VI in the same file/commit, applying R1–R6.
3. If the feature generates text via an LLM, add the VI style contract to that prompt —
   don't rely on "Respond in Vietnamese."
4. Verify:

```bash
cd frontend && npm run lint && npm run test && npm run build
cd src && grep -rn "thể tích\|sinh lý\|kiến tạo\|bảo chứng\|tiếp nhiên liệu\|kiểm toán" \
  --include=*.ts --include=*.tsx . | grep -v "\.bak"   # expect empty
```

5. Read the new screen in VI in the browser and check for button/chip overflow.

## When the right Vietnamese is genuinely unclear

Leave the term in English rather than inventing one, and flag it for a human call.
