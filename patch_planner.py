import re

with open("frontend/src/app/page.tsx", "r") as f:
    page = f.read()

# Make sure Plus, ArrowsLeftRight are imported
if "ArrowsLeftRight" not in page:
    page = page.replace("import { \n  Lightbulb, Sneaker, Plant", "import { \n  Plus, ArrowsLeftRight, Heartbeat, Clock, Calendar, Lightbulb, Sneaker, Plant")


# 1. New Plan Button
old_new_plan_btn = """<button
                    className="btn btn-secondary"
                    style={{ flex: 1, minWidth: "120px", fontSize: "12px", height: "36px" }}
                    onClick={() => {
                      setBackupActivePlan(activePlan);
                      setBackupWorkouts(workouts);
                      setActivePlan(null);
                    }}
                  >
                    {lang === "en" ? "New Plan" : "Kế hoạch mới"}
                  </button>"""
new_new_plan_btn = """<button
                    className="btn btn-primary"
                    style={{ flex: 1, minWidth: "120px", fontSize: "13px", fontWeight: "600", height: "38px", display: "flex", alignItems: "center", justifyContent: "center", gap: "6px", boxShadow: "0 4px 12px rgba(25, 206, 139, 0.2)" }}
                    onClick={() => {
                      setBackupActivePlan(activePlan);
                      setBackupWorkouts(workouts);
                      setActivePlan(null);
                    }}
                  >
                    <Plus size={16} weight="bold" />
                    {lang === "en" ? "New Plan" : "Kế hoạch mới"}
                  </button>"""
page = page.replace(old_new_plan_btn, new_new_plan_btn)


# 2. Swap Options
# First, remove the old Swap Day Controller completely
old_swap_controller = """            {/* Swap Day Controller */}
            <div style={{ display: "flex", flexDirection: isMobile ? "column" : "row", gap: "8px", alignItems: isMobile ? "stretch" : "center", background: "rgba(255,255,255,0.15)", border: "1px solid var(--border-color)", padding: "12px", borderRadius: "12px", marginBottom: "16px" }}>
              <div style={{ fontSize: "12.5px", fontWeight: "600", color: "var(--accent-secondary)" }}>
                🔄 {lang === "en" ? "Swap:" : "Tráo đổi:"}
              </div>
              <div style={{ display: "flex", gap: "6px", alignItems: "center", flex: 1 }}>
                <select
                  className="chat-input"
                  style={{ flex: 1, padding: "4px 8px", height: "30px", fontSize: "12px", borderRadius: "6px" }}
                  value={swapDay1}
                  onChange={(e) => setSwapDay1(e.target.value)}
                >
                  {["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"].map(d => {
                    const label = lang === "vi"
                      ? d.replace("Monday", "T2").replace("Tuesday", "T3").replace("Wednesday", "T4").replace("Thursday", "T5").replace("Friday", "T6").replace("Saturday", "T7").replace("Sunday", "CN")
                      : d.substring(0, 3);
                    return <option key={d} value={d}>{label}</option>;
                  })}
                </select>
                <span style={{ fontSize: "11px" }}>↔️</span>
                <select
                  className="chat-input"
                  style={{ flex: 1, padding: "4px 8px", height: "30px", fontSize: "12px", borderRadius: "6px" }}
                  value={swapDay2}
                  onChange={(e) => setSwapDay2(e.target.value)}
                >
                  {["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"].map(d => {
                    const label = lang === "vi"
                      ? d.replace("Monday", "T2").replace("Tuesday", "T3").replace("Wednesday", "T4").replace("Thursday", "T5").replace("Friday", "T6").replace("Saturday", "T7").replace("Sunday", "CN")
                      : d.substring(0, 3);
                    return <option key={d} value={d}>{label}</option>;
                  })}
                </select>
              </div>
              <button className="btn btn-primary" style={{ padding: "6px 12px", height: "30px", fontSize: "12px", borderRadius: "6px", width: isMobile ? "100%" : "auto" }} onClick={handleSwapWorkouts}>
                {lang === "en" ? "Apply" : "Áp dụng"}
              </button>
            </div>"""

if old_swap_controller in page:
    page = page.replace(old_swap_controller, "")

# Now inject it into the Weekly Header
old_weekly_header = """                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", paddingBottom: "12px", marginBottom: "16px", borderBottom: "1px solid var(--border-color)" }}>
                  <div style={{ display: "flex", flexDirection: "column" }}>
                    <span style={{ fontSize: "10px", color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: "0.05em", fontWeight: "700" }}>
                      {lang === "en" ? `Weekly Volume (Wk ${selectedWeek})` : `Thể tích tuần (Tuần ${selectedWeek})`}
                    </span>
                    <div style={{ display: "flex", alignItems: "baseline", gap: "6px" }}>
                      <span style={{ fontSize: "18px", fontWeight: "800", color: "var(--accent-primary)" }}>{weeklyKm.toFixed(1)} km</span>
                      <span style={{ fontSize: "13px", color: "var(--text-muted)", fontWeight: "600" }}>/ {weeklyHours} {lang === "en" ? "hrs" : "giờ"}</span>
                    </div>
                  </div>
                </div>"""

new_weekly_header = """                <div style={{ display: "flex", flexDirection: isMobile ? "column" : "row", gap: "12px", justifyContent: "space-between", alignItems: isMobile ? "flex-start" : "center", paddingBottom: "12px", marginBottom: "16px", borderBottom: "1px solid var(--border-color)" }}>
                  <div style={{ display: "flex", flexDirection: "column" }}>
                    <span style={{ fontSize: "10px", color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: "0.05em", fontWeight: "700" }}>
                      {lang === "en" ? `Weekly Volume (Wk ${selectedWeek})` : `Thể tích tuần (Tuần ${selectedWeek})`}
                    </span>
                    <div style={{ display: "flex", alignItems: "baseline", gap: "6px" }}>
                      <span style={{ fontSize: "18px", fontWeight: "800", color: "var(--accent-primary)" }}>{weeklyKm.toFixed(1)} km</span>
                      <span style={{ fontSize: "13px", color: "var(--text-muted)", fontWeight: "600" }}>/ {weeklyHours} {lang === "en" ? "hrs" : "giờ"}</span>
                    </div>
                  </div>

                  {/* Inline Swap Options */}
                  <div style={{ display: "flex", gap: "4px", alignItems: "center", background: "rgba(255,255,255,0.5)", border: "1px solid rgba(0,0,0,0.05)", padding: "4px", borderRadius: "999px", boxShadow: "inset 0 1px 0 rgba(255,255,255,0.5)" }}>
                    <select
                      className="chat-input"
                      style={{ padding: "0 10px", height: "26px", fontSize: "12px", borderRadius: "999px", border: "none", background: "transparent", fontWeight: "600", cursor: "pointer", appearance: "none", outline: "none" }}
                      value={swapDay1}
                      onChange={(e) => setSwapDay1(e.target.value)}
                    >
                      {["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"].map(d => {
                        const label = lang === "vi" ? d.replace("Monday", "T2").replace("Tuesday", "T3").replace("Wednesday", "T4").replace("Thursday", "T5").replace("Friday", "T6").replace("Saturday", "T7").replace("Sunday", "CN") : d.substring(0, 3);
                        return <option key={d} value={d}>{label}</option>;
                      })}
                    </select>
                    
                    <button onClick={handleSwapWorkouts} style={{ background: "var(--accent-primary)", color: "#111", border: "none", borderRadius: "50%", width: "24px", height: "24px", display: "flex", alignItems: "center", justifyContent: "center", cursor: "pointer", boxShadow: "0 2px 6px rgba(25, 206, 139, 0.4)" }}>
                      <ArrowsLeftRight size={14} weight="bold" />
                    </button>

                    <select
                      className="chat-input"
                      style={{ padding: "0 10px", height: "26px", fontSize: "12px", borderRadius: "999px", border: "none", background: "transparent", fontWeight: "600", cursor: "pointer", appearance: "none", outline: "none" }}
                      value={swapDay2}
                      onChange={(e) => setSwapDay2(e.target.value)}
                    >
                      {["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"].map(d => {
                        const label = lang === "vi" ? d.replace("Monday", "T2").replace("Tuesday", "T3").replace("Wednesday", "T4").replace("Thursday", "T5").replace("Friday", "T6").replace("Saturday", "T7").replace("Sunday", "CN") : d.substring(0, 3);
                        return <option key={d} value={d}>{label}</option>;
                      })}
                    </select>
                  </div>
                </div>"""
page = page.replace(old_weekly_header, new_weekly_header)

# 3. Return to Running settings
page = page.replace('<span>{lang === "en" ? "or" : "hoặc"}</span>\n                    <select', '<select')
page = page.replace('🔄 {lang === "en" ? "Load Recent Plan" : "Tải lịch tập gần đây"}', '{lang === "en" ? "Load Recent Plan..." : "Tải lịch tập gần đây..."}')

# 4. Glowing CTA
old_generate_btn = """<button 
                  className="btn btn-primary" 
                  style={{ width: "100%", padding: "14px", fontSize: "16px" }} 
                  onClick={generatePlan}
                >"""
new_generate_btn = """<button 
                  className="btn btn-primary" 
                  style={{ width: "100%", padding: "14px", fontSize: "16px", boxShadow: "0 0 24px rgba(25, 206, 139, 0.5), inset 0 1px 1px rgba(255,255,255,0.3)", transition: "all 0.3s ease" }} 
                  onClick={generatePlan}
                >"""
page = page.replace(old_generate_btn, new_generate_btn)

with open("frontend/src/app/page.tsx", "w") as f:
    f.write(page)
