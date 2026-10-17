import { useEffect, useState } from "react";
import { getApiBaseUrl } from "../lib/apiUrlOverride";
import type { TrainingMountain } from "../types";
import { translations } from "../app/translations";

// Where the athlete can actually train: weekdays with hill/trail access (e.g. weekend
// trips from a flat city), stairs, and the treadmill's top incline. The backend turns
// these into a venue for every session type (services/training_venues.py).
export interface TrainingVenueValue {
  mountain_days: string[];
  training_mountain?: string | null;
  mountain_min_minutes?: number | null;
  stair_access: boolean;
  treadmill_max_incline: number;
}

interface TrainingVenueFieldsProps {
  lang: string;
  t: (key: keyof typeof translations.en) => string;
  value: TrainingVenueValue;
  // The incline picker only makes sense for an athlete who has a treadmill.
  useTreadmill: boolean;
  onChange: (patch: Partial<TrainingVenueValue>) => void;
}

const FULL_DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

// plans.mountain_days is stored as JSON text ('["Saturday","Sunday"]'); accept that,
// an already-parsed array, or nothing.
export function parseDayList(value: unknown): string[] {
  let parsed: unknown = value;
  if (typeof value === "string") {
    try { parsed = JSON.parse(value); } catch { return []; }
  }
  if (!Array.isArray(parsed)) return [];
  const days: unknown[] = parsed;
  return FULL_DAYS.filter((d) => days.includes(d));
}

const SHORT_DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
const SHORT_DAYS_VI = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"];
const INCLINES = [15, 20, 25];

const labelStyle = { display: "block", fontSize: "12px", fontWeight: "600", marginBottom: "6px", color: "var(--text-secondary)" } as const;
const helpStyle = { fontSize: "11px", color: "var(--text-muted)", margin: "5px 0 0 0" } as const;

function chipStyle(selected: boolean) {
  return {
    padding: "5px 10px",
    borderRadius: "8px",
    border: `1.5px solid ${selected ? "var(--accent-primary)" : "var(--border-color)"}`,
    background: selected ? "rgba(16,185,129,0.1)" : "rgba(255,255,255,0.3)",
    color: selected ? "var(--accent-primary)" : "var(--text-secondary)",
    fontWeight: selected ? "700" : "500",
    fontSize: "12px",
    cursor: "pointer",
  } as const;
}

export function TrainingVenueFields({ lang, t, value, useTreadmill, onChange }: TrainingVenueFieldsProps) {
  const [mountains, setMountains] = useState<TrainingMountain[]>([]);
  const [loadError, setLoadError] = useState(false);
  useEffect(() => {
    let active = true;
    fetch(`${getApiBaseUrl()}/api/training-mountains`)
      .then(response => { if (!response.ok) throw new Error(); return response.json(); })
      .then(rows => { if (active) setMountains(rows); })
      .catch(() => { if (active) setLoadError(true); });
    return () => { active = false; };
  }, []);
  return (
    <div data-testid="training-venue-fields">
      <div style={{ marginTop: "12px" }}>
        <label htmlFor="training-mountain" style={labelStyle}>{t("plan_training_mountain")}</label>
        <select id="training-mountain" className="chat-input" style={{ width: "100%", padding: "8px" }}
          disabled={mountains.length === 0} value={value.training_mountain ?? ""} onChange={e => {
            const mountain = mountains.find(m => m.key === e.target.value);
            onChange({ training_mountain: mountain?.key ?? null, mountain_min_minutes: mountain?.default_min_minutes ?? null });
          }}>
          <option value="">{t("plan_mountain_other")}</option>
          {mountains.map(m => <option key={m.key} value={m.key}>{lang === "vi" ? m.name_vi : m.name_en} · {m.climb_rate} m D+/km</option>)}
        </select>
        {loadError && <p role="alert" style={helpStyle}>{t("plan_mountains_unavailable")}</p>}
      </div>
      <div style={{ marginTop: "12px" }}>
        <label htmlFor="mountain-min-minutes" style={labelStyle}>{t("plan_mountain_min_minutes")}</label>
        <input id="mountain-min-minutes" aria-describedby="mountain-min-help" className="chat-input" type="number" min="0" step="1"
          value={value.mountain_min_minutes ?? ""}
          onChange={e => onChange({ mountain_min_minutes: e.target.value === "" ? null : Number(e.target.value) })} />
        <p id="mountain-min-help" style={helpStyle}>{t("plan_mountain_min_minutes_help")}</p>
      </div>
      <div style={{ marginTop: "12px" }}>
        <label style={labelStyle}>{t("plan_mountain_days")}</label>
        <div style={{ display: "flex", gap: "5px", flexWrap: "wrap" }}>
          {SHORT_DAYS.map((short, i) => {
            const full = FULL_DAYS[i];
            const selected = value.mountain_days.includes(full);
            return (
              <button key={full} type="button" aria-pressed={selected}
                onClick={() => {
                  const next = selected ? value.mountain_days.filter((d) => d !== full) : [...value.mountain_days, full];
                  onChange({ mountain_days: FULL_DAYS.filter((d) => next.includes(d)) });
                }}
                style={chipStyle(selected)}
              >{lang === "vi" ? SHORT_DAYS_VI[i] : short}</button>
            );
          })}
        </div>
        <p style={helpStyle}>{t("plan_mountain_days_help")}</p>
      </div>

      <label style={{ display: "flex", alignItems: "center", gap: "8px", cursor: "pointer", fontSize: "13px", color: "var(--text-primary)", marginTop: "12px" }}>
        <input type="checkbox" checked={value.stair_access}
          onChange={(e) => onChange({ stair_access: e.target.checked })}
          style={{ width: "16px", height: "16px", accentColor: "var(--accent-primary)" }} />
        {t("plan_stair_access")}
      </label>

      {useTreadmill && (
        <div style={{ marginTop: "12px" }}>
          <label style={labelStyle}>{t("plan_treadmill_max_incline")}</label>
          <div style={{ display: "flex", gap: "6px" }}>
            {INCLINES.map((incline) => {
              const selected = value.treadmill_max_incline === incline
                || (incline === 25 && value.treadmill_max_incline > 25);
              return (
                <button key={incline} type="button" aria-pressed={selected}
                  onClick={() => onChange({ treadmill_max_incline: incline })}
                  style={{ ...chipStyle(selected), flex: 1, fontSize: "13px", padding: "7px 0" }}
                >{incline === 25 ? "25%+" : `${incline}%`}</button>
              );
            })}
          </div>
          <p style={helpStyle}>{t("plan_treadmill_max_incline_help")}</p>
        </div>
      )}
    </div>
  );
}
