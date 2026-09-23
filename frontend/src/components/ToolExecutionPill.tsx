import { ToolResultEvent, ToolCallEvent } from "../lib/coachChatStream";
import { translations } from "../app/translations";

const TOOL_NAME_TO_KEY: Record<string, keyof typeof translations.en> = {
  get_week: "chat_tool_label_get_week",
  pace_strategy: "chat_tool_label_pace_strategy",
  week_review: "chat_tool_label_week_review",
  kb_search: "chat_tool_label_kb_search",
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
  const t = (key: keyof typeof translations.en) =>
    translations[lang as keyof typeof translations]?.[key] || translations.en[key] || key;

  const translationKey = TOOL_NAME_TO_KEY[call.name];
  const label = translationKey ? t(translationKey) : call.name;
  const running = !result;
  const failed = result?.status === "error";
  const failedText = ` — ${t("chat_tool_failed")}`;

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
      {failed && failedText}
    </div>
  );
}
