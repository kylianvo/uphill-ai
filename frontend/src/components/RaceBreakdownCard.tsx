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
      style={{
        background: "var(--bg-surface)",
        border: "1px solid var(--border-color)",
        borderRadius: "10px",
        padding: "16px 20px",
        display: "flex",
        flexDirection: "column",
        gap: "14px",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <FlagBanner size={16} style={{ color: "var(--accent-primary)" }} />
          <h4 style={{ margin: 0, fontSize: "14px", fontWeight: 600, color: "var(--text-primary)" }}>
            {lang === "en" ? "Target Race Distribution" : "Phân bổ theo giải đấu"}
          </h4>
        </div>
        <span
          style={{
            fontSize: "11px",
            color: "var(--text-muted)",
            background: "var(--bg-hover, rgba(255,255,255,0.05))",
            padding: "2px 8px",
            borderRadius: "12px",
            border: "1px solid var(--border-color)",
          }}
        >
          {lang === "en"
            ? `${races.length} ${races.length === 1 ? "race" : "races"} (${totalRacedAthletes} runners)`
            : `${races.length} giải (${totalRacedAthletes} VĐV)`}
        </span>
      </div>

      {races.length === 0 ? (
        <p style={{ margin: 0, fontSize: "13px", color: "var(--text-secondary)" }}>
          {lang === "en"
            ? "No athletes currently have an active plan with a target race."
            : "Chưa có vận động viên nào có kế hoạch với giải đấu mục tiêu."}
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
                  gap: "6px",
                  padding: "10px 12px",
                  borderRadius: "8px",
                  background: isSelected
                    ? "var(--accent-primary-subtle, rgba(99, 102, 241, 0.1))"
                    : "var(--bg-card, rgba(255,255,255,0.02))",
                  border: isSelected ? "1px solid var(--accent-primary)" : "1px solid var(--border-color)",
                  cursor: onSelectRace ? "pointer" : "default",
                  transition: "all 0.15s ease",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                    <span style={{ fontSize: "13px", fontWeight: 600, color: "var(--text-primary)" }}>
                      {race.race_name}
                    </span>
                    {race.race_date && (
                      <span
                        style={{
                          fontSize: "11px",
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
                      fontWeight: 600,
                      color: "var(--accent-primary)",
                      background: "var(--accent-primary-subtle, rgba(99, 102, 241, 0.12))",
                      padding: "2px 8px",
                      borderRadius: "10px",
                      display: "inline-flex",
                      alignItems: "center",
                      gap: "4px",
                    }}
                  >
                    <Users size={13} />
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
                          color: "var(--text-secondary)",
                          background: "var(--border-color)",
                          padding: "1px 7px",
                          borderRadius: "4px",
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
            paddingTop: "8px",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <span>{lang === "en" ? "Athletes without target race:" : "VĐV chưa có giải mục tiêu:"}</span>
          <span style={{ fontWeight: 600 }}>{athletesWithoutRace}</span>
        </div>
      )}
    </div>
  );
}
