# Task F12 Brief: Render bilingual chat, sources and honest failures

## Goal
Build and ship the production-grade, bilingual Coach Chat user interface in `frontend/src/views/ChatTab.tsx` and the evidence drawer in `frontend/src/components/ChatSources.tsx`. Integrate `useCoachChat` as the sole state owner. Ensure bilingual support adhering to `uphill-ai-vietnamese-copy`. Enforce honest UI boundaries (no write tools, no Apply actions, no fabricated badges or unsupported claims).

## Architecture & Requirements
1. **Bilingual Chat View (`frontend/src/views/ChatTab.tsx`)**:
   - Consumes `useCoachChat()` exclusively for messages, streaming status, retry, pagination, clearing, and error state.
   - Header:
     - Color-coded status indicator dot (green = idle/ready, pulsing amber = retrieving/generating, red = error/interrupted).
     - Localized status label: "Ready" / "Sẵn sàng", "Retrieving training principles..." / "Đang tra cứu nguyên lý...", "Coach Uphill is thinking..." / "Coach Uphill đang trả lời...", "Interrupted" / "Bị gián đoạn", "Error" / "Lỗi".
     - Clear Chat button with localized confirmation dialog.
   - Honest Empty State:
     - Clear capability descriptions: 80/20 intensity, Zone 2 aerobic base, Muscular Endurance (ME), and race fueling.
     - Strict boundary notice: Coach chat explains principles and answers questions; it will not directly modify workouts or the active training schedule.
     - Zero tool rows, cards, Apply buttons, or false claims.
   - Message Stream & History:
     - Immediate user message rendering.
     - Streaming assistant token rendering with markdown formatting.
     - In-flight retrieval spinner and typing indicator.
     - Interrupted partial message preservation with amber badge and explicit "Retry" button linked to `request_id`.
     - "Sources" button with count badge on assistant messages with citations.
     - Pagination with "Load older messages" button.
   - Localized Error Banner:
     - Handles 429 quota errors (50 daily turns, 10 retries), 409 clear conflict, disabled status, and network errors in English and Vietnamese.
   - Input Bar:
     - Disabled during active streaming.
     - Quick preset prompt buttons for common coaching queries.
2. **Sources Drawer Component (`frontend/src/components/ChatSources.tsx`)**:
   - Sliding right-hand drawer with backdrop and accessible ESC key handling.
   - Renders referenced sources with domain tag (`scheduler`, `nutrition`), title, excerpt quote, and validated clickable external link (`target="_blank" rel="noopener noreferrer"`).
   - Renders retrieved context chunks.
   - Shows clean empty state if no citations were recorded for the message.
3. **Locale Dictionaries (`frontend/src/app/translations.ts`)**:
   - Added all UI strings to `en` and `vi` sections in full compliance with `uphill-ai-vietnamese-copy` rules (plain, direct `bạn`, technical terms in English, zero banned marketing superlatives).
4. **Live Caller Clean-up**:
   - `frontend/src/views/ChatView.tsx`: Delegates directly to `ChatTab`.
   - `frontend/src/app/app/page.tsx`: Removed dead `handleSendMessage` and obsolete chat destructurings.
5. **Colocated Unit Tests**:
   - `frontend/src/components/ChatSources.test.tsx`: backdrop, empty state, citation rendering, safe links, accessibility.
   - `frontend/src/views/ChatTab.test.tsx`: honest empty state, capabilities, lack of tool/apply buttons, retrieving/generating status, interrupted badge + retry, 429 quota error, 409 clear conflict, sources button, pagination.
