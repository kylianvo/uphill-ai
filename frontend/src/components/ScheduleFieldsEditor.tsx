import { translations } from "../app/translations";

export interface ScheduleFieldsValue {
  days_per_week: number;
  long_run_day: string;
  preferred_days: string[];
  has_gym_access: boolean;
  use_treadmill: boolean;
  training_environment: "flat" | "hilly" | "mixed";
  double_session_days: string[];
}

interface ScheduleFieldsEditorProps {
  lang: string;
  t: (key: keyof typeof translations.en) => string;
  isMobile: boolean;
  value: ScheduleFieldsValue;
  onChange: (patch: Partial<ScheduleFieldsValue>) => void;
}

const FULL_DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];
const SHORT_DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
const SHORT_DAYS_VI = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"];

export function ScheduleFieldsEditor({ lang, t, isMobile, value, onChange }: ScheduleFieldsEditorProps) {
  return (
    <div style={{ marginBottom: "16px", padding: "14px", background: "rgba(255,255,255,0.15)", border: "1px solid var(--border-color)", borderRadius: "12px" }}>
      <label style={{ display: "block", fontSize: "12px", fontWeight: "700", marginBottom: "10px", color: "var(--text-secondary)", letterSpacing: "0.04em", textTransform: "uppercase" }}>
        {t("plan_schedule_prefs")}
      </label>

      <div style={{ display: "grid", gridTemplateColumns: isMobile ? "1fr" : "1fr 1fr", gap: "12px", marginBottom: "12px" }}>
        <div>
          <label style={{ display: "block", fontSize: "12px", fontWeight: "600", marginBottom: "6px", color: "var(--text-secondary)" }}>
            {t("plan_days_per_week")}
          </label>
          <div style={{ display: "flex", gap: "6px" }}>
            {[3, 4, 5, 6, 7].map(n => (
              <button key={n} type="button" onClick={() => onChange({ days_per_week: n })}
                style={{ flex: 1, padding: "7px 0", borderRadius: "8px", border: `1.5px solid ${value.days_per_week === n ? "var(--accent-primary)" : "var(--border-color)"}`, background: value.days_per_week === n ? "rgba(16,185,129,0.1)" : "rgba(255,255,255,0.3)", color: value.days_per_week === n ? "var(--accent-primary)" : "var(--text-primary)", fontWeight: "700", fontSize: "13px", cursor: "pointer" }}
              >{n}</button>
            ))}
          </div>
        </div>
        <div>
          <label style={{ display: "block", fontSize: "12px", fontWeight: "600", marginBottom: "6px", color: "var(--text-secondary)" }}>
            {t("plan_long_run_day")}
          </label>
          <select className="chat-input" style={{ borderRadius: "8px", width: "100%", height: "38px", padding: "0 8px", fontSize: "13px" }}
            value={value.long_run_day} onChange={e => onChange({ long_run_day: e.target.value })}>
            {FULL_DAYS.map(d => {
              const label = lang === "vi"
                ? d.replace("Monday", "Thứ Hai").replace("Tuesday", "Thứ Ba").replace("Wednesday", "Thứ Tư").replace("Thursday", "Thứ Năm").replace("Friday", "Thứ Sáu").replace("Saturday", "Thứ Bảy").replace("Sunday", "Chủ Nhật")
                : d;
              return (
                <option key={d} value={d}>{label}</option>
              );
            })}
          </select>
        </div>
      </div>

      <div>
        <label style={{ display: "block", fontSize: "12px", fontWeight: "600", marginBottom: "6px", color: "var(--text-secondary)" }}>
          {t("plan_preferred_days")}
        </label>
        <div style={{ display: "flex", gap: "5px", flexWrap: "wrap" }}>
          {SHORT_DAYS.map((short, i) => {
            const full = FULL_DAYS[i];
            const selected = value.preferred_days.includes(full);
            const label = lang === "vi" ? SHORT_DAYS_VI[i] : short;
            return (
              <button key={full} type="button"
                onClick={() => {
                  const next = selected ? value.preferred_days.filter((d) => d !== full) : [...value.preferred_days, full];
                  onChange({ preferred_days: next });
                }}
                style={{ padding: "5px 10px", borderRadius: "8px", border: `1.5px solid ${selected ? "var(--accent-primary)" : "var(--border-color)"}`, background: selected ? "rgba(16,185,129,0.1)" : "rgba(255,255,255,0.3)", color: selected ? "var(--accent-primary)" : "var(--text-secondary)", fontWeight: selected ? "700" : "500", fontSize: "12px", cursor: "pointer" }}
              >{label}</button>
            );
          })}
        </div>
        <p style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "5px", margin: "5px 0 0 0" }}>
          {lang === "en"
            ? "The AI will prioritise these days when building your weekly schedule."
            : "Trí tuệ nhân tạo (AI) sẽ ưu tiên xếp lịch tập vào các ngày này."}
        </p>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: isMobile ? "1fr" : "1fr 1fr", gap: "12px", marginTop: "12px" }}>
        <label style={{ display: "flex", alignItems: "center", gap: "8px", cursor: "pointer", fontSize: "13px", color: "var(--text-primary)" }}>
          <input type="checkbox" checked={value.has_gym_access}
            onChange={e => onChange({ has_gym_access: e.target.checked })}
            style={{ width: "16px", height: "16px", accentColor: "var(--accent-primary)" }} />
          {t("plan_gym_access")}
        </label>
        <label style={{ display: "flex", alignItems: "center", gap: "8px", cursor: "pointer", fontSize: "13px", color: "var(--text-primary)" }}>
          <input type="checkbox" checked={value.use_treadmill}
            onChange={e => onChange({ use_treadmill: e.target.checked })}
            style={{ width: "16px", height: "16px", accentColor: "var(--accent-primary)" }} />
          {t("plan_use_treadmill")}
        </label>
      </div>

      <div style={{ marginTop: "12px" }}>
        <label style={{ display: "block", fontSize: "12px", fontWeight: "600", marginBottom: "6px", color: "var(--text-secondary)" }}>
          {t("plan_training_environment")}
        </label>
        <div style={{ display: "flex", gap: "6px" }}>
          {(["flat", "hilly", "mixed"] as const).map(env => {
            const selected = value.training_environment === env;
            const envKey = ("plan_training_environment_" + env) as keyof typeof translations.en;
            return (
              <button key={env} type="button" onClick={() => onChange({ training_environment: env })}
                style={{ flex: 1, padding: "7px 0", borderRadius: "8px", border: `1.5px solid ${selected ? "var(--accent-primary)" : "var(--border-color)"}`, background: selected ? "rgba(16,185,129,0.1)" : "rgba(255,255,255,0.3)", color: selected ? "var(--accent-primary)" : "var(--text-primary)", fontWeight: selected ? "700" : "500", fontSize: "13px", cursor: "pointer" }}
              >{t(envKey)}</button>
            );
          })}
        </div>
        <p style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "5px", margin: "5px 0 0 0" }}>
          {t("plan_training_environment_help")}
        </p>
      </div>

      <div style={{ marginTop: "12px" }}>
        <label style={{ display: "block", fontSize: "12px", fontWeight: "600", marginBottom: "6px", color: "var(--text-secondary)" }}>
          {t("plan_double_session_days")}
        </label>
        <div style={{ display: "flex", gap: "5px", flexWrap: "wrap" }}>
          {SHORT_DAYS.map((short, i) => {
            const full = FULL_DAYS[i];
            if (!value.preferred_days.includes(full)) return null;
            const selected = value.double_session_days.includes(full);
            const disabled = !selected && value.double_session_days.length >= 2;
            const label = lang === "vi" ? SHORT_DAYS_VI[i] : short;
            return (
              <button key={full} type="button" disabled={disabled}
                onClick={() => {
                  const next = selected
                    ? value.double_session_days.filter((d) => d !== full)
                    : [...value.double_session_days, full];
                  onChange({ double_session_days: next });
                }}
                style={{ padding: "5px 10px", borderRadius: "8px", border: `1.5px solid ${selected ? "var(--accent-primary)" : "var(--border-color)"}`, background: selected ? "rgba(16,185,129,0.1)" : "rgba(255,255,255,0.3)", color: selected ? "var(--accent-primary)" : disabled ? "var(--text-muted)" : "var(--text-secondary)", fontWeight: selected ? "700" : "500", fontSize: "12px", cursor: disabled ? "not-allowed" : "pointer", opacity: disabled ? 0.5 : 1 }}
              >{label}</button>
            );
          })}
        </div>
        <p style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "5px", margin: "5px 0 0 0" }}>
          {t("plan_double_session_help")}
        </p>
      </div>
    </div>
  );
}
