# Task F12 Report: Render bilingual chat, sources and honest failures

## Summary
Task F12 implements the production bilingual Coach Chat interface in `frontend/src/views/ChatTab.tsx` and the evidence drawer in `frontend/src/components/ChatSources.tsx`. It integrates `useCoachChat` as the single conversation state owner, updates the English and Vietnamese locale dictionaries in `frontend/src/app/translations.ts` in accordance with `uphill-ai-vietnamese-copy`, delegates `ChatView.tsx` to `ChatTab.tsx`, removes obsolete chat handlers from `page.tsx`, and provides unit tests in `ChatTab.test.tsx` and `ChatSources.test.tsx`.

## Components & Contracts Implemented
1. **Bilingual Chat Interface (`frontend/src/views/ChatTab.tsx`)**:
   - Sole conversation state consumer: Uses `useCoachChat()`.
   - Dynamic status dot and labels: Visual indicator transition between idle (green), retrieving/generating (pulsing amber), and interrupted/error (red).
   - Honest empty state: Documents core capabilities (80/20 intensity, Zone 2 aerobic base, Muscular Endurance, race fueling) and explicitly warns that chat does not modify workouts or the active schedule directly.
   - Strict boundary enforcement: No write tools, action cards, Apply buttons, or false capability claims are rendered.
   - In-flight feedback: Displays distinct spinners and typing indicators during retrieval and generation.
   - Interrupted response preservation: Retains partial streamed tokens, displays an amber `Interrupted` badge, and exposes a direct `Retry` action bound to the root turn UUID.
   - Citations & sources drawer: Assistant messages display a `Sources (N)` action button that opens `ChatSources`.
   - Pagination: Exposes a `Load older messages` action when `hasMore` is true.
   - Clear conversation: Provides a `Clear Chat` action with localized confirmation.
   - Localized error banner: Surfaces 429 turn/retry limits, 409 clear conflicts, service disabled notices, and network disconnects.
2. **Sources Drawer (`frontend/src/components/ChatSources.tsx`)**:
   - Modal drawer with dark aesthetic, ESC key listener, and backdrop dismissal.
   - Renders referenced sources with domain tags (`scheduler`, `nutrition`), titles, quote blocks, and safe outbound links (`target="_blank" rel="noopener noreferrer"`).
   - Renders retrieved context excerpts.
   - Shows clean empty notice in EN/VI when no external citations were recorded.
3. **Locale Dictionaries (`frontend/src/app/translations.ts`)**:
   - Added all 18 new UI keys across `en` and `vi` sections.
   - Adheres strictly to `uphill-ai-vietnamese-copy`: technical terms (`Zone 2`, `80/20`, `ME`, `Pace`, `Fueling`, `Trail`) remain in English; direct, plain register (`bạn`); banned marketing buzzwords avoided.
4. **Live Callers**:
   - `frontend/src/views/ChatView.tsx`: Simplified to a transparent wrapper around `ChatTab`.
   - `frontend/src/app/app/page.tsx`: Removed obsolete `handleSendMessage` and unused chat context variables.
5. **Colocated Unit Tests**:
   - `frontend/src/components/ChatSources.test.tsx`: Tests open/closed state, empty notice in EN/VI, citation rendering with safe links, and escape/close button handling.
   - `frontend/src/views/ChatTab.test.tsx`: Tests honest empty state, lack of write/apply buttons, retrieving/generating status labels, interrupted partial message with retry action, 429 and 409 error banners, sources inspection, pagination, and message sending.

## Files Touched
- Modified: `frontend/src/views/ChatTab.tsx`
- Created: `frontend/src/views/ChatTab.test.tsx`
- Created: `frontend/src/components/ChatSources.tsx`
- Created: `frontend/src/components/ChatSources.test.tsx`
- Modified: `frontend/src/views/ChatView.tsx`
- Modified: `frontend/src/app/app/page.tsx`
- Modified: `frontend/src/app/translations.ts`
- Created: `.superpowers/sdd/2026-09-20-coach-chat-foundation/task-F12-brief.md`
- Created: `.superpowers/sdd/2026-09-20-coach-chat-foundation/task-F12-report.md`
