/* eslint-disable @typescript-eslint/no-explicit-any */
import { ToolResultEvent } from "../lib/coachChatStream";
import { translations } from "../app/translations";
import WorkoutCard from "./WorkoutCard";
import WeeklyReview from "./WeeklyReview";
import { KnowledgeCard } from "./KnowledgeCard";
import { ProfileChart, PacingSplitsTable } from "./PacingSplitsView";
import { computeWorkoutDate } from "../utils/planDate";

interface RichCardRendererProps {
  result: ToolResultEvent;
  lang: string;
  onOpenPaceStrategy: (payload: {
    race_name: string;
    distance_km?: number;
    distance_label?: string;
    target_time_mins?: number;
  }) => void;
  isMobile?: boolean;
}

const cardWrapStyle: React.CSSProperties = {
  padding: "12px",
  borderRadius: "12px",
  backgroundColor: "rgba(255, 255, 255, 0.6)",
  border: "1px solid rgba(0, 0, 0, 0.08)",
  marginTop: "6px",
  marginBottom: "6px",
  maxWidth: "100%",
  overflowX: "auto",
};
const cardHeaderStyle: React.CSSProperties = { fontWeight: 600, marginBottom: "6px" };

function translate(lang: string, key: keyof typeof translations.en): string {
  return translations[lang as keyof typeof translations]?.[key] || translations.en[key] || key;
}

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

function WeekScheduleCard({ data, lang, isMobile }: { data: any; lang: string; isMobile: boolean }) {
  const workouts = data.workouts || [];
  const getWorkoutDate = (wo: any) => {
    const d = computeWorkoutDate({ start_date: data.plan_start_date, race_date: data.race_date }, workouts, wo);
    if (!d) return "";
    return d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
  };

  return (
    <div style={cardWrapStyle}>
      <div style={cardHeaderStyle}>
        {translate(lang, "chat_card_week")} {data.week_number}
        {" · "}
        {data.total_distance_km} km · +{data.total_elevation_gain_m} m D+
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
        {workouts.map((w: any) => (
          <WorkoutCard
            key={w.id}
            wo={w}
            lang={lang}
            isMobile={isMobile}
            getWorkoutDate={getWorkoutDate}
            readOnly
          />
        ))}
      </div>
    </div>
  );
}

function WeekReviewCard({ data, lang }: { data: any; lang: string }) {
  return (
    <div style={cardWrapStyle}>
      {data.week_label && <div style={cardHeaderStyle}>{data.week_label}</div>}
      <WeeklyReview data={data} lang={lang as "en" | "vi"} />
    </div>
  );
}

function PacingSplitsCard({
  data,
  onOpenPaceStrategy,
  lang,
}: {
  data: any;
  onOpenPaceStrategy: RichCardRendererProps["onOpenPaceStrategy"];
  lang: string;
}) {
  const splits = data.splits || [];

  return (
    <div style={cardWrapStyle}>
      <div style={cardHeaderStyle}>{data.race_name}</div>
      <div style={{ fontSize: "13px", color: "var(--text-secondary)", marginBottom: "10px" }}>
        {data.distance_label ? `${data.distance_label} · ` : ""}
        {data.total_distance_km} km · +{data.total_elevation_m} m D+
        {data.target_time_formatted ? ` · ${data.target_time_formatted}` : ""}
      </div>
      {splits.length > 1 && (
        <>
          <ProfileChart paced={splits} lang={lang as "en" | "vi"} />
          <div style={{ marginTop: "12px" }}>
            <PacingSplitsTable checkpoints={splits} lang={lang as "en" | "vi"} />
          </div>
        </>
      )}
      <button
        onClick={() =>
          onOpenPaceStrategy({
            race_name: data.race_name,
            distance_km: data.total_distance_km,
            distance_label: data.distance_label,
          })
        }
        style={buttonStyle}
      >
        {translate(lang, "chat_open_in_pace_strategy")}
      </button>
    </div>
  );
}

function KnowledgeCitationsCard({ data }: { data: any }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "8px", marginTop: "6px", marginBottom: "6px" }}>
      {(data.citations || []).map((c: any, i: number) => (
        <KnowledgeCard key={i} card={c} />
      ))}
    </div>
  );
}

export default function RichCardRenderer({ result, lang, onOpenPaceStrategy, isMobile }: RichCardRendererProps) {
  if (result.status !== "success" || !result.card_data) return null;

  switch (result.card_type) {
    case "week_schedule":
      return <WeekScheduleCard data={result.card_data} lang={lang} isMobile={!!isMobile} />;
    case "week_review":
      return <WeekReviewCard data={result.card_data} lang={lang} />;
    case "pacing_splits":
      return <PacingSplitsCard data={result.card_data} onOpenPaceStrategy={onOpenPaceStrategy} lang={lang} />;
    case "knowledge_citations":
      return <KnowledgeCitationsCard data={result.card_data} />;
    default:
      return null;
  }
}
