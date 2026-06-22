with open("frontend/src/app/page.tsx", "r") as f:
    page = f.read()

# 1. Fix Planner Goals
old_planner_goals = """                {([
                  { val: "race",          emoji: "🏆", label: t("goal_race").replace(" 🏆", "") },
                  { val: "distance",      emoji: "📏", label: t("goal_distance").replace(" 📏", "") },
                  { val: "start_running", label: t("goal_start").replace(" 🌱", "") },
                  { val: "return",        emoji: "🔄", label: t("goal_return").replace(" 🔄", "") },
                  { val: "recovery",      emoji: "💤", label: t("goal_recovery").replace(" 💤", "") },
                ] as const).map(({ val, emoji, label }) => {"""

new_planner_goals = """                {([
                  { val: "race",          Icon: Trophy, label: t("goal_race").replace(" 🏆", "") },
                  { val: "distance",      Icon: Target, label: t("goal_distance").replace(" 📏", "") },
                  { val: "start_running", Icon: Sneaker, label: t("goal_start").replace(" 🌱", "") },
                  { val: "return",        Icon: PersonSimpleRun, label: t("goal_return").replace(" 🔄", "") },
                  { val: "recovery",      Icon: Bed, label: t("goal_recovery").replace(" 💤", "") },
                ] as const).map(({ val, Icon, label }) => {"""
page = page.replace(old_planner_goals, new_planner_goals)
page = page.replace('<span style={{ fontSize: "18px" }}>{emoji}</span>', '<Icon size={24} weight="duotone" />')

# 2. Fix Onboarding Goals
old_onboarding_goals = """                {[
                  { val: "race", emoji: "🏆", label: lang === "en" ? "Race (target event)" : "Giải chạy (sự kiện mục tiêu)" },
                  { val: "distance", emoji: "📏", label: lang === "en" ? "Run a Specific Distance" : "Chạy một cự ly cụ thể" },
                  { val: "start_running", label: lang === "en" ? "Start Running" : "Bắt đầu chạy bộ" },
                  { val: "return", emoji: "🔄", label: lang === "en" ? "Get Back to Running" : "Tập luyện chạy bộ trở lại" },
                  { val: "recovery", emoji: "💤", label: lang === "en" ? "Post-Race Recovery" : "Phục hồi sau cuộc đua" },
                ].map(({ val, emoji, label }) => ("""

new_onboarding_goals = """                {[
                  { val: "race", Icon: Trophy, label: lang === "en" ? "Race (target event)" : "Giải chạy (sự kiện mục tiêu)" },
                  { val: "distance", Icon: Target, label: lang === "en" ? "Run a Specific Distance" : "Chạy một cự ly cụ thể" },
                  { val: "start_running", Icon: Sneaker, label: lang === "en" ? "Start Running" : "Bắt đầu chạy bộ" },
                  { val: "return", Icon: PersonSimpleRun, label: lang === "en" ? "Get Back to Running" : "Tập luyện chạy bộ trở lại" },
                  { val: "recovery", Icon: Bed, label: lang === "en" ? "Post-Race Recovery" : "Phục hồi sau cuộc đua" },
                ].map(({ val, Icon, label }) => ("""
page = page.replace(old_onboarding_goals, new_onboarding_goals)

page = page.replace('style={{ ...optBtn(val, label, emoji), display: "flex", alignItems: "center", gap: "10px", textAlign: "left" as const }}>', 'style={{ ...optBtn(val, label), display: "flex", alignItems: "center", gap: "10px", textAlign: "left" as const }}>')
page = page.replace('<span style={{ fontSize: "20px" }}>{emoji}</span>', '<Icon size={24} color="var(--accent-primary)" weight="duotone" />')

with open("frontend/src/app/page.tsx", "w") as f:
    f.write(page)
