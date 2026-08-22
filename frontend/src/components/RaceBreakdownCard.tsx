import React from "react";
import { FlagBanner, Users, CalendarBlank } from "@phosphor-icons/react";
import { RaceBreakdownEntry } from "../hooks/useCoachOverview";

interface RaceBreakdownCardProps {
  races: RaceBreakdownEntry[];
  athletesWithoutRace?: number;
  selectedRace?: string | null;
  onSelectRace?: (raceName: string | null) => void;
  lang: "en" | "vi";
}

export default function RaceBreakdownCard({
  races,
  athletesWithoutRace = 0,
  selectedRace = null,
  onSelectRace,
  lang,
}: RaceBreakdownCardProps) {
  const totalRacedAthletes = races.reduce((sum, r) => sum + r.count, 0);

  return (
    <div
      className="snow-glass"
      style={{
        borderRadius: "16px",
        padding: "18px 20px",
        display: "flex",
        flexDirection: "column",
        gap: "14px",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <FlagBanner size={18} weight="duotone" style={{ color: "var(--accent-primary)" }} />
          <h4 style={{ margin: 0, fontSize: "15px", fontWeight: 700, color: "var(--text-primary)" }}>
            {lang === "en" ? "Target Race Distribution" : "Phân bổ race mục tiêu"}
          </h4>
        </div>
        <span
          style={{
            fontSize: "11.5px",
            fontWeight: 600,
            color: "var(--text-primary)",
            background: "rgba(255, 255, 255, 0.5)",
            padding: "3px 10px",
            borderRadius: "12px",
            border: "1px solid rgba(0, 0, 0, 0.08)",
            boxShadow: "0 1px 3px rgba(0,0,0,0.04)",
          }}
        >
          {lang === "en"
            ? `${races.length} ${races.length === 1 ? "race" : "races"} (${totalRacedAthletes} runners)`
            : `${races.length} race (${totalRacedAthletes} VĐV)`}
        </span>
      </div>

      {races.length === 0 ? (
        <p style={{ margin: 0, fontSize: "13px", color: "var(--text-secondary)" }}>
          {lang === "en"
            ? "No athletes currently have an active plan with a target race."
            : "Chưa có VĐV nào có giáo án với race mục tiêu."}
        </p>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
          {races.map((race) => {
            const isSelected = selectedRace === race.race_name;
            return (
              <div
                key={race.race_name}
                onClick={() => onSelectRace && onSelectRace(isSelected ? null : race.race_name)}
                style={{
                  display: "flex",
                  flexDirection: "column",
                  gap: "8px",
                  padding: "12px 14px",
                  borderRadius: "10px",
                  background: isSelected
                    ? "rgba(99, 102, 241, 0.14)"
                    : "rgba(255, 255, 255, 0.4)",
                  border: isSelected ? "1.5px solid var(--accent-primary)" : "1px solid rgba(0, 0, 0, 0.07)",
                  cursor: onSelectRace ? "pointer" : "default",
                  transition: "all 0.15s ease",
                  boxShadow: isSelected
                    ? "0 3px 12px rgba(99, 102, 241, 0.18)"
                    : "0 1px 3px rgba(0, 0, 0, 0.03)",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                    <span style={{ fontSize: "13.5px", fontWeight: 700, color: "var(--text-primary)" }}>
                      {race.race_name}
                    </span>
                    {race.race_date && (
                      <span
                        style={{
                          fontSize: "11px",
                          fontWeight: 500,
                          color: "var(--text-muted)",
                          display: "inline-flex",
                          alignItems: "center",
                          gap: "3px",
                        }}
                      >
                        <CalendarBlank size={12} />
                        {race.race_date}
                      </span>
                    )}
                  </div>
                  <span
                    style={{
                      fontSize: "11.5px",
                      fontWeight: 700,
                      color: isSelected ? "#ffffff" : "var(--accent-primary)",
                      background: isSelected ? "var(--accent-primary)" : "rgba(99, 102, 241, 0.12)",
                      padding: "3px 9px",
                      borderRadius: "10px",
                      display: "inline-flex",
                      alignItems: "center",
                      gap: "4px",
                      boxShadow: isSelected ? "0 2px 6px rgba(99, 102, 241, 0.3)" : "none",
                    }}
                  >
                    <Users size={13} weight="bold" />
                    {lang === "en"
                      ? `${race.count} ${race.count === 1 ? "runner" : "runners"}`
                      : `${race.count} VĐV`}
                  </span>
                </div>

                {race.athletes && race.athletes.length > 0 && (
                  <div style={{ display: "flex", flexWrap: "wrap", gap: "6px", marginTop: "2px" }}>
                    {race.athletes.map((ath) => (
                      <span
                        key={ath.athlete_id}
                        style={{
                          fontSize: "11px",
                          fontWeight: 500,
                          color: "var(--text-secondary)",
                          background: "rgba(255, 255, 255, 0.65)",
                          border: "1px solid rgba(0, 0, 0, 0.08)",
                          padding: "2px 8px",
                          borderRadius: "6px",
                        }}
                      >
                        {ath.name}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {athletesWithoutRace > 0 && (
        <div
          style={{
            fontSize: "12px",
            color: "var(--text-muted)",
            borderTop: "1px dashed var(--border-color)",
            paddingTop: "10px",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <span>{lang === "en" ? "Athletes without target race:" : "VĐV chưa có race mục tiêu:"}</span>
          <span style={{ fontWeight: 700, color: "var(--text-primary)" }}>{athletesWithoutRace}</span>
        </div>
      )}
    </div>
  );
}
