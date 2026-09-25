# Early Adopter Feedback & UX Improvements Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement 6 user feedback improvements: profile save success alert, watch zones & thresholds helper modal, delete recent plan endpoint & custom dropdown, display race target time on active plan, workout content readability with 1-click execution steps, and action confirmation modals.

**Architecture:**
- Backend: Expose `DELETE /api/coach/plans/{plan_id}` in `backend/main.py` using `delete_plan` in `backend/db.py` with ownership validation. Cascading DB foreign keys ensure child workouts and blocks are cleanly removed.
- Frontend: Add `WatchZonesGuideModal.tsx` and `ConfirmActionModal.tsx` components. Enhance `ProfileSettingsModal.tsx` with save success feedback and helper links. Update `PlannerView.tsx` with a custom recent-plans dropdown with delete actions, target time formatting, and action confirmations. Update `WorkoutCard.tsx` for 1-click execution access and 14px typography.

**Architecture Diagram:**

```mermaid
graph TD
    subgraph "Backend (FastAPI & SQLite/Postgres)"
        API["DELETE /api/coach/plans/{plan_id}"] --> DB["delete_plan(plan_id, user_id)"]
        DB --> CASCADE["CASCADE workouts, scheduled_blocks, weekly_reviews"]
    end

    subgraph "Frontend Components"
        PSM["ProfileSettingsModal.tsx"] -->|Save Success Alert| UI1["Green Banner & triggerHaptic"]
        PSM -->|(? Help Link)| WZGM["WatchZonesGuideModal.tsx"]
        OW["OnboardingWizard.tsx"] -->|(? Help Link)| WZGM
        PV["PlannerView.tsx"] -->|Custom Dropdown| DEL["Delete Plan Action"]
        DEL --> API
        PV -->|Active Plan Header| TIME["Format & display target_time_hours"]
        PV -->|Generate Plan| CAM["ConfirmActionModal.tsx"]
        PV -->|Generate Next Block| CAM
        AWM["AdaptWeekModal.tsx"] -->|Regenerate Week| CAM
        WC["WorkoutCard.tsx"] -->|Click Header / Expand| EXEC["1-Click Execution Timeline (14px font)"]
    end
```

**Tech Stack:**
- Frontend: Next.js (React 19), TypeScript, Phosphor Icons, Vanilla CSS
- Backend: FastAPI, SQLAlchemy, Pydantic, pytest
- Testing: Vitest (Frontend), Pytest (Backend)

---

### Task 1: Save Settings Profile Alert in `ProfileSettingsModal.tsx`

**Files:**
- Modify: `frontend/src/views/ProfileSettingsModal.tsx`
- Test: `frontend/src/views/ProfileSettingsModal.test.tsx` (or new test)

- [ ] **Step 1: Write the test verifying save profile shows success message**

In `frontend/src/views/ProfileSettingsModal.test.tsx`:
```tsx
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import React from "react";
import ProfileSettingsModal from "./ProfileSettingsModal";
import { AppContext } from "../contexts/AppContext";

describe("ProfileSettingsModal Save Success", () => {
  const mockSetUser = vi.fn();
  const mockContextValue = {
    lang: "en",
    user: { id: 1, name: "Test Runner", email: "runner@test.com" },
    setUser: mockSetUser,
    profileSettingsOpen: true,
    setProfileSettingsOpen: vi.fn(),
    profileForm: {
      age: "30",
      gender: "male",
      height_cm: "175",
      weight_kg: "70",
      max_hr: "185",
      resting_hr: "50",
      aet_hr: "140",
      ant_hr: "168",
      zone2_pace_min: "5:30",
      zone2_pace_max: "5:00",
      gemini_api_key: "",
    },
    setProfileForm: vi.fn(),
    setAuthModalOpen: vi.fn(),
    setOnboardingOpen: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.setItem("uphill_session_token", "fake-token");
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ id: 1, name: "Test Runner", aet_hr: 140 }),
    }) as any;
  });

  it("displays success alert banner after successful profile save", async () => {
    render(
      <AppContext.Provider value={mockContextValue as any}>
        <ProfileSettingsModal />
      </AppContext.Provider>
    );

    const saveButton = screen.getByRole("button", { name: /save settings|save profile/i });
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(screen.getByText(/profile updated successfully/i)).toBeInTheDocument();
    });
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npm test -- src/views/ProfileSettingsModal.test.tsx`
Expected: FAIL (no success message found)

- [ ] **Step 3: Implement success alert in `ProfileSettingsModal.tsx`**

1. Add state `const [profileSaveSuccess, setProfileSaveSuccess] = useState(false);`
2. In `handleSaveProfile`:
   - On success: `setProfileSaveSuccess(true); triggerHaptic();`
   - Set timeout to auto-clear after 4000ms: `setTimeout(() => setProfileSaveSuccess(false), 4000);`
3. In JSX, render a green banner above the form if `profileSaveSuccess`:
```tsx
{profileSaveSuccess && (
  <div style={{
    background: "rgba(16, 185, 129, 0.12)",
    border: "1px solid rgba(16, 185, 129, 0.4)",
    borderRadius: "10px",
    padding: "12px 16px",
    display: "flex",
    alignItems: "center",
    gap: "10px",
    color: "#059669",
    fontWeight: "600",
    fontSize: "13px",
    marginBottom: "16px",
  }}>
    <CheckCircle size={18} weight="fill" color="#10b981" />
    <span>{t("profile_update_success")}</span>
  </div>
)}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npm test -- src/views/ProfileSettingsModal.test.tsx`
Expected: PASS

- [ ] **Step 5: Commit changes**

```bash
git add frontend/src/views/ProfileSettingsModal.tsx frontend/src/views/ProfileSettingsModal.test.tsx
git commit -m "feat(profile): display success banner and haptic feedback on save"
```

---

### Task 2: Watch Zones & Thresholds Helper Modal (`WatchZonesGuideModal.tsx`)

**Files:**
- Create: `frontend/src/components/WatchZonesGuideModal.tsx`
- Test: `frontend/src/components/WatchZonesGuideModal.test.tsx`
- Modify: `frontend/src/views/ProfileSettingsModal.tsx`
- Modify: `frontend/src/views/OnboardingWizard.tsx`

- [ ] **Step 1: Write test for `WatchZonesGuideModal`**

In `frontend/src/components/WatchZonesGuideModal.test.tsx`:
```tsx
import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import React from "react";
import WatchZonesGuideModal from "./WatchZonesGuideModal";

describe("WatchZonesGuideModal", () => {
  it("renders platform guides and copy prompt button", async () => {
    const onClose = vi.fn();
    render(<WatchZonesGuideModal isOpen={true} onClose={onClose} lang="en" />);

    expect(screen.getByText(/Garmin/i)).toBeInTheDocument();
    expect(screen.getByText(/COROS/i)).toBeInTheDocument();
    expect(screen.getByText(/Apple Watch/i)).toBeInTheDocument();

    const copyBtn = screen.getByRole("button", { name: /copy prompt/i });
    expect(copyBtn).toBeInTheDocument();
    
    // Mock navigator.clipboard
    Object.assign(navigator, {
      clipboard: {
        writeText: vi.fn().mockResolvedValue(undefined),
      },
    });

    fireEvent.click(copyBtn);
    expect(navigator.clipboard.writeText).toHaveBeenCalled();
    expect(await screen.findByText(/copied!/i)).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npm test -- src/components/WatchZonesGuideModal.test.tsx`
Expected: FAIL (file does not exist)

- [ ] **Step 3: Implement `WatchZonesGuideModal.tsx`**

Build modal with:
1. Platforms: Garmin, COROS, Apple Watch, Suunto/Polar.
2. Threshold definitions (AeT, AnT).
3. Copyable prompt card with 1-click clipboard copy:
   - Text EN: `"I am an endurance runner. Here is a screenshot of my Heart Rate Zones and resting/max HR from my watch. Please extract: 1) AeT (Aerobic Threshold - upper edge of Zone 2), 2) AnT (Anaerobic / Lactate Threshold - upper edge of Zone 4), 3) Resting HR, 4) Max HR."`
   - Text VI: `"Tôi là vận động viên chạy bộ bền bỉ. Đây là ảnh chụp màn hình các Vùng Nhịp Tim (Heart Rate Zones) và nhịp tim nghỉ/tối đa từ đồng hồ của tôi. Hãy trích xuất giúp tôi: 1) AeT (Ngưỡng hiếu khí - giới hạn trên của Zone 2), 2) AnT (Ngưỡng kỵ khí / lactate threshold - giới hạn trên của Zone 4), 3) Nhịp tim nghỉ ngơi (Resting HR), 4) Nhịp tim tối đa (Max HR)."`
4. Wire into `ProfileSettingsModal.tsx` next to `profile_aet_hr` and `profile_ant_hr` labels with a clickable button: `(? How to find from your watch / Xem cách lấy từ đồng hồ)`.
5. Wire into `OnboardingWizard.tsx` fitness step.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npm test -- src/components/WatchZonesGuideModal.test.tsx`
Expected: PASS

- [ ] **Step 5: Commit changes**

```bash
git add frontend/src/components/WatchZonesGuideModal.tsx frontend/src/components/WatchZonesGuideModal.test.tsx frontend/src/views/ProfileSettingsModal.tsx frontend/src/views/OnboardingWizard.tsx
git commit -m "feat(physio): add watch zones & thresholds helper modal with AI prompt"
```

---

### Task 3: Backend Delete Plan API

**Files:**
- Modify: `backend/db.py`
- Modify: `backend/main.py`
- Test: `backend/tests/integration/test_delete_plan.py`

- [ ] **Step 1: Write integration tests for plan deletion**

In `backend/tests/integration/test_delete_plan.py`:
```python
import pytest
from fastapi.testclient import TestClient
from main import app
from db import create_plan, get_plan_by_id, create_user

client = TestClient(app)

def test_delete_own_plan(auth_headers):
    user_id = auth_headers["user_id"]
    headers = auth_headers["headers"]
    plan_id = create_plan(user_id=user_id, race_name="Test Race", race_date="2026-10-10", goal_type="finish", total_weeks=12)
    assert get_plan_by_id(plan_id) is not None

    resp = client.delete(f"/api/coach/plans/{plan_id}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["success"] is True
    assert get_plan_by_id(plan_id) is None

def test_delete_other_user_plan_forbidden(auth_headers):
    other_user = create_user("other@test.com", "hash", "Other")
    plan_id = create_plan(user_id=other_user["id"], race_name="Other Race", race_date="2026-10-10", goal_type="finish", total_weeks=12)

    resp = client.delete(f"/api/coach/plans/{plan_id}", headers=auth_headers["headers"])
    assert resp.status_code == 404
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest backend/tests/integration/test_delete_plan.py -v`
Expected: FAIL (404 or 405 Method Not Allowed)

- [ ] **Step 3: Implement `delete_plan` in `db.py` and endpoint in `main.py`**

In `backend/db.py`:
```python
def delete_plan(plan_id: int, user_id: int) -> bool:
    """Delete a plan belonging to user_id. Cascades to workouts, blocks, and reviews."""
    with engine.connect() as conn:
        res = conn.execute(
            text("DELETE FROM plans WHERE id = :plan_id AND user_id = :user_id"),
            {"plan_id": plan_id, "user_id": user_id}
        )
        conn.commit()
        return res.rowcount > 0
```

In `backend/main.py`:
```python
@app.delete("/api/coach/plans/{plan_id}")
def delete_user_plan(plan_id: int, user: dict[str, Any] = Depends(get_current_user)):
    """Delete a training plan owned by the current user."""
    _verify_plan_ownership(plan_id, user["id"])
    success = delete_plan(plan_id, user["id"])
    if not success:
        raise HTTPException(status_code=404, detail="Plan not found.")
    return {"success": True, "deleted_plan_id": plan_id}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest backend/tests/integration/test_delete_plan.py -v`
Expected: PASS

- [ ] **Step 5: Commit changes**

```bash
git add backend/db.py backend/main.py backend/tests/integration/test_delete_plan.py
git commit -m "feat(plans): add DELETE /api/coach/plans/{plan_id} endpoint"
```

---

### Task 4: Delete Recent Plan UI in `PlannerView.tsx`

**Files:**
- Modify: `frontend/src/views/PlannerView.tsx`
- Modify: `frontend/src/hooks/usePlanner.ts`
- Test: `frontend/src/views/PlannerView.test.tsx`

- [ ] **Step 1: Write test for plan deletion in UI**

In `frontend/src/views/PlannerView.test.tsx`:
```tsx
it("renders delete button on recent plan item and invokes delete API upon confirmation", async () => {
  // Test that clicking trash icon on a recent plan prompts confirmation and calls DELETE /api/coach/plans/:id
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npm test -- src/views/PlannerView.test.tsx`
Expected: FAIL

- [ ] **Step 3: Implement custom dropdown and delete action in `PlannerView.tsx`**

1. Replace the `<select>` in `PlannerView.tsx` with a custom dropdown:
   - A button showing "Load Recent Plan..." with a caret.
   - When clicked, a popup menu displays each plan formatted with name, race date, distance.
   - Each item has a trash can button `<Trash size={14} color="#ef4444" />`.
2. Add `handleDeletePlan(planId: number, planName: string)`:
   - Shows confirmation prompt: `window.confirm` or `ConfirmActionModal`.
   - Sends `DELETE /api/coach/plans/${planId}`.
   - If `activePlan?.id === planId`, clears active plan.
   - Refetches `recentPlans`.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npm test -- src/views/PlannerView.test.tsx`
Expected: PASS

- [ ] **Step 5: Commit changes**

```bash
git add frontend/src/views/PlannerView.tsx frontend/src/hooks/usePlanner.ts
git commit -m "feat(planner): custom recent plans dropdown with delete plan action"
```

---

### Task 5: Display Inputted Race Target Time on Active Plan

**Files:**
- Modify: `frontend/src/views/PlannerView.tsx`
- Test: `frontend/src/views/PlannerView.test.tsx`

- [ ] **Step 1: Write test verifying target time formatted in active plan header**

In `frontend/src/views/PlannerView.test.tsx`:
```tsx
it("displays inputted target time in active plan header when target_time_hours is present", () => {
  const planWithTarget = {
    id: 1,
    race_name: "UTMB",
    race_date: "2026-08-28",
    goal_type: "time",
    target_time_hours: 8.5,
    total_weeks: 16,
  };
  // render PlannerView with activePlan = planWithTarget
  // verify "8h 30m" is displayed in the header subtitle
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npm test -- src/views/PlannerView.test.tsx`
Expected: FAIL (target time not found in subtitle)

- [ ] **Step 3: Implement target time display in `PlannerView.tsx`**

1. Add helper function `formatTargetTimeHours(hours: number): string`:
   ```ts
   export function formatTargetTimeHours(hours: number): string {
     const h = Math.floor(hours);
     const m = Math.round((hours - h) * 60);
     if (h === 0) return `${m}m`;
     if (m === 0) return `${h}h`;
     return `${h}h ${m}m`;
   }
   ```
2. In the plan header metadata (lines 1250-1257):
   ```tsx
   <p style={{ color: "var(--text-secondary)", fontSize: "12px", marginTop: "2px", fontWeight: "500" }}>
     {(() => {
       const goal = activePlan.goal_type || "";
       if (["start_running", "return", "recovery"].includes(goal)) {
         return lang === "en" ? `Block ends: ${activePlan.race_date}` : `Kết thúc: ${activePlan.race_date}`;
       } else {
         return lang === "en" ? `Race Day: ${activePlan.race_date}` : `Ngày đua: ${activePlan.race_date}`;
       }
     })()} | {activePlan.goal_type === "finish"
       ? (lang === "en" ? "Simply Finish" : "Chỉ cần Hoàn thành")
       : activePlan.goal_type === "time"
         ? (lang === "en" ? "Time Target" : "Mục tiêu Thời gian")
         : activePlan.goal_type === "optimal"
           ? (lang === "en" ? "Optimal Performance" : "Hiệu suất Tối ưu")
           : activePlan.goal_type.toUpperCase().replace("_", " ")}
     {activePlan.target_time_hours ? ` (${formatTargetTimeHours(activePlan.target_time_hours)})` : ""}
   </p>
   ```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npm test -- src/views/PlannerView.test.tsx`
Expected: PASS

- [ ] **Step 5: Commit changes**

```bash
git add frontend/src/views/PlannerView.tsx
git commit -m "feat(planner): display formatted race target time in active plan header"
```

---

### Task 6: Workout Readability & 1-Click Execution Steps in `WorkoutCard.tsx`

**Files:**
- Modify: `frontend/src/components/WorkoutCard.tsx`
- Test: `frontend/src/components/WorkoutCard.test.tsx`

- [ ] **Step 1: Write test verifying execution steps are visible on card expand**

In `frontend/src/components/WorkoutCard.test.tsx`:
```tsx
it("reveals execution steps immediately when card is expanded with single click", () => {
  const wo = {
    id: 1,
    title: "Aerobic Base Run",
    type: "Easy Run",
    duration_minutes: 60,
    target_zone: "Zone 2",
    description: "Warm-up: 10 min easy. Main set: Run 45 min at Zone 2. Cool-down: 5 min walk.",
    day_of_week: "Monday",
    approved_at: "2026-09-01T00:00:00Z",
  };
  render(<WorkoutCard wo={wo as any} isMobile={false} lang="en" getWorkoutDate={() => "Sep 1"} defaultExpanded={true} />);
  expect(screen.getByText(/Run 45 min at Zone 2/i)).toBeInTheDocument();
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npm test -- src/components/WorkoutCard.test.tsx`
Expected: FAIL (steps hidden because `mainExpanded` is false)

- [ ] **Step 3: Implement 1-click execution and typography update in `WorkoutCard.tsx`**

1. Change `const [mainExpanded, setMainExpanded] = useState(true);` (default to `true` instead of `false`).
2. Add `onClick={() => setExpanded(!expanded)}` to the card header area so clicking the card title or row expands the card directly (while keeping child interactive buttons like checkboxes and edit icons from propagating using `e.stopPropagation()`).
3. Update font sizes:
   - Change step text `fontSize` from `"12.5px"` to `"14px"`.
   - Change overview description `fontSize` from `"13px"` to `"14px"`.
   - Set `lineHeight: "1.6"`.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npm test -- src/components/WorkoutCard.test.tsx`
Expected: PASS

- [ ] **Step 5: Commit changes**

```bash
git add frontend/src/components/WorkoutCard.tsx frontend/src/components/WorkoutCard.test.tsx
git commit -m "feat(workout): 1-click execution guide access and 14px typography"
```

---

### Task 7: Action Confirmation Modal (`ConfirmActionModal.tsx`)

**Files:**
- Create: `frontend/src/components/ConfirmActionModal.tsx`
- Test: `frontend/src/components/ConfirmActionModal.test.tsx`
- Modify: `frontend/src/views/PlannerView.tsx`
- Modify: `frontend/src/components/AdaptWeekModal.tsx`

- [ ] **Step 1: Write test for `ConfirmActionModal`**

In `frontend/src/components/ConfirmActionModal.test.tsx`:
```tsx
import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import React from "react";
import ConfirmActionModal from "./ConfirmActionModal";

describe("ConfirmActionModal", () => {
  it("renders title, description, details and handles confirmation", () => {
    const onConfirm = vi.fn();
    const onCancel = vi.fn();
    render(
      <ConfirmActionModal
        isOpen={true}
        title="Generate Block 2"
        description="Coach Uphill AI will generate your next 2-week training block."
        confirmLabel="Confirm & Generate"
        cancelLabel="Cancel"
        onConfirm={onConfirm}
        onCancel={onCancel}
        details={[
          { label: "Race", value: "UTMB 50K" },
          { label: "Weeks", value: "Weeks 3 - 4" },
        ]}
      />
    );

    expect(screen.getByText("Generate Block 2")).toBeInTheDocument();
    expect(screen.getByText("UTMB 50K")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /confirm & generate/i }));
    expect(onConfirm).toHaveBeenCalled();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npm test -- src/components/ConfirmActionModal.test.tsx`
Expected: FAIL (file does not exist)

- [ ] **Step 3: Implement `ConfirmActionModal.tsx` and wire into actions**

1. Create `frontend/src/components/ConfirmActionModal.tsx` using `createPortal` with clean glassmorphic card, action summary, and confirm/cancel buttons.
2. In `PlannerView.tsx`:
   - Intercept `handleGeneratePlan`: If not yet confirmed, open `ConfirmActionModal`. When confirmed, proceed with generation.
   - Intercept `handleGenerateNextBlock`: Open confirmation dialog summarizing the upcoming block parameters.
3. In `AdaptWeekModal.tsx`:
   - Intercept form submit: Confirm before submitting week adaptation job.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npm test -- src/components/ConfirmActionModal.test.tsx`
Expected: PASS

- [ ] **Step 5: Commit changes**

```bash
git add frontend/src/components/ConfirmActionModal.tsx frontend/src/components/ConfirmActionModal.test.tsx frontend/src/views/PlannerView.tsx frontend/src/components/AdaptWeekModal.tsx
git commit -m "feat(planner): add ConfirmActionModal for plan generation, next block, and adaptation"
```

---

### Task 8: Full Verification & Browser Evidence

**Files:**
- Run full backend & frontend test suites
- Capture screenshots for verification

- [ ] **Step 1: Run backend tests**

Run: `pytest backend/tests/ -v`
Expected: ALL PASS

- [ ] **Step 2: Run frontend tests & lint**

Run: `cd frontend && npm run test && npm run lint`
Expected: ALL PASS

- [ ] **Step 3: Capture browser screenshot evidence**

Start local server and verify all modified components visually:
- Profile Settings save alert banner
- Watch Zones Guide Modal
- Recent Plans custom dropdown with delete
- Active Plan target time display
- Workout card with expanded execution steps and 14px font
- Confirm action dialog
