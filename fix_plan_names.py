with open("frontend/src/app/page.tsx", "r") as f:
    page = f.read()

# 1. Fix formatPlanName
old_format = """  const formatPlanName = (p: ActivePlan) => {
    const dist = getPlanDistance(p);
    const elev = getPlanElevation(p);
    const kmStr = dist ? `${dist}km` : "0km";
    const gainStr = elev ? `+${elev}m` : "+0m";
    let targetStr = "Finish";
    if (p.goal_type === "time" && p.target_time_hours) {
      targetStr = `${p.target_time_hours}h`;
    } else if (p.goal_type === "optimal") {
      targetStr = "Optimal";
    } else if (p.goal_type) {
      targetStr = p.goal_type.charAt(0).toUpperCase() + p.goal_type.slice(1);
    }
    return `${p.race_name || "Untitled Plan"} - ${p.race_date || "No Date"} - ${kmStr} - ${gainStr} - ${targetStr}`;
  };"""

new_format = """  const formatPlanName = (p: ActivePlan) => {
    const dist = getPlanDistance(p);
    const elev = getPlanElevation(p);
    const kmStr = dist ? `${dist}km` : "0km";
    const gainStr = elev ? `+${elev}m` : "+0m";
    let targetStr = "Finish";
    let dateStr = p.race_date || "No Date";

    if (p.goal_type === "time" && p.target_time_hours) {
      targetStr = `${p.target_time_hours}h`;
    } else if (p.goal_type === "optimal") {
      targetStr = "Optimal";
    } else if (p.goal_type) {
      targetStr = p.goal_type.charAt(0).toUpperCase() + p.goal_type.slice(1).replace("_", " ");
    }
    
    if (["start_running", "return", "recovery"].includes(p.goal_type || "")) {
      dateStr = `Ends ${p.race_date}`;
      return `${p.race_name || "Untitled Plan"} (${dateStr}) | ${targetStr}`;
    } else {
      dateStr = `Race: ${p.race_date}`;
      return `${p.race_name || "Untitled Plan"} (${dateStr}) | ${kmStr} | +${elev || 0}m | ${targetStr}`;
    }
  };"""
page = page.replace(old_format, new_format)


# 2. Fix active plan header
old_header = """                <p style={{ color: "var(--text-secondary)", fontSize: "12px", marginTop: "2px" }}>
                  {activePlan.race_date} | {activePlan.goal_type === "finish" 
                    ? (lang === "en" ? "Simply Finish" : "Chỉ cần Hoàn thành")
                    : activePlan.goal_type === "time"
                      ? (lang === "en" ? "Time Target" : "Mục tiêu Thời gian")
                      : activePlan.goal_type === "optimal"
                        ? (lang === "en" ? "Optimal Performance" : "Hiệu suất Tối ưu")
                        : activePlan.goal_type.toUpperCase()}
                </p>"""

new_header = """                <p style={{ color: "var(--text-secondary)", fontSize: "12px", marginTop: "2px", fontWeight: "500" }}>
                  {(() => {
                    const goal = activePlan.goal_type || "";
                    if (["start_running", "return", "recovery"].includes(goal)) {
                      if (workouts.length > 0) {
                        return `${workouts[0].date} ➡️ ${activePlan.race_date}`;
                      }
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
                </p>"""
page = page.replace(old_header, new_header)

with open("frontend/src/app/page.tsx", "w") as f:
    f.write(page)
