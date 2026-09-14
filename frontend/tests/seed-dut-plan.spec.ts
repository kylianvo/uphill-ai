import { test, expect } from "@playwright/test";

const DALAT_USER = {
  id: 1,
  name: "Dalat Ultra Runner",
  email: "dut-runner@uphill.ai",
  age: 33,
  gender: "male",
  height_cm: 175,
  weight_kg: 68,
  aet_hr: 142,
  ant_hr: 165,
  max_hr: 185,
  resting_hr: 48,
  zone2_pace_min: "6:30",
  zone2_pace_max: "5:45",
  onboarding_complete: true,
};

const DALAT_PLAN = {
  id: 101,
  race_name: "Dalat Ultra Trail (DUT)",
  race_date: "2027-03-27",
  start_date: "2026-12-07",
  goal_type: "finish",
  total_weeks: 16,
  course_distance_km: 100.0,
  course_elevation_gain_m: 2079,
  terrain: "trail",
  target_time_hours: null,
  plan_status: "active",
  athlete_tier: "intermediate",
  days_per_week: 5,
  long_run_day: "Saturday",
  preferred_days: ["Tuesday", "Wednesday", "Thursday", "Saturday", "Sunday"],
  double_session_days: [],
  has_gym_access: true,
  use_treadmill: false,
  training_environment: "hilly",
};

const DALAT_WORKOUTS = [
  {
    id: 1001,
    plan_id: 101,
    week_number: 1,
    day_of_week: "Tuesday",
    phase: "Aerobic Base",
    title: "Aerobic Base Run (AeT Focus)",
    type: "easy_run",
    duration_minutes: 65,
    distance_km: 10.5,
    target_zone: "Zone 2",
    target_hr_range: "130–142 bpm",
    target_pace: "6:00 – 6:30 min/km",
    description: "Continuous aerobic running strictly below your Aerobic Threshold (142 bpm) on rolling fire trails to build mitochondrial density for Langbiang mountain climbs.",
    is_completed: 0,
  },
  {
    id: 1002,
    plan_id: 101,
    week_number: 1,
    day_of_week: "Wednesday",
    phase: "Aerobic Base",
    title: "Gym Muscular Endurance (ME)",
    type: "strength",
    duration_minutes: 50,
    distance_km: null,
    target_zone: "Strength",
    target_hr_range: "120–145 bpm",
    description: "Weighted box step-ups, split squats, and calf raises to prepare quads for the relentless 25-35% gradients of Langbiang Peak.",
    is_completed: 0,
  },
  {
    id: 1003,
    plan_id: 101,
    week_number: 1,
    day_of_week: "Thursday",
    phase: "Aerobic Base",
    title: "Trail Aerobic Run + Pine Root Strides",
    type: "easy_run",
    duration_minutes: 55,
    distance_km: 8.8,
    target_zone: "Zone 2",
    target_hr_range: "130–142 bpm",
    target_pace: "6:05 – 6:35 min/km",
    description: "Easy recovery miles followed by 6x20s uphill strides practicing rapid cadence and agility on pine needle descents.",
    is_completed: 0,
  },
  {
    id: 1004,
    plan_id: 101,
    week_number: 1,
    day_of_week: "Saturday",
    phase: "Aerobic Base",
    title: "Mountain Long Run (Langbiang Locus)",
    type: "long_run",
    duration_minutes: 160,
    distance_km: 25.0,
    target_zone: "Zone 2",
    target_hr_range: "132–142 bpm",
    target_pace: "6:15 – 6:45 min/km",
    description: "Sustained mountain endurance with 900m+ elevation gain. Practice race hydration and fuel intake every 25 minutes simulating dry highland conditions.",
    is_completed: 0,
  },
  {
    id: 1005,
    plan_id: 101,
    week_number: 1,
    day_of_week: "Sunday",
    phase: "Aerobic Base",
    title: "Aerobic Flush Recovery",
    type: "easy_run",
    duration_minutes: 40,
    distance_km: 6.0,
    target_zone: "Zone 1-2",
    target_hr_range: "< 130 bpm",
    target_pace: "6:30 – 7:00 min/km",
    description: "Gentle recovery jog on soft surface to flush legs following Saturday mountain volume.",
    is_completed: 0,
  },
  {
    id: 1006,
    plan_id: 101,
    week_number: 2,
    day_of_week: "Tuesday",
    phase: "Aerobic Base",
    title: "Aerobic Base + Steady Hill Climbs",
    type: "workout",
    duration_minutes: 75,
    distance_km: 12.0,
    target_zone: "Zone 2-3",
    target_hr_range: "135–155 bpm",
    target_pace: "5:50 – 6:20 min/km",
    description: "Aerobic base running incorporating 4x4min continuous uphill climbing intervals touching AnT threshold (165 bpm).",
    is_completed: 0,
  },
  {
    id: 1007,
    plan_id: 101,
    week_number: 2,
    day_of_week: "Wednesday",
    phase: "Aerobic Base",
    title: "Gym Muscular Endurance Circuit",
    type: "strength",
    duration_minutes: 55,
    distance_km: null,
    target_zone: "Strength",
    target_hr_range: "120–145 bpm",
    description: "Heavy step-ups with 10kg pack and eccentric quad loading for 100km downhill fatigue resistance.",
    is_completed: 0,
  },
  {
    id: 1008,
    plan_id: 101,
    week_number: 2,
    day_of_week: "Thursday",
    phase: "Aerobic Base",
    title: "Sustained Zone 2 Trail Run",
    type: "easy_run",
    duration_minutes: 60,
    distance_km: 9.5,
    target_zone: "Zone 2",
    target_hr_range: "130–142 bpm",
    target_pace: "6:05 – 6:35 min/km",
    description: "Steady aerobic maintenance strictly below AeT 142 bpm ceiling.",
    is_completed: 0,
  },
  {
    id: 1009,
    plan_id: 101,
    week_number: 2,
    day_of_week: "Saturday",
    phase: "Aerobic Base",
    title: "Progressive Mountain Long Run (100km Sim)",
    type: "long_run",
    duration_minutes: 190,
    distance_km: 30.0,
    target_zone: "Zone 2",
    target_hr_range: "134–144 bpm",
    target_pace: "6:15 – 6:45 min/km",
    description: "Back-to-back mountain volume: 1,200m+ D+ elevation gain. Practice race nutrition strategy (60-80g carbs/hr).",
    is_completed: 0,
  },
  {
    id: 1010,
    plan_id: 101,
    week_number: 2,
    day_of_week: "Sunday",
    phase: "Aerobic Base",
    title: "Aerobic Recovery Flush",
    type: "easy_run",
    duration_minutes: 45,
    distance_km: 6.8,
    target_zone: "Zone 1-2",
    target_hr_range: "< 130 bpm",
    target_pace: "6:30 – 7:00 min/km",
    description: "Light conversational recovery shuffle to promote blood flow.",
    is_completed: 0,
  },
];

test.use({
  deviceScaleFactor: 2,
  viewport: { width: 1140, height: 860 },
});

test("seed Dalat Ultra Trail 100km plan and capture screenshots", async ({ page }) => {
  page.on("console", (msg) => console.log("PAGE LOG:", msg.text()));
  page.on("pageerror", (err) => console.log("PAGE ERROR:", err.message));

  // Route mock backend responses
  await page.route("**/api/health**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ status: "healthy", gemini_api_configured: true }),
    });
  });

  await page.route("**/api/auth/me**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(DALAT_USER),
    });
  });

  await page.route("**/api/coach/active-plan**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        active: true,
        plan: DALAT_PLAN,
        workouts: DALAT_WORKOUTS,
      }),
    });
  });

  await page.route("**/api/coach/recent-plans**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        plans: [DALAT_PLAN],
      }),
    });
  });

  await page.route("**/api/coach/workouts**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        workouts: DALAT_WORKOUTS,
      }),
    });
  });

  await page.route("**/api/coach/block-completion/**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        blocks: [
          {
            block_number: 1,
            completion_pct: 85.0,
            unlocked: true,
            weeks: [1, 2],
          },
        ],
        max_generated_week: 2,
      }),
    });
  });

  await page.route("**/api/coach/block-evaluation/**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        block_number: 1,
        quality_grade: "A",
        avg_quality_score: 94,
        completion_pct: 85,
        coach_summary: "Outstanding aerobic foundation in Block 1 for Dalat Ultra Trail. All base runs remained strictly under your 142 bpm AeT ceiling, establishing the physiological base required for 100km and 2,079m D+.",
        coaching_takeaways: [
          "AeT discipline: 98% of aerobic mileage strictly under 142 bpm",
          "Completed 25km Langbiang mountain simulation with 900m D+",
          "ME Gym sessions built eccentric quad durability for steep downhill running"
        ],
        coach_notes: [
          "Nutrition test successful: 60g carbs/hr practiced during Saturday's mountain run"
        ]
      }),
    });
  });

  await page.route("**/api/coach/generate-next-block", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ success: true, message: "Block 2 generated" }),
    });
  });

  await page.route("**/api/analytics/**", async (route) => {
    await route.fulfill({ status: 200, contentType: "application/json", body: "{}" });
  });

  // Pre-seed localStorage with session and profile so user is logged in
  await page.addInitScript((user) => {
    localStorage.setItem("uphill_session_token", "mock-dut-token");
    localStorage.setItem("uphill_user", JSON.stringify(user));
  }, DALAT_USER);

  // 1. Open /app
  await page.goto("/app");
  await page.waitForLoadState("networkidle");

  // Click Scheduler / Planner tab
  const schedulerBtn = page.getByRole("button", { name: /Scheduler/i });
  if (await schedulerBtn.isVisible()) {
    await schedulerBtn.click();
  }

  // Wait for Dalat Ultra Trail header to be visible
  await expect(page.getByRole("heading", { name: /Dalat Ultra Trail/i })).toBeVisible({ timeout: 10000 });
  await page.waitForTimeout(600);

  // Hide Next.js dev overlay indicator
  await page.addStyleTag({
    content: `
      nextjs-portal,
      #nextjs__container_build_error_label,
      [data-nextjs-toast],
      div:has(> button[aria-label="Issues"]) {
        display: none !important;
      }
    `,
  });

  // A. Take a full-screen zoomed marketing capture (Dalat Ultra Trail active plan)
  await page.screenshot({
    path: "test-results/dut-100km-marketing-overview.png",
    fullPage: false,
  });
  console.log("Captured test-results/dut-100km-marketing-overview.png");

  // B. Scroll slightly so the navbar is out of view and the Dalat Ultra Trail card fills the frame
  await page.evaluate(() => {
    window.scrollTo({ top: 72, behavior: "instant" });
  });
  await page.waitForTimeout(400);

  await page.screenshot({
    path: "test-results/dut-100km-zoomed-in-plan.png",
    fullPage: false,
  });
  console.log("Captured test-results/dut-100km-zoomed-in-plan.png");

  // Copy to public/screenshots/current-planner-view.png for marketing landing page Step 1
  await page.screenshot({
    path: "public/screenshots/current-planner-view.png",
    fullPage: false,
  });
  console.log("Updated public/screenshots/current-planner-view.png with Dalat Ultra Trail plan");

  // C. Expand the Tuesday workout card to show the coach guidance and AeT ceiling
  const tuesdayCard = page.locator('div:has-text("Aerobic Base Run (AeT Focus)")').filter({ hasText: "Zone 2" }).first();
  if (await tuesdayCard.isVisible()) {
    const expandBtn = tuesdayCard.locator('button:has(svg)').last();
    if (await expandBtn.isVisible()) {
      await expandBtn.click();
      await page.waitForTimeout(500);

      await page.screenshot({
        path: "test-results/dut-100km-expanded-workout.png",
        fullPage: false,
      });
      console.log("Captured test-results/dut-100km-expanded-workout.png");
    }
  }

  // Scroll back to top for modal interactions
  await page.evaluate(() => {
    window.scrollTo({ top: 0, behavior: "instant" });
  });
  await page.waitForTimeout(300);

  // 2. Open Next Block Modal via the Block 1 Complete banner or Generate Block 2 button
  const genBlockBtn = page.getByRole("button", { name: /Generate Block 2/i });
  if (await genBlockBtn.isVisible()) {
    await genBlockBtn.click();
    await page.waitForTimeout(800);

    // Capture zoomed modal screenshot showing Coach Evaluation (Grade A, 94%, AeT adherence)
    await page.screenshot({
      path: "test-results/dut-next-block-modal-evaluation.png",
      fullPage: false,
    });
    console.log("Captured test-results/dut-next-block-modal-evaluation.png");

    // Scroll modal down to reveal Schedule Preferences and constraints
    await page.evaluate(() => {
      const dialog = document.querySelector('div[style*="max-height: 90vh"], div[style*="maxHeight: 90vh"]') ||
                     document.querySelector('div[style*="overflow-y: auto"]');
      if (dialog) {
        dialog.scrollTop = 450;
      }
    });
    await page.waitForTimeout(600);

    await page.screenshot({
      path: "test-results/dut-next-block-modal-constraints.png",
      fullPage: false,
    });
    console.log("Captured test-results/dut-next-block-modal-constraints.png");

    await page.screenshot({
      path: "public/screenshots/next-block-modal-constraints.png",
      fullPage: false,
    });
    console.log("Updated public/screenshots/next-block-modal-constraints.png");

    // Close the review modal
    const cancelBtn = page.getByRole("button", { name: /Cancel|Hủy/i });
    if (await cancelBtn.isVisible()) {
      await cancelBtn.click();
      await page.waitForTimeout(500);
    }
  }

  // 3. Capture the New Plan generation form with Dalat Ultra Trail 100km & threshold constraints
  const newPlanBtn = page.getByRole("button", { name: /New Plan/i });
  if (await newPlanBtn.isVisible()) {
    await newPlanBtn.click();
    await page.waitForTimeout(600);

    // Fill in Dalat Ultra Trail details
    const raceInput = page.getByPlaceholder(/e\.g\. UTMB/i);
    if (await raceInput.isVisible()) {
      await raceInput.fill("Dalat Ultra Trail");
    }

    const distInput = page.locator('input[placeholder="e.g. 50"]');
    if (await distInput.isVisible()) {
      await distInput.fill("100");
    }

    const elevInput = page.locator('input[placeholder="e.g. 1500"]');
    if (await elevInput.isVisible()) {
      await elevInput.fill("2079");
    }

    const kmInput = page.locator('input[placeholder="e.g. 30"], input[placeholder="vd. 30"]');
    if (await kmInput.isVisible()) {
      await kmInput.fill("55");
    }

    const dateInputs = page.locator('input[type="date"]');
    if ((await dateInputs.count()) > 0) {
      await dateInputs.first().fill("2027-03-27");
    }

    await page.waitForTimeout(500);

    // Scroll form to center inputs
    await page.evaluate(() => {
      window.scrollTo({ top: 60, behavior: "instant" });
    });
    await page.waitForTimeout(400);

    // A. Zoomed-in form screenshot
    await page.screenshot({
      path: "test-results/dut-plan-generation-form-zoomed.png",
      fullPage: false,
    });
    console.log("Captured test-results/dut-plan-generation-form-zoomed.png");
  }
});
