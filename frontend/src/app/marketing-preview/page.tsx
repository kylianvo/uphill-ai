"use client";
import React from "react";
import {
  MapPin,
  CalendarBlank,
  ArrowsClockwise,
  Trophy,
  ShieldCheck,
  CheckCircle,
  Gauge,
  Crosshair,
  Sneaker,
  BowlFood,
  Clock,
  Mountains,
  Fire,
  ChartLineUp,
  Sliders,
  Target,
  Lightning,
  Sparkle,
  ArrowRight,
} from "@phosphor-icons/react";

export default function MarketingPreview() {
  return (
    <div
      style={{
        background: "#0f172a",
        minHeight: "100vh",
        padding: "40px 20px",
        display: "flex",
        flexDirection: "column",
        gap: "60px",
        alignItems: "center",
        fontFamily: "system-ui, -apple-system, sans-serif",
      }}
    >
      <h1 style={{ color: "#ffffff", fontSize: "24px", margin: 0 }}>
        Marketing Cards Capture Harness
      </h1>

      {/* ── 1. STEP 1: CURRENT PLANNER VIEW ───────────────────────── */}
      <div
        id="step1-planner-card"
        style={{
          width: "680px",
          background: "#ffffff",
          borderRadius: "20px",
          padding: "24px 28px",
          boxShadow: "0 20px 40px rgba(0,0,0,0.12)",
          border: "1px solid rgba(0,0,0,0.08)",
          boxSizing: "border-box",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "16px" }}>
          <div>
            <div style={{ display: "inline-flex", alignItems: "center", gap: "6px", background: "rgba(25, 206, 139, 0.12)", color: "#059669", padding: "4px 10px", borderRadius: "9999px", fontSize: "11.5px", fontWeight: 700, marginBottom: "8px" }}>
              <MapPin size={14} weight="fill" />
              <span>ACTIVE TRAINING PLAN · 16 WEEKS</span>
            </div>
            <h2 style={{ fontSize: "24px", fontWeight: 800, color: "#111827", margin: "0 0 4px", letterSpacing: "-0.5px" }}>
              Dalat Ultra Trail (DUT)
              <span style={{ fontSize: "16px", fontWeight: 700, color: "#059669", marginLeft: "8px" }}>
                100km · +5,156m D+
              </span>
            </h2>
            <p style={{ fontSize: "13px", color: "#6b7280", margin: 0, fontWeight: 500 }}>
              Race Day: 27 Mar 2027 · Elevation Gain: 5,156m · Target Finish: 14h 30m · Athlete Tier: Intermediate
            </p>
          </div>
          <div style={{ display: "flex", gap: "4px", background: "#f3f4f6", padding: "3px", borderRadius: "8px" }}>
            <span style={{ background: "#ffffff", color: "#111827", padding: "4px 12px", borderRadius: "6px", fontSize: "12px", fontWeight: 700, boxShadow: "0 1px 3px rgba(0,0,0,0.08)" }}>List</span>
            <span style={{ color: "#6b7280", padding: "4px 12px", fontSize: "12px", fontWeight: 600 }}>Calendar</span>
          </div>
        </div>

        {/* Threshold & Volume Calibration Bar */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "10px", background: "#f8fafc", padding: "12px 14px", borderRadius: "12px", border: "1px solid #e2e8f0", marginBottom: "18px" }}>
          <div>
            <div style={{ fontSize: "10.5px", fontWeight: 700, color: "#64748b", textTransform: "uppercase" }}>AeT Ceiling (HR)</div>
            <div style={{ fontSize: "17px", fontWeight: 800, color: "#059669" }}>142 <span style={{ fontSize: "11px", fontWeight: 600 }}>bpm</span></div>
          </div>
          <div>
            <div style={{ fontSize: "10.5px", fontWeight: 700, color: "#64748b", textTransform: "uppercase" }}>AnT Threshold (HR)</div>
            <div style={{ fontSize: "17px", fontWeight: 800, color: "#d97706" }}>165 <span style={{ fontSize: "11px", fontWeight: 600 }}>bpm</span></div>
          </div>
          <div>
            <div style={{ fontSize: "10.5px", fontWeight: 700, color: "#64748b", textTransform: "uppercase" }}>Accumulated Vol.</div>
            <div style={{ fontSize: "17px", fontWeight: 800, color: "#7c3aed" }}>8.5 hrs <span style={{ fontSize: "11px", fontWeight: 600 }}>/ 136h target</span></div>
          </div>
          <div>
            <div style={{ fontSize: "10.5px", fontWeight: 700, color: "#64748b", textTransform: "uppercase" }}>Course Vert</div>
            <div style={{ fontSize: "17px", fontWeight: 800, color: "#0284c7" }}>+5,156m <span style={{ fontSize: "11px", fontWeight: 600 }}>D+</span></div>
          </div>
        </div>

        {/* Week 1 Workout Sessions */}
        <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", borderBottom: "1px solid #e5e7eb", paddingBottom: "6px" }}>
            <span style={{ fontSize: "13px", fontWeight: 700, color: "#111827" }}>
              Week 1: Aerobic Base · 8h 15m accumulated (56.3 km · +1,420m D+)
            </span>
            <span style={{ fontSize: "12px", fontWeight: 600, color: "#059669" }}>
              82% Zone 2 (6h 45m) · 80/20 Audited
            </span>
          </div>

          {/* Session 1 */}
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "10px 14px", background: "#ffffff", borderRadius: "10px", border: "1px solid #e5e7eb" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
              <span style={{ background: "#ecfdf5", color: "#059669", fontWeight: 800, fontSize: "11.5px", padding: "4px 8px", borderRadius: "6px" }}>TUE</span>
              <div>
                <div style={{ fontSize: "14px", fontWeight: 700, color: "#111827" }}>Aerobic Base Run (AeT Focus)</div>
                <div style={{ fontSize: "12px", color: "#6b7280" }}>1h 05m (10.5 km) · Target HR 130–142 bpm · Strictly below AeT ceiling</div>
              </div>
            </div>
            <span style={{ fontSize: "12px", fontWeight: 700, color: "#059669", background: "rgba(25,206,139,0.12)", padding: "3px 8px", borderRadius: "6px" }}>Zone 2</span>
          </div>

          {/* Session 2 */}
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "10px 14px", background: "#ffffff", borderRadius: "10px", border: "1px solid #e5e7eb" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
              <span style={{ background: "#f5f3ff", color: "#7c3aed", fontWeight: 800, fontSize: "11.5px", padding: "4px 8px", borderRadius: "6px" }}>WED</span>
              <div>
                <div style={{ fontSize: "14px", fontWeight: 700, color: "#111827" }}>Gym Muscular Endurance (ME)</div>
                <div style={{ fontSize: "12px", color: "#6b7280" }}>0h 50m · Weighted step-ups & split squats for steep Langbiang descents</div>
              </div>
            </div>
            <span style={{ fontSize: "12px", fontWeight: 700, color: "#7c3aed", background: "rgba(124,58,237,0.1)", padding: "3px 8px", borderRadius: "6px" }}>Strength</span>
          </div>

          {/* Session 3 */}
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "10px 14px", background: "#ffffff", borderRadius: "10px", border: "1px solid #e5e7eb" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
              <span style={{ background: "#ecfdf5", color: "#059669", fontWeight: 800, fontSize: "11.5px", padding: "4px 8px", borderRadius: "6px" }}>SAT</span>
              <div>
                <div style={{ fontSize: "14px", fontWeight: 700, color: "#111827" }}>Mountain Long Run (Langbiang Locus)</div>
                <div style={{ fontSize: "12px", color: "#6b7280" }}>2h 40m (25.0 km, +900m D+) · Practice 60g carbs/hr race nutrition</div>
              </div>
            </div>
            <span style={{ fontSize: "12px", fontWeight: 700, color: "#059669", background: "rgba(25,206,139,0.12)", padding: "3px 8px", borderRadius: "6px" }}>Long Run</span>
          </div>
        </div>
      </div>

      {/* ── 1B. STEP 1 (TELL US WHERE YOU ARE): ONBOARDING & GOAL DETERMINER ── */}
      <div
        id="step1-onboarding-card"
        style={{
          width: "680px",
          background: "#ffffff",
          borderRadius: "20px",
          padding: "24px 28px",
          boxShadow: "0 20px 40px rgba(0,0,0,0.12)",
          border: "1px solid rgba(0,0,0,0.08)",
          boxSizing: "border-box",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "16px" }}>
          <div>
            <div style={{ display: "inline-flex", alignItems: "center", gap: "6px", background: "rgba(25, 206, 139, 0.12)", color: "#059669", padding: "4px 10px", borderRadius: "9999px", fontSize: "11.5px", fontWeight: 700, marginBottom: "8px" }}>
              <Crosshair size={14} weight="bold" />
              <span>ATHLETE CALIBRATION & GOAL RACE</span>
            </div>
            <h3 style={{ fontSize: "20px", fontWeight: 800, color: "#111827", margin: "0 0 4px" }}>
              Tell us where you are
            </h3>
            <p style={{ fontSize: "12.5px", color: "#6b7280", margin: 0 }}>
              Course vert, baseline weekly hours, and AeT threshold calibrate your starting point.
            </p>
          </div>
          <span style={{ background: "#ecfdf5", color: "#059669", padding: "4px 10px", borderRadius: "8px", fontSize: "11px", fontWeight: 700, border: "1px solid #a7f3d0" }}>
            Step 01 / 04
          </span>
        </div>

        {/* 2-Column Parameter Grid */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px", marginBottom: "14px" }}>
          <div style={{ background: "#f8fafc", padding: "12px 14px", borderRadius: "12px", border: "1px solid #e2e8f0" }}>
            <span style={{ fontSize: "10.5px", fontWeight: 700, color: "#64748b", textTransform: "uppercase" }}>Target Race & Course Vert</span>
            <div style={{ fontSize: "15px", fontWeight: 800, color: "#111827", marginTop: "2px" }}>Dalat Ultra Trail (DUT)</div>
            <div style={{ fontSize: "12px", fontWeight: 600, color: "#059669" }}>100km · +5,156m elevation gain</div>
          </div>
          <div style={{ background: "#f8fafc", padding: "12px 14px", borderRadius: "12px", border: "1px solid #e2e8f0" }}>
            <span style={{ fontSize: "10.5px", fontWeight: 700, color: "#64748b", textTransform: "uppercase" }}>Current Baseline Fitness</span>
            <div style={{ fontSize: "15px", fontWeight: 800, color: "#111827", marginTop: "2px" }}>6.5 hrs / week base</div>
            <div style={{ fontSize: "12px", color: "#64748b" }}>5 days available · 0 active injuries</div>
          </div>
        </div>

        {/* Physiological Calibration */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "10px", background: "#f0fdf4", padding: "10px 14px", borderRadius: "12px", border: "1px solid #bbf7d0", marginBottom: "16px" }}>
          <div>
            <div style={{ fontSize: "10.5px", fontWeight: 700, color: "#166534" }}>AeT Aerobic Threshold</div>
            <div style={{ fontSize: "16px", fontWeight: 800, color: "#15803d" }}>142 bpm <span style={{ fontSize: "10.5px", fontWeight: 600 }}>(MAF Test)</span></div>
          </div>
          <div>
            <div style={{ fontSize: "10.5px", fontWeight: 700, color: "#166534" }}>AnT Anaerobic Ceiling</div>
            <div style={{ fontSize: "16px", fontWeight: 800, color: "#d97706" }}>165 bpm</div>
          </div>
          <div>
            <div style={{ fontSize: "10.5px", fontWeight: 700, color: "#166534" }}>Aerobic Deficit</div>
            <div style={{ fontSize: "16px", fontWeight: 800, color: "#0284c7" }}>16.2% <span style={{ fontSize: "10.5px", fontWeight: 600 }}>(Base Ready)</span></div>
          </div>
        </div>

        {/* Goal Determiner Target Calibration Row */}
        <div style={{ marginBottom: "8px" }}>
          <div style={{ fontSize: "11px", fontWeight: 700, color: "#64748b", textTransform: "uppercase", marginBottom: "6px" }}>
            Goal Determiner Finish Calibration (+5,156m Course Model)
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "8px" }}>
            <div style={{ border: "1px solid #e2e8f0", background: "#ffffff", padding: "8px 10px", borderRadius: "10px", textAlign: "center" }}>
              <div style={{ fontSize: "10px", fontWeight: 700, color: "#0284c7" }}>A · AMBITIOUS</div>
              <div style={{ fontSize: "15px", fontWeight: 800, color: "#111827" }}>13h 45m</div>
              <div style={{ fontSize: "10px", color: "#64748b" }}>Top 8% finisher</div>
            </div>
            <div style={{ border: "2px solid #059669", background: "rgba(25,206,139,0.08)", padding: "8px 10px", borderRadius: "10px", textAlign: "center" }}>
              <div style={{ fontSize: "10px", fontWeight: 800, color: "#059669" }}>B · REALISTIC (TARGET)</div>
              <div style={{ fontSize: "15px", fontWeight: 800, color: "#111827" }}>14h 30m</div>
              <div style={{ fontSize: "10px", fontWeight: 600, color: "#059669" }}>Peak: 8.5 hrs/wk</div>
            </div>
            <div style={{ border: "1px solid #e2e8f0", background: "#ffffff", padding: "8px 10px", borderRadius: "10px", textAlign: "center" }}>
              <div style={{ fontSize: "10px", fontWeight: 700, color: "#d97706" }}>C · SAFE FINISH</div>
              <div style={{ fontSize: "15px", fontWeight: 800, color: "#111827" }}>15h 40m</div>
              <div style={{ fontSize: "10px", color: "#64748b" }}>Course cutoff safety</div>
            </div>
          </div>
        </div>
      </div>

      {/* ── 2. STEP 2: NEXT BLOCK MODAL CONSTRAINTS ───────────────── */}
      <div
        id="step2-constraints-card"
        style={{
          width: "640px",
          background: "#ffffff",
          borderRadius: "20px",
          padding: "24px 28px",
          boxShadow: "0 20px 40px rgba(0,0,0,0.12)",
          border: "1px solid rgba(0,0,0,0.08)",
          boxSizing: "border-box",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "16px" }}>
          <div style={{ width: "36px", height: "36px", borderRadius: "10px", background: "rgba(25, 206, 139, 0.12)", color: "#059669", display: "flex", alignItems: "center", justifyContent: "center" }}>
            <Sliders size={20} weight="bold" />
          </div>
          <div>
            <h3 style={{ fontSize: "18px", fontWeight: 800, color: "#111827", margin: 0 }}>Schedule Preferences & Constraints</h3>
            <p style={{ fontSize: "12.5px", color: "#6b7280", margin: 0 }}>Calibrating Block 2 around your life & terrain access</p>
          </div>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "14px", marginBottom: "16px" }}>
          <div style={{ background: "#f8fafc", padding: "14px", borderRadius: "12px", border: "1px solid #e2e8f0" }}>
            <label style={{ display: "block", fontSize: "11px", fontWeight: 700, color: "#64748b", textTransform: "uppercase", marginBottom: "6px" }}>Weekly Running Days</label>
            <div style={{ fontSize: "16px", fontWeight: 700, color: "#111827" }}>5 days per week</div>
            <div style={{ fontSize: "11.5px", color: "#64748b", marginTop: "2px" }}>Tue, Wed, Thu, Sat, Sun</div>
          </div>
          <div style={{ background: "#f8fafc", padding: "14px", borderRadius: "12px", border: "1px solid #e2e8f0" }}>
            <label style={{ display: "block", fontSize: "11px", fontWeight: 700, color: "#64748b", textTransform: "uppercase", marginBottom: "6px" }}>Long Run Anchor Day</label>
            <div style={{ fontSize: "16px", fontWeight: 700, color: "#111827" }}>Saturday</div>
            <div style={{ fontSize: "11.5px", color: "#64748b", marginTop: "2px" }}>Dedicated mountain volume day</div>
          </div>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "14px", marginBottom: "18px" }}>
          <div style={{ background: "#f8fafc", padding: "14px", borderRadius: "12px", border: "1px solid #e2e8f0", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <div>
              <div style={{ fontSize: "13.5px", fontWeight: 700, color: "#111827" }}>Gym Access (ME)</div>
              <div style={{ fontSize: "11.5px", color: "#64748b" }}>Weighted step-ups enabled</div>
            </div>
            <span style={{ background: "#ecfdf5", color: "#059669", fontWeight: 700, fontSize: "12px", padding: "3px 8px", borderRadius: "6px" }}>Yes</span>
          </div>
          <div style={{ background: "#f8fafc", padding: "14px", borderRadius: "12px", border: "1px solid #e2e8f0", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <div>
              <div style={{ fontSize: "13.5px", fontWeight: 700, color: "#111827" }}>Treadmill Incline Mode</div>
              <div style={{ fontSize: "11.5px", color: "#64748b" }}>Grade-adjusted speed pairs</div>
            </div>
            <span style={{ background: "#ecfdf5", color: "#059669", fontWeight: 700, fontSize: "12px", padding: "3px 8px", borderRadius: "6px" }}>Active</span>
          </div>
        </div>

        <div style={{ background: "rgba(25, 206, 139, 0.08)", padding: "12px 16px", borderRadius: "12px", border: "1px solid rgba(25, 206, 139, 0.25)", display: "flex", alignItems: "center", gap: "10px" }}>
          <ShieldCheck size={20} weight="fill" color="#059669" />
          <span style={{ fontSize: "12.5px", color: "#065f46", fontWeight: 600 }}>
            Every session in Block 2 is hard-capped by your 142 bpm AeT ceiling and 80/20 balance.
          </span>
        </div>
      </div>

      {/* ── 3. STEP 3: ADAPT WEEK FEELING SELECTOR (RPE MODEL) ─────── */}
      <div
        id="step3-feeling-card"
        style={{
          width: "680px",
          background: "#ffffff",
          borderRadius: "20px",
          padding: "24px 28px",
          boxShadow: "0 20px 40px rgba(0,0,0,0.12)",
          border: "1px solid rgba(0,0,0,0.08)",
          boxSizing: "border-box",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "16px" }}>
          <div>
            <div style={{ display: "inline-flex", alignItems: "center", gap: "6px", background: "rgba(25, 206, 139, 0.12)", color: "#059669", padding: "4px 10px", borderRadius: "9999px", fontSize: "11.5px", fontWeight: 700, marginBottom: "8px" }}>
              <ArrowsClockwise size={14} weight="bold" />
              <span>RPE FATIGUE MODEL · DYNAMIC ADAPTATION</span>
            </div>
            <h3 style={{ fontSize: "20px", fontWeight: 800, color: "#111827", margin: "0 0 4px" }}>
              Train, log, and adapt
            </h3>
            <p style={{ fontSize: "12.5px", color: "#6b7280", margin: 0 }}>
              Athlete logs session RPE (1–10 CR10 scale). Coach AI recalibrates remaining block.
            </p>
          </div>
          <span style={{ background: "#ecfdf5", color: "#059669", padding: "4px 10px", borderRadius: "8px", fontSize: "11px", fontWeight: 700, border: "1px solid #a7f3d0" }}>
            Step 03 / 04
          </span>
        </div>

        {/* 5 RPE Selector Cards (Uphill AI RPE Model) */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: "8px", marginBottom: "16px" }}>
          {[
            { id: "very_light", rpe: 2, label: "Very Light", sub: "Active recovery", color: "#06b6d4", bg: "#ecfeff" },
            { id: "light", rpe: 4, label: "Light", sub: "Zone 1/2 base", color: "#10b981", bg: "#ecfdf5" },
            { id: "moderate", rpe: 6, label: "Moderate", sub: "Steady effort", color: "#3b82f6", bg: "#eff6ff" },
            { id: "hard", rpe: 8, label: "Hard", sub: "Heavy legs", color: "#d97706", bg: "#fef3c7", active: true },
            { id: "max_effort", rpe: 10, label: "Max Effort", sub: "Exhaustion", color: "#ef4444", bg: "#fef2f2" },
          ].map((item) => (
            <div
              key={item.id}
              style={{
                border: item.active ? `2px solid ${item.color}` : "1px solid #e2e8f0",
                background: item.active ? item.bg : "#f8fafc",
                borderRadius: "12px",
                padding: "10px 6px",
                textAlign: "center",
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                gap: "2px",
                boxShadow: item.active ? "0 4px 12px rgba(217, 119, 6, 0.15)" : "none",
              }}
            >
              <div style={{ fontSize: "11px", fontWeight: 800, color: item.color }}>RPE {item.rpe}</div>
              <div style={{ fontSize: "12.5px", fontWeight: 700, color: item.active ? "#92400e" : "#111827" }}>{item.label}</div>
              <div style={{ fontSize: "10px", color: "#64748b" }}>{item.sub}</div>
              {item.active && (
                <div style={{ marginTop: "4px", background: item.color, color: "#ffffff", fontSize: "9px", fontWeight: 800, padding: "1px 6px", borderRadius: "9999px" }}>
                  LOGGED
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Logged Workout Context Box */}
        <div style={{ background: "#f8fafc", padding: "10px 14px", borderRadius: "10px", border: "1px solid #e2e8f0", marginBottom: "14px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div>
            <div style={{ fontSize: "11px", fontWeight: 700, color: "#64748b", textTransform: "uppercase" }}>Latest Logged Workout</div>
            <div style={{ fontSize: "13.5px", fontWeight: 700, color: "#111827" }}>Saturday Mountain Long Run (25km · +900m D+)</div>
            <div style={{ fontSize: "11.5px", color: "#4b5563", marginTop: "1px" }}>
              Athlete Note: &ldquo;Quads felt heavy on second climb, cardiac drift measured 7.4%&rdquo;
            </div>
          </div>
          <span style={{ background: "#fef3c7", color: "#d97706", padding: "4px 10px", borderRadius: "8px", fontSize: "12px", fontWeight: 800, border: "1px solid #fde68a" }}>
            RPE 8 Logged
          </span>
        </div>

        {/* Coach Adaptation Response Box */}
        <div style={{ background: "rgba(25, 206, 139, 0.08)", padding: "12px 14px", borderRadius: "12px", border: "1px solid rgba(25, 206, 139, 0.25)" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "6px", marginBottom: "4px" }}>
            <Sparkle size={16} weight="fill" color="#059669" />
            <span style={{ fontSize: "12.5px", fontWeight: 700, color: "#065f46" }}>Coach AI Dynamic Adaptation Engine</span>
          </div>
          <p style={{ fontSize: "12px", color: "#1e3a2f", lineHeight: 1.5, margin: 0 }}>
            Neuromuscular fatigue detected (RPE 8 vs planned 6). Converting Tuesday Gym ME session to <strong>45-min Zone 1 Active Recovery (&lt;130 bpm)</strong> to flush metabolites and protect aerobic base.
          </p>
        </div>
      </div>

      {/* ── 4. STEP 4: BLOCK REVIEW COACH FEEDBACK ───────────────── */}
      <div
        id="step4-review-card"
        style={{
          width: "640px",
          background: "#ffffff",
          borderRadius: "20px",
          padding: "24px 28px",
          boxShadow: "0 20px 40px rgba(0,0,0,0.12)",
          border: "1px solid rgba(0,0,0,0.08)",
          boxSizing: "border-box",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "16px" }}>
          <div>
            <div style={{ display: "inline-flex", alignItems: "center", gap: "6px", background: "rgba(25, 206, 139, 0.12)", color: "#059669", padding: "4px 10px", borderRadius: "9999px", fontSize: "11.5px", fontWeight: 700, marginBottom: "8px" }}>
              <Trophy size={14} weight="fill" />
              <span>BLOCK 1 EVALUATION · COMPLETE</span>
            </div>
            <h3 style={{ fontSize: "20px", fontWeight: 800, color: "#111827", margin: "0 0 4px" }}>
              Block 1: Aerobic Base Foundation
            </h3>
            <p style={{ fontSize: "12.5px", color: "#6b7280", margin: 0 }}>
              4 Weeks · 186.5 km Total Volume · 3,420m D+
            </p>
          </div>
          {/* Grade Badge */}
          <div style={{ textAlign: "center", background: "#ecfdf5", border: "1.5px solid #059669", padding: "8px 16px", borderRadius: "14px" }}>
            <div style={{ fontSize: "26px", fontWeight: 900, color: "#059669", lineHeight: 1 }}>GRADE A</div>
            <div style={{ fontSize: "11px", fontWeight: 700, color: "#065f46", marginTop: "4px" }}>94% Score</div>
          </div>
        </div>

        {/* Coach Summary */}
        <div style={{ background: "#f8fafc", padding: "14px", borderRadius: "12px", border: "1px solid #e2e8f0", marginBottom: "16px" }}>
          <p style={{ fontSize: "13px", color: "#334155", lineHeight: 1.55, margin: 0 }}>
            &ldquo;Outstanding aerobic foundation in Block 1 for Dalat Ultra Trail. All base runs remained strictly under your 142 bpm AeT ceiling, establishing the mitochondrial density required for 100km and 2,079m D+.&rdquo;
          </p>
        </div>

        {/* Key Takeaways */}
        <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "12.5px", color: "#374151" }}>
            <CheckCircle size={16} weight="fill" color="#059669" />
            <span><strong>AeT discipline:</strong> 98% of aerobic mileage strictly under 142 bpm.</span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "12.5px", color: "#374151" }}>
            <CheckCircle size={16} weight="fill" color="#059669" />
            <span><strong>Long Run:</strong> Completed 25km Langbiang simulation with 900m D+.</span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "12.5px", color: "#374151" }}>
            <CheckCircle size={16} weight="fill" color="#059669" />
            <span><strong>Muscular Endurance:</strong> Gym sessions built eccentric quad durability for steep descents.</span>
          </div>
        </div>
      </div>

      {/* ── 5. COACH UPHILL CHAT EXCHANGE (DEDICATED FEATURE MOMENT) ── */}
      <div
        id="coach-chat-exchange-card"
        style={{
          width: "680px",
          background: "#ffffff",
          borderRadius: "20px",
          padding: "24px 28px",
          boxShadow: "0 20px 40px rgba(0,0,0,0.12)",
          border: "1px solid rgba(0,0,0,0.08)",
          boxSizing: "border-box",
        }}
      >
        {/* Chat Header */}
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", paddingBottom: "14px", borderBottom: "1px solid #f1f5f9", marginBottom: "18px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <div style={{ position: "relative" }}>
              <div style={{ width: "38px", height: "38px", borderRadius: "50%", background: "#111827", color: "#ffffff", display: "flex", alignItems: "center", justifyContent: "center", fontWeight: 800, fontSize: "15px" }}>
                CU
              </div>
              <span style={{ position: "absolute", bottom: 0, right: 0, width: "10px", height: "10px", borderRadius: "50%", background: "#19ce8b", border: "2px solid #ffffff" }} />
            </div>
            <div>
              <div style={{ fontSize: "15px", fontWeight: 700, color: "#111827" }}>Coach Uphill (AI)</div>
              <div style={{ fontSize: "12px", color: "#059669", fontWeight: 600 }}>Grounded on Exercise Physiology & Training Science</div>
            </div>
          </div>
          <span style={{ fontSize: "11px", fontWeight: 700, background: "rgba(25, 206, 139, 0.12)", color: "#059669", padding: "4px 10px", borderRadius: "9999px" }}>
            RAG GROUNDED
          </span>
        </div>

        {/* Conversation */}
        <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
          {/* User Bubble */}
          <div style={{ alignSelf: "flex-end", maxWidth: "84%", background: "#111827", color: "#ffffff", padding: "12px 18px", borderRadius: "18px 18px 4px 18px", fontSize: "13.5px", lineHeight: 1.5 }}>
            My quads are completely smoked from Saturday&apos;s +1,400m downhill vert. I have a Gym Muscular Endurance (ME) session scheduled tomorrow with weighted step-ups. Should I push through or adjust the plan?
          </div>

          {/* Coach Bubble (Literature Citation + Plan Change) */}
          <div style={{ alignSelf: "flex-start", maxWidth: "92%", background: "#f8fafc", color: "#1e293b", padding: "16px 20px", borderRadius: "18px 18px 18px 4px", fontSize: "13.5px", lineHeight: 1.6, border: "1px solid #e2e8f0" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "6px", color: "#059669", fontSize: "11.5px", fontWeight: 700, marginBottom: "6px" }}>
              <ShieldCheck size={16} weight="fill" />
              <span>CITATION: Training for the Uphill Athlete (House, Johnston, Jornet, Ch. 8)</span>
            </div>
            Do not perform Gym Muscular Endurance (ME) with active eccentric muscle damage. ME utilizes heavy resistance to recruit high-threshold motor units under high tension in an aerobic state. Performing weighted step-ups with micro-tears impairs neural recruitment and spikes patellar tendon strain.

            {/* Dynamic Plan Modification Box */}
            <div style={{ marginTop: "12px", padding: "12px 14px", background: "#f0fdf4", border: "1px solid #bbf7d0", borderRadius: "10px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "6px", color: "#15803d", fontSize: "11.5px", fontWeight: 800, textTransform: "uppercase", marginBottom: "6px" }}>
                <ArrowsClockwise size={15} weight="bold" />
                <span>SCHEDULE AUTOMATICALLY ADJUSTED</span>
              </div>
              <ul style={{ margin: "0 0 8px", paddingLeft: "18px", fontSize: "12.5px", color: "#166534", lineHeight: 1.5 }}>
                <li><strong>Tomorrow (Tuesday):</strong> Converted to 40-min Zone 1 Active Recovery (&lt;130 bpm) to flush metabolites.</li>
                <li><strong>Gym ME Session:</strong> Moved to Thursday to allow a 48h neuromuscular recovery window.</li>
                <li>If soreness remains above RPE 3 on Thursday, we will convert ME to mobility and resume next week.</li>
              </ul>
              <div style={{ display: "inline-flex", alignItems: "center", gap: "6px", background: "#15803d", color: "#ffffff", padding: "4px 10px", borderRadius: "6px", fontSize: "11.5px", fontWeight: 700 }}>
                <CheckCircle size={14} weight="fill" />
                <span>Tuesday workout updated to Active Recovery (Zone 1)</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ── 6. TOOL 1: PACE STRATEGY SPLITS TABLE ────────────────── */}
      <div
        id="tool-pace-card"
        style={{
          width: "680px",
          background: "#ffffff",
          borderRadius: "20px",
          padding: "24px 28px",
          boxShadow: "0 20px 40px rgba(0,0,0,0.12)",
          border: "1px solid rgba(0,0,0,0.08)",
          boxSizing: "border-box",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "16px" }}>
          <div>
            <div style={{ display: "inline-flex", alignItems: "center", gap: "6px", background: "rgba(25, 206, 139, 0.12)", color: "#059669", padding: "4px 10px", borderRadius: "9999px", fontSize: "11.5px", fontWeight: 700, marginBottom: "8px" }}>
              <Gauge size={14} weight="bold" />
              <span>MINETTI PHYSICS ENGINE</span>
            </div>
            <h3 style={{ fontSize: "20px", fontWeight: 800, color: "#111827", margin: "0 0 4px" }}>
              Pace Strategy · Dalat Ultra Trail 100km
            </h3>
            <p style={{ fontSize: "12.5px", color: "#6b7280", margin: 0 }}>
              Segment-by-segment pacing solving for 14h 30m target finish
            </p>
          </div>
          <div style={{ textAlign: "right" }}>
            <div style={{ fontSize: "18px", fontWeight: 800, color: "#111827" }}>14h 12m <span style={{ fontSize: "12px", color: "#6b7280", fontWeight: 500 }}>moving</span></div>
            <div style={{ fontSize: "12px", color: "#059669", fontWeight: 700 }}>+18m aid station rest</div>
          </div>
        </div>

        {/* Splits Table */}
        <table style={{ width: "100%", fontSize: "12px", borderCollapse: "collapse", textAlign: "left" }}>
          <thead>
            <tr style={{ borderBottom: "2px solid #e5e7eb", color: "#64748b", fontWeight: 700 }}>
              <th style={{ padding: "8px 6px" }}>Checkpoint</th>
              <th style={{ padding: "8px 6px" }}>Dist</th>
              <th style={{ padding: "8px 6px" }}>Grade</th>
              <th style={{ padding: "8px 6px" }}>Minetti Pace</th>
              <th style={{ padding: "8px 6px" }}>Elapsed Time</th>
              <th style={{ padding: "8px 6px" }}>Effort</th>
            </tr>
          </thead>
          <tbody>
            <tr style={{ borderBottom: "1px solid #f1f5f9" }}>
              <td style={{ padding: "8px 6px", fontWeight: 700, color: "#111827" }}>CP1 Robin Hill</td>
              <td style={{ padding: "8px 6px", color: "#4b5563" }}>12.5 km</td>
              <td style={{ padding: "8px 6px", color: "#059669", fontWeight: 600 }}>+4.2%</td>
              <td style={{ padding: "8px 6px", fontWeight: 700, color: "#111827" }}>6:45 /km</td>
              <td style={{ padding: "8px 6px", color: "#4b5563" }}>1h 24m</td>
              <td style={{ padding: "8px 6px" }}><span style={{ background: "#ecfdf5", color: "#059669", padding: "2px 6px", borderRadius: "4px", fontWeight: 700 }}>Zone 2</span></td>
            </tr>
            <tr style={{ borderBottom: "1px solid #f1f5f9" }}>
              <td style={{ padding: "8px 6px", fontWeight: 700, color: "#111827" }}>CP2 Tuyen Lam</td>
              <td style={{ padding: "8px 6px", color: "#4b5563" }}>28.0 km</td>
              <td style={{ padding: "8px 6px", color: "#059669", fontWeight: 600 }}>+3.8%</td>
              <td style={{ padding: "8px 6px", fontWeight: 700, color: "#111827" }}>7:15 /km</td>
              <td style={{ padding: "8px 6px", color: "#4b5563" }}>3h 18m</td>
              <td style={{ padding: "8px 6px" }}><span style={{ background: "#ecfdf5", color: "#059669", padding: "2px 6px", borderRadius: "4px", fontWeight: 700 }}>Zone 2</span></td>
            </tr>
            <tr style={{ borderBottom: "1px solid #f1f5f9" }}>
              <td style={{ padding: "8px 6px", fontWeight: 700, color: "#111827" }}>CP3 Langbiang Base</td>
              <td style={{ padding: "8px 6px", color: "#4b5563" }}>52.0 km</td>
              <td style={{ padding: "8px 6px", color: "#d97706", fontWeight: 600 }}>+8.5%</td>
              <td style={{ padding: "8px 6px", fontWeight: 700, color: "#111827" }}>8:30 /km</td>
              <td style={{ padding: "8px 6px", color: "#4b5563" }}>6h 42m</td>
              <td style={{ padding: "8px 6px" }}><span style={{ background: "#fef3c7", color: "#d97706", padding: "2px 6px", borderRadius: "4px", fontWeight: 700 }}>Aid 15m</span></td>
            </tr>
            <tr style={{ borderBottom: "1px solid #f1f5f9" }}>
              <td style={{ padding: "8px 6px", fontWeight: 700, color: "#111827" }}>CP4 Langbiang Summit</td>
              <td style={{ padding: "8px 6px", color: "#4b5563" }}>68.5 km</td>
              <td style={{ padding: "8px 6px", color: "#dc2626", fontWeight: 600 }}>+18.4%</td>
              <td style={{ padding: "8px 6px", fontWeight: 700, color: "#111827" }}>11:20 /km</td>
              <td style={{ padding: "8px 6px", color: "#4b5563" }}>9h 35m</td>
              <td style={{ padding: "8px 6px" }}><span style={{ background: "#fee2e2", color: "#dc2626", padding: "2px 6px", borderRadius: "4px", fontWeight: 700 }}>Power Hike</span></td>
            </tr>
            <tr>
              <td style={{ padding: "8px 6px", fontWeight: 700, color: "#111827" }}>Finish Dalat</td>
              <td style={{ padding: "8px 6px", color: "#4b5563" }}>100.0 km</td>
              <td style={{ padding: "8px 6px", color: "#059669", fontWeight: 600 }}>-2.1%</td>
              <td style={{ padding: "8px 6px", fontWeight: 700, color: "#111827" }}>7:55 /km</td>
              <td style={{ padding: "8px 6px", fontWeight: 800, color: "#059669" }}>14h 12m</td>
              <td style={{ padding: "8px 6px" }}><span style={{ background: "#ecfdf5", color: "#059669", padding: "2px 6px", borderRadius: "4px", fontWeight: 700 }}>Finished</span></td>
            </tr>
          </tbody>
        </table>
      </div>

      {/* ── 7. TOOL 2: GOAL DETERMINER A/B/C CARDS ────────────────── */}
      <div
        id="tool-goal-card"
        style={{
          width: "680px",
          background: "#ffffff",
          borderRadius: "20px",
          padding: "24px 28px",
          boxShadow: "0 20px 40px rgba(0,0,0,0.12)",
          border: "1px solid rgba(0,0,0,0.08)",
          boxSizing: "border-box",
        }}
      >
        <div style={{ marginBottom: "16px" }}>
          <div style={{ display: "inline-flex", alignItems: "center", gap: "6px", background: "rgba(25, 206, 139, 0.12)", color: "#059669", padding: "4px 10px", borderRadius: "9999px", fontSize: "11.5px", fontWeight: 700, marginBottom: "8px" }}>
            <Crosshair size={14} weight="bold" />
            <span>FINISH TIME PREDICTOR</span>
          </div>
          <h3 style={{ fontSize: "20px", fontWeight: 800, color: "#111827", margin: "0 0 4px" }}>
            Goal Determiner · Dalat Ultra Trail 100km
          </h3>
          <p style={{ fontSize: "12.5px", color: "#6b7280", margin: 0 }}>
            Calibrated from 5:45 min/km base flat pace + 16-week fitness adaptation (−4.0%)
          </p>
        </div>

        {/* 3 Asymmetric Goal Cards */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "12px", marginBottom: "16px" }}>
          {/* Card A */}
          <div style={{ border: "1px solid #e2e8f0", background: "#f8fafc", borderRadius: "14px", padding: "16px" }}>
            <div style={{ fontSize: "11.5px", fontWeight: 800, color: "#0284c7", textTransform: "uppercase" }}>
              GOAL A · AMBITIOUS
            </div>
            <div style={{ fontSize: "24px", fontWeight: 800, color: "#111827", margin: "6px 0 2px" }}>
              13h 45m
            </div>
            <div style={{ fontSize: "11.5px", color: "#64748b" }}>8:15 min/km avg</div>
            <div style={{ marginTop: "10px", display: "inline-block", background: "rgba(2, 132, 199, 0.1)", color: "#0284c7", fontSize: "11px", fontWeight: 700, padding: "2px 8px", borderRadius: "6px" }}>
              Top 8% finisher
            </div>
          </div>

          {/* Card B (Realistic) */}
          <div style={{ border: "2px solid #059669", background: "rgba(25, 206, 139, 0.05)", borderRadius: "14px", padding: "16px" }}>
            <div style={{ fontSize: "11.5px", fontWeight: 800, color: "#059669", textTransform: "uppercase" }}>
              GOAL B · REALISTIC
            </div>
            <div style={{ fontSize: "24px", fontWeight: 800, color: "#111827", margin: "6px 0 2px" }}>
              14h 30m
            </div>
            <div style={{ fontSize: "11.5px", color: "#64748b" }}>8:42 min/km avg</div>
            <div style={{ marginTop: "10px", display: "inline-block", background: "rgba(25, 206, 139, 0.15)", color: "#059669", fontSize: "11px", fontWeight: 700, padding: "2px 8px", borderRadius: "6px" }}>
              Top 18% (Target)
            </div>
          </div>

          {/* Card C (Safe) */}
          <div style={{ border: "1px solid #e2e8f0", background: "#f8fafc", borderRadius: "14px", padding: "16px" }}>
            <div style={{ fontSize: "11.5px", fontWeight: 800, color: "#d97706", textTransform: "uppercase" }}>
              GOAL C · SAFE
            </div>
            <div style={{ fontSize: "24px", fontWeight: 800, color: "#111827", margin: "6px 0 2px" }}>
              15h 40m
            </div>
            <div style={{ fontSize: "11.5px", color: "#64748b" }}>9:24 min/km avg</div>
            <div style={{ marginTop: "10px", display: "inline-block", background: "rgba(217, 119, 6, 0.1)", color: "#d97706", fontSize: "11px", fontWeight: 700, padding: "2px 8px", borderRadius: "6px" }}>
              Top 35% safe finish
            </div>
          </div>
        </div>

        <div style={{ display: "flex", gap: "10px" }}>
          <button style={{ flex: 1, padding: "10px", borderRadius: "10px", background: "#111827", color: "#ffffff", fontSize: "13px", fontWeight: 700, border: "none" }}>
            Plan Pacing for Goal B →
          </button>
          <button style={{ flex: 1, padding: "10px", borderRadius: "10px", background: "#f3f4f6", color: "#374151", fontSize: "13px", fontWeight: 600, border: "1px solid #e5e7eb" }}>
            Use for Training Plan
          </button>
        </div>
      </div>

      {/* ── 8. TOOL 3: GEAR FINDER TECHNICAL SHOE CARD ───────────── */}
      <div
        id="tool-gear-card"
        style={{
          width: "680px",
          background: "#ffffff",
          borderRadius: "20px",
          padding: "24px 28px",
          boxShadow: "0 20px 40px rgba(0,0,0,0.12)",
          border: "1px solid rgba(0,0,0,0.08)",
          boxSizing: "border-box",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "16px" }}>
          <div>
            <div style={{ display: "inline-flex", alignItems: "center", gap: "6px", background: "rgba(25, 206, 139, 0.12)", color: "#059669", padding: "4px 10px", borderRadius: "9999px", fontSize: "11.5px", fontWeight: 700, marginBottom: "8px" }}>
              <Sneaker size={14} weight="bold" />
              <span>CATALOG GROUNDED · NO HALLUCINATIONS</span>
            </div>
            <h3 style={{ fontSize: "20px", fontWeight: 800, color: "#111827", margin: "0 0 4px" }}>
              Gear Finder · Technical Trail Match
            </h3>
            <p style={{ fontSize: "12.5px", color: "#6b7280", margin: 0 }}>
              Matched to Dalat Ultra Trail 100km terrain (red clay, pine root singletrack, granite)
            </p>
          </div>
          <span style={{ fontSize: "11px", fontWeight: 800, background: "#ecfdf5", color: "#059669", padding: "4px 10px", borderRadius: "6px", border: "1px solid #a7f3d0" }}>
            98% COMPATIBILITY
          </span>
        </div>

        {/* Selected Shoe Card: Norda 005 */}
        <div style={{ border: "1px solid #e2e8f0", borderRadius: "14px", padding: "18px", background: "#f8fafc" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
            <div>
              <span style={{ fontSize: "11px", fontWeight: 700, color: "#64748b", textTransform: "uppercase" }}>NORDA</span>
              <h4 style={{ fontSize: "18px", fontWeight: 800, color: "#111827", margin: "2px 0 0" }}>005</h4>
            </div>
            <div style={{ fontSize: "16px", fontWeight: 800, color: "#059669" }}>$325</div>
          </div>

          {/* Specs Grid */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "8px", marginBottom: "14px" }}>
            <div style={{ background: "#ffffff", padding: "8px 10px", borderRadius: "8px", border: "1px solid #e2e8f0" }}>
              <div style={{ fontSize: "10.5px", color: "#64748b" }}>Stack / Drop</div>
              <div style={{ fontSize: "13px", fontWeight: 700, color: "#111827" }}>32.5/25.5mm (7mm)</div>
            </div>
            <div style={{ background: "#ffffff", padding: "8px 10px", borderRadius: "8px", border: "1px solid #e2e8f0" }}>
              <div style={{ fontSize: "10.5px", color: "#64748b" }}>Weight</div>
              <div style={{ fontSize: "13px", fontWeight: 700, color: "#111827" }}>214g (7.5 oz)</div>
            </div>
            <div style={{ background: "#ffffff", padding: "8px 10px", borderRadius: "8px", border: "1px solid #e2e8f0" }}>
              <div style={{ fontSize: "10.5px", color: "#64748b" }}>Outsole Grip</div>
              <div style={{ fontSize: "13px", fontWeight: 700, color: "#111827" }}>Vibram Megagrip Elite</div>
            </div>
            <div style={{ background: "#ffffff", padding: "8px 10px", borderRadius: "8px", border: "1px solid #e2e8f0" }}>
              <div style={{ fontSize: "10.5px", color: "#64748b" }}>Midsole Foam</div>
              <div style={{ fontSize: "13px", fontWeight: 700, color: "#111827" }}>Arnitel TPEE</div>
            </div>
          </div>

          <p style={{ fontSize: "12.5px", color: "#475569", lineHeight: 1.5, margin: "0 0 10px" }}>
            <strong>Coach Rationale:</strong> Ultralight 214g trail racer engineered for fast 100km terrain. High-rebound Arnitel TPEE midsole delivers smooth energy return without plate fatigue, while the Bio-Dyneema seamless upper and tacky Vibram Megagrip Elite outsole withstand abrasive volcanic dirt and slick roots.
          </p>

          <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
            <span style={{ fontSize: "11px", background: "rgba(25,206,139,0.12)", color: "#059669", fontWeight: 600, padding: "2px 8px", borderRadius: "6px" }}>
              Bio-Dyneema Seamless Upper
            </span>
            <span style={{ fontSize: "11px", background: "rgba(2,132,199,0.1)", color: "#0284c7", fontWeight: 600, padding: "2px 8px", borderRadius: "6px" }}>
              2024 JFK 50 Podium Shoe (Matt Seidel)
            </span>
            <span style={{ fontSize: "11px", background: "#f1f5f9", color: "#475569", fontWeight: 500, padding: "2px 8px", borderRadius: "6px" }}>
              Catalog Verified: Believe in the Run Review
            </span>
          </div>
        </div>
      </div>

      {/* ── 9. TOOL 4: NUTRITION LAB HOURLY FUEL PLAN ─────────────── */}
      <div
        id="tool-nutrition-card"
        style={{
          width: "680px",
          background: "#ffffff",
          borderRadius: "20px",
          padding: "24px 28px",
          boxShadow: "0 20px 40px rgba(0,0,0,0.12)",
          border: "1px solid rgba(0,0,0,0.08)",
          boxSizing: "border-box",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "16px" }}>
          <div>
            <div style={{ display: "inline-flex", alignItems: "center", gap: "6px", background: "rgba(25, 206, 139, 0.12)", color: "#059669", padding: "4px 10px", borderRadius: "9999px", fontSize: "11.5px", fontWeight: 700, marginBottom: "8px" }}>
              <BowlFood size={14} weight="bold" />
              <span>METABOLIC COMMAND CENTER</span>
            </div>
            <h3 style={{ fontSize: "20px", fontWeight: 800, color: "#111827", margin: "0 0 4px" }}>
              Nutrition Lab · Dalat Ultra Trail 100km
            </h3>
            <p style={{ fontSize: "12.5px", color: "#6b7280", margin: 0 }}>
              Hour-by-hour race fueling protocol derived from real product catalog
            </p>
          </div>
          <span style={{ fontSize: "11px", fontWeight: 700, background: "#ecfdf5", color: "#059669", padding: "4px 10px", borderRadius: "6px" }}>
            14.5 HR DURATION
          </span>
        </div>

        {/* Hourly Metabolic Targets */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "10px", background: "#f8fafc", padding: "12px 14px", borderRadius: "12px", border: "1px solid #e2e8f0", marginBottom: "16px" }}>
          <div>
            <div style={{ fontSize: "11px", color: "#64748b", fontWeight: 600 }}>Carb Target</div>
            <div style={{ fontSize: "17px", fontWeight: 800, color: "#059669" }}>60 g <span style={{ fontSize: "11px", fontWeight: 600 }}>/ hour</span></div>
          </div>
          <div>
            <div style={{ fontSize: "11px", color: "#64748b", fontWeight: 600 }}>Sodium Target</div>
            <div style={{ fontSize: "17px", fontWeight: 800, color: "#0284c7" }}>650 mg <span style={{ fontSize: "11px", fontWeight: 600 }}>/ hour</span></div>
          </div>
          <div>
            <div style={{ fontSize: "11px", color: "#64748b", fontWeight: 600 }}>Fluid Target</div>
            <div style={{ fontSize: "17px", fontWeight: 800, color: "#7c3aed" }}>550 ml <span style={{ fontSize: "11px", fontWeight: 600 }}>/ hour</span></div>
          </div>
        </div>

        {/* Hour-by-Hour Actions */}
        <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "12px", padding: "8px 12px", background: "#ffffff", borderRadius: "8px", border: "1px solid #e5e7eb" }}>
            <span style={{ fontFamily: "monospace", fontWeight: 800, fontSize: "12px", color: "#059669", background: "rgba(25,206,139,0.12)", padding: "2px 6px", borderRadius: "4px" }}>H 01–03</span>
            <div style={{ fontSize: "12.5px", color: "#111827", flex: 1 }}>
              1x Maurten GEL 100 (25g) + 500ml Skratch Hydration (20g carbs, 400mg sodium) + 15g Chews
            </div>
            <span style={{ fontSize: "11px", fontWeight: 700, color: "#059669" }}>60g / 400mg</span>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "12px", padding: "8px 12px", background: "#ffffff", borderRadius: "8px", border: "1px solid #e5e7eb" }}>
            <span style={{ fontFamily: "monospace", fontWeight: 800, fontSize: "12px", color: "#d97706", background: "rgba(217,119,6,0.12)", padding: "2px 6px", borderRadius: "4px" }}>H 04–06</span>
            <div style={{ fontSize: "12.5px", color: "#111827", flex: 1 }}>
              1x Maurten GEL 100 Caf 100 + 1x SaltStick Cap (215mg Na) + Precision Hydration Chew (30g)
            </div>
            <span style={{ fontSize: "11px", fontWeight: 700, color: "#d97706" }}>65g / 650mg</span>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "12px", padding: "8px 12px", background: "#ffffff", borderRadius: "8px", border: "1px solid #e5e7eb" }}>
            <span style={{ fontFamily: "monospace", fontWeight: 800, fontSize: "12px", color: "#7c3aed", background: "rgba(124,58,237,0.12)", padding: "2px 6px", borderRadius: "4px" }}>CP3 52km</span>
            <div style={{ fontSize: "12.5px", color: "#111827", flex: 1 }}>
              Aid Station Solid Fuel: Boiled salted potato (30g carbs) + Warm broth (500mg Na)
            </div>
            <span style={{ fontSize: "11px", fontWeight: 700, color: "#7c3aed" }}>Solid Fuel</span>
          </div>
        </div>
      </div>
    </div>
  );
}
