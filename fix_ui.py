import re

# 1. Update globals.css for transparency and inputs
with open("frontend/src/app/globals.css", "r") as f:
    css = f.read()

# Make boxes more transparent
css = css.replace('--bg-main:           rgba(255, 255, 255, 0.4);', '--bg-main:           rgba(255, 255, 255, 0.15);')
css = css.replace('--bg-card:           rgba(255, 255, 255, 0.3);', '--bg-card:           rgba(255, 255, 255, 0.08);')

# Fix input field visibility
# Replace the old input[type="text"].chat-input block
old_input_css = """input[type="text"].chat-input,
.chat-pane .chat-input {"""
new_input_css = """input.chat-input,
select.chat-input,
textarea.chat-input,
.chat-pane .chat-input {"""
css = css.replace(old_input_css, new_input_css)

# Ensure the background is solid enough to read, but glass-like
# We will just change the properties of .chat-input to ensure text is visible
css = re.sub(r'background:\s*#ffffff\s*!important;', 'background: rgba(255, 255, 255, 0.85) !important;\n  backdrop-filter: blur(12px) !important;', css)
css = re.sub(r'color:\s*#111111\s*!important;', 'color: #000000 !important;\n  font-weight: 500 !important;', css)


with open("frontend/src/app/globals.css", "w") as f:
    f.write(css)


# 2. Update page.tsx for emojis
with open("frontend/src/app/page.tsx", "r") as f:
    page = f.read()

# Add Phosphor icon imports
page = page.replace('import { \n  Code, Robot', 'import { \n  Lightbulb, Sneaker, Plant, Code, Robot')

# Replace emojis
page = page.replace('<span style={{ fontSize: "26px" }}>💡</span>', '<Lightbulb size={26} color="var(--accent-primary)" weight="duotone" />')
page = page.replace('🍌 {lang === "en" ? "Precision Fueling Engine" : "Công cụ Dinh dưỡng Chính xác"}', '<span style={{ display: "flex", alignItems: "center", gap: "6px" }}><BowlFood size={20} color="var(--accent-primary)" weight="duotone" /> {lang === "en" ? "Precision Fueling Engine" : "Công cụ Dinh dưỡng Chính xác"}</span>')
page = page.replace('<span>👟 {lang === "en" ? "Gear Finder" : "Tìm kiếm Thiết bị"}</span>', '<span style={{ display: "flex", alignItems: "center", gap: "6px" }}><Sneaker size={20} color="var(--accent-primary)" weight="duotone" /> {lang === "en" ? "Gear Finder" : "Tìm kiếm Thiết bị"}</span>')

# Remove emojis from dropdowns (native <select> options can only contain text)
page = page.replace('{ val: "start_running", emoji: "🌱", label: t("goal_start").replace(" 🌱", "") }', '{ val: "start_running", label: t("goal_start").replace(" 🌱", "") }')
page = page.replace('{ val: "start_running", emoji: "🌱", label: lang === "en" ? "Start Running" : "Bắt đầu chạy bộ" }', '{ val: "start_running", label: lang === "en" ? "Start Running" : "Bắt đầu chạy bộ" }')
page = page.replace('lang === "en" ? "🌱 Start Running Program" : "🌱 Lộ trình Bắt đầu Chạy bộ"', 'lang === "en" ? "Start Running Program" : "Lộ trình Bắt đầu Chạy bộ"')
page = page.replace('lang === "en" ? "👟 Balanced" : "👟 Cân bằng (Balanced)"', 'lang === "en" ? "Balanced" : "Cân bằng (Balanced)"')

# Fix inline styles for inputs that might override the CSS
page = page.replace('background: "rgba(255,255,255,0.5)"', 'background: "transparent"')

with open("frontend/src/app/page.tsx", "w") as f:
    f.write(page)
