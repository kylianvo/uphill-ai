with open("frontend/src/app/page.tsx", "r") as f:
    page = f.read()

old_card_style = """                  <div
                    key={wo.id}
                    style={{
                      background: rest ? "rgba(255,255,255,0.1)" : "var(--bg-card)",
                      border: "1px solid",
                      borderColor: wo.is_completed ? "var(--accent-success)" : "var(--border-color)",
                      borderRadius: "12px",
                      padding: isMobile ? "14px" : "20px",
                      opacity: rest ? 0.75 : 1,
                      display: "grid",
                      gridTemplateColumns: isMobile ? "1fr" : "70px 1.6fr 1.1fr",
                      gap: isMobile ? "10px" : "16px",
                      alignItems: "start",
                    }}
                  >"""

new_card_style = """                  <div
                    key={wo.id}
                    style={{
                      background: rest ? "rgba(255,255,255,0.05)" : "var(--bg-card)",
                      backdropFilter: "blur(20px)",
                      WebkitBackdropFilter: "blur(20px)",
                      boxShadow: "inset 0 1px 0 rgba(255,255,255,0.4), 0 8px 24px rgba(0,0,0,0.05)",
                      border: "1px solid",
                      borderColor: wo.is_completed ? "var(--accent-success)" : "var(--border-color)",
                      borderRadius: "12px",
                      padding: isMobile ? "14px" : "20px",
                      opacity: rest ? 0.75 : 1,
                      display: "grid",
                      gridTemplateColumns: isMobile ? "1fr" : "70px 1.6fr 1.1fr",
                      gap: isMobile ? "10px" : "16px",
                      alignItems: "start",
                    }}
                  >"""
page = page.replace(old_card_style, new_card_style)

with open("frontend/src/app/page.tsx", "w") as f:
    f.write(page)
