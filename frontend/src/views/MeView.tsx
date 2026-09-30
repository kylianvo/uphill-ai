import React, { useEffect } from "react";
import { useAppContext } from "../contexts/AppContext";
import { usePaceZones } from "../hooks/usePaceZones";
import ConnectedAccounts from "../components/ConnectedAccounts";
import RaceHistoryPanel from "../components/RaceHistoryPanel";

const card: React.CSSProperties = {
  background: "var(--bg-card)",
  border: "1px solid var(--border-color)",
  borderRadius: 12,
  padding: 16,
};
const h3: React.CSSProperties = { fontSize: 14, fontWeight: 700, margin: "0 0 10px", color: "var(--text-primary)" };

function MoreRow({ label, value, onClick }: { label: string; value?: string; onClick: () => void }) {
  return (
    <button
      type="button"
      className="me-row"
      onClick={onClick}
      style={{
        display: "flex", alignItems: "center", justifyContent: "space-between", width: "100%",
        minHeight: 48, padding: "0 4px", background: "none", border: "none",
        borderBottom: "1px solid var(--border-color)", color: "var(--text-primary)",
        fontSize: 15, textAlign: "left", cursor: "pointer",
      }}
    >
      <span>{label}</span>
      <span style={{ color: "var(--text-muted)", display: "flex", gap: 8 }}>
        {value && <span>{value}</span>}
        <span aria-hidden="true">›</span>
      </span>
    </button>
  );
}

export default function MeView({ isMobile }: { isMobile: boolean }) {
  const { handleTabSwitch, user, lang, setLang, activePlan, setProfileSettingsOpen, handleLogout } = useAppContext();
  const { zones, fetchPaceZones } = usePaceZones();
  const hasPlan = !!activePlan && !!user;

  useEffect(() => {
    if (hasPlan) fetchPaceZones();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hasPlan]);

  const name = user?.name || user?.email || "Athlete";
  const paces: { label: string; value?: string | null }[] = [
    { label: "Z2", value: zones?.zone2_pace },
    { label: "Threshold", value: zones?.threshold_pace ?? zones?.zone4_pace },
    { label: "VO2", value: zones?.zone5_pace },
  ];
  const rows: { label: string; tab: "tools" | "knowledge" | "about" }[] = [
    { label: "Gear Finder", tab: "tools" },
    { label: "Knowledge Hub", tab: "knowledge" },
    { label: "About Uphill", tab: "about" },
  ];

  return (
    <div style={{ maxWidth: isMobile ? undefined : 640, margin: "0 auto", display: "flex", flexDirection: "column", gap: 16 }}>
      <style>{`.me-row:focus-visible,.me-edit:focus-visible{outline:2px solid var(--accent-color, #22c55e);outline-offset:2px}`}</style>
      <h2 style={{ margin: 0 }}>Me</h2>

      <section style={{ ...card, display: "flex", alignItems: "center", gap: 12 }}>
        <div aria-hidden="true" style={{ width: 44, height: 44, borderRadius: "50%", background: "var(--border-color)", display: "flex", alignItems: "center", justifyContent: "center", fontWeight: 700 }}>
          {name.charAt(0).toUpperCase()}
        </div>
        <div style={{ flex: 1, fontWeight: 600 }}>{name}</div>
        <button type="button" className="btn me-edit" style={{ minHeight: 44 }} onClick={() => setProfileSettingsOpen(true)}>
          Edit profile
        </button>
      </section>

      <section style={card}>
        <h3 style={h3}>My paces</h3>
        {hasPlan ? (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 8, textAlign: "center" }}>
            {paces.map((p) => (
              <div key={p.label}>
                <div style={{ fontSize: 12, color: "var(--text-muted)" }}>{p.label}</div>
                <div style={{ fontWeight: 600 }}>{p.value ? `${p.value} /km` : "—"}</div>
              </div>
            ))}
          </div>
        ) : (
          <p style={{ margin: 0, color: "var(--text-muted)", fontSize: 14 }}>Paces appear once you have a plan.</p>
        )}
      </section>

      <section style={card}>
        <h3 style={h3}>Watches</h3>
        <ConnectedAccounts />
      </section>

      <section style={card}>
        <h3 style={h3}>Race history</h3>
        <RaceHistoryPanel lang={lang} />
      </section>

      <section style={card}>
        <h3 style={h3}>More</h3>
        <div style={{ display: "flex", flexDirection: "column" }}>
          {rows.map((r) => (
            <MoreRow key={r.tab} label={r.label} onClick={() => handleTabSwitch(r.tab)} />
          ))}
          <MoreRow label="Language" value={lang === "en" ? "English" : "Tiếng Việt"} onClick={() => setLang(lang === "en" ? "vi" : "en")} />
          <MoreRow label="Sign out" onClick={handleLogout} />
        </div>
      </section>
    </div>
  );
}
