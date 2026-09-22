import { ToolResultEvent, ToolCallEvent } from "../lib/coachChatStream";

const TOOL_LABELS_EN: Record<string, string> = {
  get_week: "Get Week",
  pace_strategy: "Pace Strategy",
  week_review: "Week Review",
  kb_search: "Knowledge Search",
};
const TOOL_LABELS_VI: Record<string, string> = {
  get_week: "Xem lịch tuần",
  pace_strategy: "Chiến lược Pace",
  week_review: "Đánh giá tuần",
  kb_search: "Tra cứu kiến thức",
};

export default function ToolExecutionPill({
  call,
  result,
  lang,
}: {
  call: ToolCallEvent;
  result: ToolResultEvent | undefined;
  lang: string;
}) {
  const labels = lang === "vi" ? TOOL_LABELS_VI : TOOL_LABELS_EN;
  const label = labels[call.name] || call.name;
  const running = !result;
  const failed = result?.status === "error";

  return (
    <div
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "6px",
        padding: "4px 10px",
        borderRadius: "999px",
        fontSize: "12px",
        fontWeight: 500,
        backgroundColor: failed ? "rgba(220, 38, 38, 0.08)" : "rgba(0, 0, 0, 0.05)",
        color: failed ? "#dc2626" : "var(--text-secondary)",
        marginBottom: "6px",
      }}
    >
      {running && <span aria-hidden>●</span>}
      {label}
      {failed && " — failed"}
    </div>
  );
}
