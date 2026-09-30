import React from "react";
import { useAppContext } from "../contexts/AppContext";

// Minimal stub: Task 3 replaces this with the real Me screen.
export default function MeView({ isMobile }: { isMobile: boolean }) {
  const { handleTabSwitch } = useAppContext();
  const rows: { label: string; tab: "tools" | "knowledge" | "about" }[] = [
    { label: "Gear Finder", tab: "tools" },
    { label: "Knowledge Hub", tab: "knowledge" },
    { label: "About Uphill", tab: "about" },
  ];
  return (
    <div style={{ maxWidth: isMobile ? undefined : 640, margin: "0 auto" }}>
      <h2>Me</h2>
      <h3>More</h3>
      <ul style={{ listStyle: "none", padding: 0, display: "flex", flexDirection: "column", gap: 8 }}>
        {rows.map((r) => (
          <li key={r.tab}>
            <button type="button" className="btn" onClick={() => handleTabSwitch(r.tab)} style={{ width: "100%", textAlign: "left" }}>
              {r.label}
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
