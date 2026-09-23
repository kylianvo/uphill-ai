/* eslint-disable @typescript-eslint/no-explicit-any */
import React from "react";
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

// I2: a malformed tool_calls_json row (e.g. written before the card_data
// shape changed) must not crash the whole app on render -- catch it here and
// render nothing instead of blanking the page.
class CardErrorBoundary extends React.Component<{ children: React.ReactNode }, { hasError: boolean }> {
  constructor(props: { children: React.ReactNode }) {
    super(props);
    this.state = { hasError: false };
  }
  static getDerivedStateFromError() {
    return { hasError: true };
  }
  componentDidCatch(error: unknown) {
    console.error("RichCardRenderer: tool card failed to render", error);
  }
  render() {
    if (this.state.hasError) return null;
    return this.props.children;
  }
}

// Minimal shape guards per card_type: render nothing rather than throwing
// when a row has an unexpected shape.
function isValidWeekSchedule(data: any): boolean {
  return Array.isArray(data?.workouts) && data.workouts.every((w: any) => typeof w?.day_of_week === "string");
}
function isValidWeekReview(data: any): boolean {
  return (
    !!data &&
    typeof data.planned === "object" &&
    data.planned !== null &&
    typeof data.actual === "object" &&
    data.actual !== null &&
    Array.isArray(data.per_workout)
  );
}
function isValidPacingSplits(data: any): boolean {
  return Array.isArray(data?.splits);
}
function isValidKnowledgeCitations(data: any): boolean {
  return Array.isArray(data?.citations);
}

function buildWeekReviewHeader(data: any, lang: string): string | null {
  const { weeks_ago, target_week, week_label } = data;
  if (weeks_ago != null && target_week != null) {
    if (weeks_ago === 0) {
      return translate(lang, "chat_week_review_current").replace("{week}", String(target_week));
    }
    const key = weeks_ago === 1 ? "chat_week_review_weeks_ago_one" : "chat_week_review_weeks_ago_other";
    return translate(lang, key).replace("{n}", String(weeks_ago)).replace("{week}", String(target_week));
  }
  return week_label || null;
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
  const header = buildWeekReviewHeader(data, lang);
  return (
    <div style={cardWrapStyle}>
      {header && <div style={cardHeaderStyle}>{header}</div>}
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
        {data.total_distance_km} km
        {data.total_elevation_m != null ? ` · +${data.total_elevation_m} m D+` : ""}
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
            target_time_mins: data.target_time_hours != null ? data.target_time_hours * 60 : undefined,
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

function RichCard({ result, lang, onOpenPaceStrategy, isMobile }: RichCardRendererProps) {
  if (result.status !== "success" || !result.card_data) return null;
  const data = result.card_data;

  switch (result.card_type) {
    case "week_schedule":
      if (!isValidWeekSchedule(data)) return null;
      return <WeekScheduleCard data={data} lang={lang} isMobile={!!isMobile} />;
    case "week_review":
      if (!isValidWeekReview(data)) return null;
      return <WeekReviewCard data={data} lang={lang} />;
    case "pacing_splits":
      if (!isValidPacingSplits(data)) return null;
      return <PacingSplitsCard data={data} onOpenPaceStrategy={onOpenPaceStrategy} lang={lang} />;
    case "knowledge_citations":
      if (!isValidKnowledgeCitations(data)) return null;
      return <KnowledgeCitationsCard data={data} />;
    default:
      return null;
  }
}

export default function RichCardRenderer(props: RichCardRendererProps) {
  return (
    <CardErrorBoundary>
      <RichCard {...props} />
    </CardErrorBoundary>
  );
}
