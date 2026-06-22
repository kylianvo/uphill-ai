import re

with open("frontend/src/app/page.tsx", "r") as f:
    content = f.read()

# Insert the logo above the hero headline
old_headline = '<h1 className="hero-headline">'
new_logo_block = """<div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: "10px", marginBottom: "16px", color: "var(--text-primary)" }}>
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--accent-primary)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M3 15l5-5 4 4 9-9" />
              <polyline points="16 5 21 5 21 10" />
            </svg>
            <span style={{ fontSize: "40px", fontWeight: "700", letterSpacing: "-1.5px", fontFamily: "var(--font-schibsted)" }}>
              Uphill<span style={{ color: "var(--accent-primary)" }}>.AI</span>
            </span>
          </div>
          <h1 className="hero-headline">"""

content = content.replace(old_headline, new_logo_block)

with open("frontend/src/app/page.tsx", "w") as f:
    f.write(content)
