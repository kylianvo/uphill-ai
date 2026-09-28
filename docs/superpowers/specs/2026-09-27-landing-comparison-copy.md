# Landing page: comparison section (copy proposal)

Status: draft for review. Nothing implemented yet.
Placement: new section on the home tab, directly under `FeatureGrid`.
Naming: categories with examples, no standalone brand columns.

## Layout

1. Section heading + one-line intro
2. Three highlight cards (the Scheduler story): Grounding, Context, Guardrails
3. Comparison table (desktop) / one stacked card per competitor category (mobile)
4. "Where the others fit better" line (honesty row)
5. Footnote: date of comparison and sources

---

## 1. Heading + intro

**EN**
- Heading: How Uphill AI compares
- Intro: You can ask ChatGPT or Claude for a plan, connect your COROS watch to them, or follow a plan app like Runna. Here is what changes when the plan comes from the Uphill AI Scheduler.

**VI**
- Heading: Uphill AI khác gì các lựa chọn khác
- Intro: Bạn có thể nhờ ChatGPT hay Claude lên plan, kết nối đồng hồ COROS với chúng, hoặc tập theo app như Runna. Đây là những gì khác đi khi plan do Scheduler của Uphill AI tạo ra.

---

## 2. Highlight cards

### Card A: Grounded, not improvised

**EN**
- Title: Grounded, not improvised
- Body: Every plan is built from a curated knowledge base of Uphill Athlete training principles (Scott Johnston). The Scheduler retrieves the relevant principles for your plan before writing a single workout. A general chatbot answers from whatever it learned on the web, so the method shifts with how you word the prompt.

**VI**
- Title: Dựa trên nguyên tắc, không tự chế
- Body: Mọi plan đều dựa trên thư viện kiến thức Uphill Athlete (Scott Johnston) đã được tuyển chọn. Scheduler lấy đúng các nguyên tắc liên quan trước khi viết buổi tập đầu tiên. Chatbot thông thường trả lời từ những gì nó học trên web, nên cách tập thay đổi theo cách bạn đặt câu hỏi.

### Card B: The context a coach would ask for

**EN**
- Title: The context a coach would ask for
- Body: The Scheduler reads your AeT/AnT HR, 7-day HRV, resting HR and training load from COROS, your biggest recent weeks, your UTMB and road race history, the course profile of your target race, your weekly schedule limits, and feedback from your last block. You don't paste anything in, and nothing is forgotten between chats.

**VI**
- Title: Đủ dữ liệu như một coach cần
- Body: Scheduler đọc AeT/AnT HR, HRV 7 ngày, Resting HR và training load từ COROS, các tuần khối lượng cao nhất gần đây, lịch sử Race UTMB và Road, profile đường chạy của Race mục tiêu, giới hạn lịch tập trong tuần và feedback của Block trước. Bạn không cần dán gì vào, và không có gì bị quên giữa các lần chat.

### Card C: Rules before it reaches your watch

**EN**
- Title: Rules before it reaches your watch
- Body: The AI draft is checked against training rules for your level: 80/20 intensity split, no Zone 4-5 in Base when your aerobic base is weak, volume capped when your acute:chronic load passes 1.4, hard days and long runs kept apart. If the AI response fails, you still get a rule-based plan. When a chatbot writes to COROS through MCP, nothing checks the plan first.

**VI**
- Title: Kiểm tra trước khi lên đồng hồ
- Body: Bản nháp của AI được kiểm tra theo quy tắc tập cho trình độ của bạn: tỷ lệ 80/20, không Zone 4-5 trong giai đoạn Base khi nền Aerobic còn yếu, giới hạn khối lượng khi ACWR vượt 1.4, không xếp buổi nặng sát Long Run. Nếu AI lỗi, bạn vẫn nhận được plan dựng theo quy tắc. Khi chatbot ghi plan vào COROS qua MCP, không có bước kiểm tra nào.

---

## 3. Comparison table

Columns:
1. Uphill AI
2. AI chat (ChatGPT, Claude)
3. AI chat + COROS MCP
4. Plan apps (Runna)
5. Watch plans (COROS Training Hub, Garmin Coach)

Cell legend: short text, not ticks. Ticks hide the nuance that makes the argument.

| Row (EN) | Uphill AI | AI chat | AI chat + COROS MCP | Plan apps (Runna) | Watch plans |
|---|---|---|---|---|---|
| Training method | Uphill Athlete principles from a curated KB | General web knowledge, varies by prompt | Same as AI chat | App's own method | Built-in templates or algorithm |
| Your data | COROS HR zones, HRV, load, activity history, race history | What you paste in | Reads COROS data when you ask | Onboarding answers + synced runs | The watch's own metrics |
| Trail specifics | Course profile (climbs, terrain, climate, GPX elevation), ME and hill work, treadmill incline per workout | Only if you describe it | Only if you describe it | [VERIFY] | [VERIFY] |
| Safety checks | Rules per level, 80/20 check, load caps, rule-based fallback | None | None; can write plans to your watch directly | Built into app logic | Built into device logic |
| Adapts over time | Block by block from your feedback and COROS readiness; weekly goal re-check | Only when you come back and ask | When you ask; up to 14 days scheduled at a time | Adjusts to level and schedule | Adjusts daily suggestions |
| Race goal | A/B/C times from your race history and the course | A guess | A guess using your data | Target pace | Race predictor |
| Human coach | Optional: coach reviews and approves workouts | No | No | No 1:1 coaching | No |
| Language | English and Vietnamese | Any | Any | [VERIFY] | [VERIFY] |
| Watches | COROS only | Any (manual) | COROS | Garmin, Apple Watch, COROS, Suunto, Fitbit | Own brand only |

VI row labels:

| EN | VI |
|---|---|
| Training method | Phương pháp tập |
| Your data | Dữ liệu của bạn |
| Trail specifics | Riêng cho Trail |
| Safety checks | Kiểm tra an toàn |
| Adapts over time | Điều chỉnh theo thời gian |
| Race goal | Mục tiêu Race |
| Human coach | Coach thật |
| Language | Ngôn ngữ |
| Watches | Đồng hồ hỗ trợ |

VI cells for the Uphill AI column (other columns translated at implementation):

| Row | VI |
|---|---|
| Training method | Nguyên tắc Uphill Athlete từ thư viện kiến thức đã tuyển chọn |
| Your data | HR zone, HRV, training load, lịch sử bài chạy từ COROS, lịch sử Race |
| Trail specifics | Profile đường chạy (dốc, địa hình, khí hậu, độ cao GPX), bài ME và Hill, độ dốc Treadmill cho từng buổi |
| Safety checks | Quy tắc theo trình độ, kiểm tra tỷ lệ 80/20, giới hạn load, plan dự phòng theo quy tắc |
| Adapts over time | Theo từng Block dựa trên feedback và chỉ số hồi phục từ COROS; đánh giá lại mục tiêu hằng tuần |
| Race goal | Thời gian A/B/C từ lịch sử Race và đường chạy |
| Human coach | Tuỳ chọn: coach duyệt từng buổi tập |
| Language | Tiếng Anh và tiếng Việt |
| Watches | Chỉ COROS |

---

## 4. Where the others fit better (honesty row)

**EN**
- Chatbots are better for open questions on any topic. Runna supports more watches and is strong for road races. If you run Garmin or Apple Watch, Uphill AI can't sync to your watch yet.

**VI**
- Chatbot hợp hơn cho câu hỏi mở về mọi chủ đề. Runna hỗ trợ nhiều đồng hồ hơn và mạnh ở Road Race. Nếu bạn dùng Garmin hay Apple Watch, Uphill AI chưa đồng bộ được với đồng hồ của bạn.

---

## 5. Footnote

**EN**: Compared in September 2026 from each product's public pages. Features change; tell us if something is out of date.
**VI**: So sánh vào tháng 9/2026 dựa trên trang công khai của từng sản phẩm. Tính năng có thể thay đổi; báo cho chúng tôi nếu thông tin đã cũ.

Sources:
- COROS MCP: https://support.coros.com/hc/en-us/articles/50841795180948-Connect-Your-COROS-to-AI (read + write; write from 21 Sep 2026; plans 4-16 weeks; scheduling up to 14 days; ChatGPT Plus / Claude Pro / Cursor; Gemini CLI only)
- Runna: https://marathonscout.com/training/runna (5K-50K, watch list, no 1:1 coaching, $19.99/mo)

## Claims checked against code

| Claim | Where |
|---|---|
| KB retrieval for Scheduler | `services/kb_retrieval.py`, Qdrant `uphill_kb_scheduler` |
| HRV / RHR / ACWR / recovery in prompt | `plan_generator.py` "7-DAY WEARABLE BIOLOGICAL READINESS" block |
| ACWR > 1.4 cap | same block |
| ADS rule (no Z4-5 in Base/Build) | `plan_rules.py` rule 6 |
| 80/20 check | `training_rules.py:audit_80_20` |
| Hard day / long run spacing | `calendar_rules.py` |
| Rule-based fallback | Scheduler fallback tiers (CLAUDE.md) |
| Course profile | `race_info.course_context`, `course_profiles` payload |
| Race history in prompt | `services/race_history.py` |
| Treadmill incline per workout | `PlanGenerator.resolve_treadmill_settings` |

Not claimed on purpose: Gemini goal judge (`GOAL_LLM_ENABLED` is off by default), per-user keys for gear/nutrition.
