/* eslint-disable @typescript-eslint/no-explicit-any */
import { ToolResultEvent } from "../lib/coachChatStream";
import { translations } from "../app/translations";

interface RichCardRendererProps {
  result: ToolResultEvent;
  lang: string;
  onOpenPaceStrategy: (payload: { race_name: string; distance_km?: number; target_time_mins?: number }) => void;
}

function WeekWorkoutCard({ data }: { data: any }) {
  return (
    <div style={cardStyle}>
      <div style={cardHeaderStyle}>
        Week {data.week_number} — {data.total_distance_km} km, {data.total_elevation_gain_m} m D+
      </div>
      {data.workouts.map((w: any, i: number) => (
        <div key={i} style={{ padding: "6px 0", borderTop: i > 0 ? "1px solid rgba(0,0,0,0.06)" : "none" }}>
          <div>
            {w.day} — <strong>{w.name}</strong> {w.distance_km ? `(${w.distance_km} km)` : ""}
          </div>
          {w.description && <div style={{ fontSize: "13px", color: "var(--text-secondary)" }}>{w.description}</div>}
        </div>
      ))}
    </div>
  );
}

function PacingSplitCard({ data, onOpenPaceStrategy, lang }: { data: any; onOpenPaceStrategy: RichCardRendererProps["onOpenPaceStrategy"]; lang: string }) {
  const t = (key: keyof typeof translations.en) =>
    translations[lang as keyof typeof translations]?.[key] || translations.en[key] || key;

  return (
    <div style={cardStyle}>
      <div style={cardHeaderStyle}>{data.race_name}</div>
      <div style={{ fontSize: "13px", color: "var(--text-secondary)" }}>
        {data.total_distance_km} km · {data.total_elevation_m} m D+ · Target {data.target_time_formatted}
      </div>
      {(data.splits || []).slice(0, 5).map((s: any, i: number) => (
        <div key={i} style={{ padding: "4px 0", fontSize: "13px" }}>
          {s.name} — {s.distance_km ?? s.distance_meters} km @ {s.target_pace}
        </div>
      ))}
      <button
        onClick={() =>
          onOpenPaceStrategy({
            race_name: data.race_name,
            distance_km: data.total_distance_km,
          })
        }
        style={buttonStyle}
      >
        {t("chat_open_in_pace_strategy")}
      </button>
    </div>
  );
}

function KnowledgeCard({ data }: { data: any }) {
  return (
    <div style={cardStyle}>
      {(data.citations || []).map((c: any, i: number) => (
        <div key={i} style={{ padding: "6px 0", borderTop: i > 0 ? "1px solid rgba(0,0,0,0.06)" : "none" }}>
          <div style={{ fontWeight: 500 }}>
            {c.book}
            {c.chapter ? ` — ${c.chapter}` : ""}
          </div>
          <div style={{ fontSize: "13px", color: "var(--text-secondary)" }}>{c.quote}</div>
        </div>
      ))}
    </div>
  );
}

const cardStyle: React.CSSProperties = {
  padding: "12px",
  borderRadius: "12px",
  backgroundColor: "rgba(255, 255, 255, 0.6)",
  border: "1px solid rgba(0, 0, 0, 0.08)",
  marginTop: "6px",
  marginBottom: "6px",
};
const cardHeaderStyle: React.CSSProperties = { fontWeight: 600, marginBottom: "4px" };
const buttonStyle: React.CSSProperties = {
  marginTop: "8px",
  padding: "6px 12px",
  borderRadius: "8px",
  border: "none",
  backgroundColor: "var(--accent, #2563eb)",
  color: "white",
  fontSize: "13px",
  cursor: "pointer",
};

export default function RichCardRenderer({ result, lang, onOpenPaceStrategy }: RichCardRendererProps) {
  if (result.status !== "success" || !result.card_data) return null;

  switch (result.card_type) {
    case "week_schedule":
      return <WeekWorkoutCard data={result.card_data} />;
    case "pacing_splits":
      return <PacingSplitCard data={result.card_data} onOpenPaceStrategy={onOpenPaceStrategy} lang={lang} />;
    case "week_review":
      return <WeekWorkoutCard data={{ week_number: result.card_data.week_label, total_distance_km: result.card_data.completed_km, total_elevation_gain_m: result.card_data.completed_vert_m, workouts: [] }} />;
    case "knowledge_citations":
      return <KnowledgeCard data={result.card_data} />;
    default:
      return null;
  }
}
