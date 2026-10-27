import { useEffect, useId, useState, type CSSProperties } from "react";
import { getApiBaseUrl } from "../lib/apiUrlOverride";
import type { LongDayFormat, TrainingMountain } from "../types";
import { translations } from "../app/translations";
import styles from "./TrainingVenueFields.module.css";

// Where the athlete can actually train: weekdays with hill/trail access (e.g. weekend
// trips from a flat city), stairs, and the treadmill's top incline. The backend turns
// these into a venue for every session type (services/training_venues.py).
export interface TrainingVenueValue {
  mountain_days: string[];
  training_mountain?: string | null;
  mountain_min_minutes?: number | null;
  long_day_format?: LongDayFormat | null;
  stair_access: boolean;
  treadmill_max_incline: number;
}

interface TrainingVenueFieldsProps {
  lang: string;
  t: (key: keyof typeof translations.en) => string;
  value: TrainingVenueValue;
  // The incline picker only makes sense for an athlete who has a treadmill.
  useTreadmill: boolean;
  onTreadmillChange?: (enabled: boolean) => void;
  onChange: (patch: Partial<TrainingVenueValue>) => void;
  // The course's climb in m D+/km, when known: a steep course with no place to train climbing gets a prompt.
  courseSteepness?: number;
  // The long run belongs on a trail day: picking trail days moves it there (mirrors training_venues.long_run_day).
  longRunDay?: string;
  onLongRunDayChange?: (day: string) => void;
  // Where the plan saves it (create, onboarding, next block): one 6-7 h mountain day or a back-to-back weekend.
  showLongDayFormat?: boolean;
}

export const STEEP_COURSE_M_PER_KM = 25;
const VENUE_SHARE = 0.6;

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

// The trail day nearest the chosen long-run day, or the chosen day when it already is one.
export function trailLongRunDay(chosen: string, trailDays: string[]): string {
  if (!trailDays.length || trailDays.includes(chosen)) return chosen;
  const i = FULL_DAYS.indexOf(chosen);
  const gap = (d: string) => { const g = Math.abs(FULL_DAYS.indexOf(d) - i); return Math.min(g, 7 - g); };
  return i < 0 ? trailDays[trailDays.length - 1] : trailDays.reduce((a, b) => (gap(b) < gap(a) ? b : a));
}

const VI_DAYS = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"];
export const dayLabel = (day: string, lang: string) => (lang === "vi" ? VI_DAYS[FULL_DAYS.indexOf(day)] ?? day : day);

// Long-run day picker that matches training_venues.long_run_day: with trail days it only offers
// those (one trail day: a fixed row), and shows the trail day the plan will actually use.
export function LongRunDaySelect({ lang, t, value, trailDays, onChange, className, style }: {
  lang: string;
  t: (key: keyof typeof translations.en) => string;
  value: string;
  trailDays: string[];
  onChange: (day: string) => void;
  className?: string;
  style?: CSSProperties;
}) {
  const choices = trailDays.length ? FULL_DAYS.filter(d => trailDays.includes(d)) : FULL_DAYS;
  const shown = trailLongRunDay(value, trailDays);
  return <>
    {choices.length === 1
      ? <div data-testid="long-run-fixed" style={{ fontWeight: 600, fontSize: "13px", padding: "8px 0" }}>{dayLabel(shown, lang)}</div>
      : <select className={className} style={style} value={shown} onChange={e => onChange(e.target.value)}>
        {choices.map(d => <option key={d} value={d}>{dayLabel(d, lang)}</option>)}
      </select>}
    {trailDays.length > 0 && <div style={{ fontSize: "11px", marginTop: "6px", color: "var(--text-secondary)" }}>{t("plan_long_run_on_trail_day")}</div>}
  </>;
}

const SHORT_DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
const SHORT_DAYS_VI = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"];
const INCLINES = [15, 20, 25];

export function TrainingVenueFields({ lang, t, value, useTreadmill, onTreadmillChange, onChange, courseSteepness, longRunDay, onLongRunDayChange, showLongDayFormat }: TrainingVenueFieldsProps) {
  const id = useId();
  const [mountains, setMountains] = useState<TrainingMountain[]>([]);
  const [loadError, setLoadError] = useState(false);
  const [attempt, setAttempt] = useState(0);
  const [access, setAccess] = useState<boolean | null>(null);
  const [choseOther, setChoseOther] = useState(false);
  const [showDuration, setShowDuration] = useState(false);
  const hasSavedTrail = !!value.training_mountain || value.mountain_days.length > 0;
  const hasAccess = access ?? (hasSavedTrail ? true : null);
  const hasLocation = !!value.training_mountain || value.mountain_days.length > 0 || choseOther;
  const mountain = mountains.find(m => m.key === value.training_mountain);
  const minimum = value.mountain_min_minutes || mountain?.default_min_minutes;
  const needsClimbVenue = (courseSteepness ?? 0) >= STEEP_COURSE_M_PER_KM && !hasSavedTrail && !value.stair_access && !useTreadmill;
  // A mountain under 60% of the course's steepness can't rehearse it (backend goal_feasibility.VENUE_SHARE).
  const venueTooGentle = !!mountain && (courseSteepness ?? 0) >= STEEP_COURSE_M_PER_KM
    && mountain.climb_rate < VENUE_SHARE * (courseSteepness ?? 0) && !value.stair_access && !useTreadmill;
  useEffect(() => {
    let active = true;
    fetch(`${getApiBaseUrl()}/api/training-mountains`)
      .then(response => { if (!response.ok) throw new Error(); return response.json(); })
      .then(rows => { if (active) { setMountains(rows); setLoadError(false); } })
      .catch(() => { if (active) setLoadError(true); });
    return () => { active = false; };
  }, [attempt]);
  return (
    <section className={styles.section} data-testid="training-venue-fields" aria-labelledby={`${id}-title`}>
      <h3 id={`${id}-title`} className={styles.heading}>{t("plan_trail_title")}</h3>
      <ol className={styles.steps}>
        <li>
          <div role="radiogroup" aria-labelledby={`${id}-access`}>
            <span id={`${id}-access`} className={styles.question}>{t("plan_trail_access")}</span>
            <div className={styles.choices}>
              {[true, false].map(enabled => (
                <label key={String(enabled)} className={styles.choice}>
                  <input type="radio" name={`${id}-access`} checked={hasAccess === enabled}
                    onChange={() => {
                      setAccess(enabled);
                      if (!enabled) {
                        setChoseOther(false); setShowDuration(false);
                        onChange({ training_mountain: null, mountain_days: [], mountain_min_minutes: null });
                      }
                    }} />
                  {t(enabled ? "plan_trail_yes" : "plan_trail_not_now")}
                </label>
              ))}
            </div>
          </div>
        </li>
        {hasAccess && <li>
          <label htmlFor={`${id}-mountain`} className={styles.question}>{t("plan_trail_where")}</label>
          <select id={`${id}-mountain`} className={styles.input}
            value={value.training_mountain ?? (hasLocation ? "other" : "")} onChange={e => {
              const selected = mountains.find(m => m.key === e.target.value);
              setChoseOther(e.target.value === "other");
              onChange({ training_mountain: selected?.key ?? null, mountain_min_minutes: selected?.default_min_minutes ?? null });
            }}>
            <option value="" disabled>{t("plan_trail_choose_place")}</option>
            {value.training_mountain && !mountain && <option value={value.training_mountain}>{t("plan_trail_saved_place")}</option>}
            {mountains.map(m => <option key={m.key} value={m.key}>{lang === "vi" ? m.name_vi : m.name_en}</option>)}
            <option value="other">{t("plan_mountain_other")}</option>
          </select>
          {loadError && <div role="alert">
            <p className={styles.help}>{t("plan_mountains_unavailable")}</p>
            <button type="button" className={styles.quiet} onClick={() => setAttempt(n => n + 1)}>{t("plan_trail_retry")}</button>
          </div>}
        </li>}
        {hasAccess && hasLocation && <li>
          <div>
            <span id={`${id}-days`} className={styles.question}>{t("plan_mountain_days")}</span>
            <div className={styles.choices} role="group" aria-labelledby={`${id}-days`}>
              {SHORT_DAYS.map((short, i) => {
                const full = FULL_DAYS[i];
                const selected = value.mountain_days.includes(full);
                return <button key={full} type="button" className={styles.choice} aria-pressed={selected}
                  onClick={() => {
                    const next = selected ? value.mountain_days.filter(d => d !== full) : [...value.mountain_days, full];
                    const days = FULL_DAYS.filter(d => next.includes(d));
                    onChange({ mountain_days: days });
                    if (longRunDay && onLongRunDayChange) {
                      const moved = trailLongRunDay(longRunDay, days);
                      if (moved !== longRunDay) onLongRunDayChange(moved);
                    }
                  }}>{lang === "vi" ? SHORT_DAYS_VI[i] : short}</button>;
              })}
            </div>
            <p className={styles.help}>{t("plan_mountain_days_help")}</p>
            {longRunDay && value.mountain_days.includes(longRunDay) && (
              <p className={styles.help}>{t("plan_long_run_on_this_trail_day").replace("{day}", dayLabel(longRunDay, lang))}</p>
            )}
          </div>
        </li>}
      </ol>
      {hasAccess && hasLocation && <div className={styles.duration}>
        <strong>{t("plan_trail_coach_duration")}</strong>
        {minimum != null && <p className={styles.help}>{t("plan_trail_min_summary").replace("{minutes}", String(minimum))}</p>}
        <button type="button" className={styles.quiet} aria-expanded={showDuration} aria-controls={`${id}-duration`}
          onClick={() => setShowDuration(!showDuration)}>{t("plan_trail_duration_settings")}</button>
        {showDuration && <div id={`${id}-duration`} className={styles.override}>
          <label htmlFor={`${id}-minimum`} className={styles.question}>{t("plan_mountain_min_minutes")}</label>
          <input id={`${id}-minimum`} aria-describedby={`${id}-min-help`} className={styles.input} type="number" min="0" step="1"
            value={value.mountain_min_minutes ?? ""}
            onChange={e => onChange({ mountain_min_minutes: e.target.value === "" ? null : Number(e.target.value) })} />
          <p id={`${id}-min-help`} className={styles.help}>{t("plan_mountain_min_minutes_help")}</p>
          <button type="button" className={styles.quiet} onClick={() => {
            onChange({ mountain_min_minutes: mountain?.default_min_minutes ?? null }); setShowDuration(false);
          }}>{t("plan_trail_duration_reset")}</button>
        </div>}
        {showLongDayFormat && <div className={styles.override} role="radiogroup" aria-labelledby={`${id}-long-day`}>
          <span id={`${id}-long-day`} className={styles.question}>{t("plan_long_day_format")}</span>
          <div className={styles.choices}>
            {(["single", "back_to_back"] as const).map(format => (
              <label key={format} className={styles.choice}>
                <input type="radio" name={`${id}-long-day`}
                  checked={(value.long_day_format ?? "single") === format}
                  onChange={() => onChange({ long_day_format: format })} />
                {t(format === "single" ? "plan_long_day_single" : "plan_long_day_b2b")}
              </label>
            ))}
          </div>
          <p className={styles.help}>{t("plan_long_day_help")}</p>
        </div>}
      </div>}
      <div className={styles.alternatives}>
        <h3 className={styles.heading}>{t("plan_trail_alternatives")}</h3>
        {needsClimbVenue && <p role="status" data-testid="climb-venue-needed" className={styles.help}>
          {t("plan_climb_venue_needed").replace("{gradient}", String(Math.round(courseSteepness ?? 0)))}
        </p>}
        {venueTooGentle && mountain && <p role="status" data-testid="venue-too-gentle" className={styles.help}>
          {t("plan_venue_too_gentle")
            .replace("{mountain}", lang === "vi" ? mountain.name_vi : mountain.name_en)
            .replace("{venue}", String(Math.round(mountain.climb_rate)))
            .replace("{course}", String(Math.round(courseSteepness ?? 0)))}
        </p>}
        <label className={styles.toggle}>
          <input type="checkbox" checked={value.stair_access} onChange={e => onChange({ stair_access: e.target.checked })} />
          {t("plan_stair_access")}
        </label>
        {onTreadmillChange && <label className={styles.toggle}>
          <input type="checkbox" checked={useTreadmill} onChange={e => onTreadmillChange(e.target.checked)} />
          {t("plan_use_treadmill")}
        </label>}
        {useTreadmill && <div className={styles.incline}>
          <span id={`${id}-incline`} className={styles.question}>{t("plan_treadmill_max_incline")}</span>
          <div className={styles.choices} role="group" aria-labelledby={`${id}-incline`}>
            {INCLINES.map(incline => <button key={incline} type="button" className={styles.choice}
              aria-pressed={value.treadmill_max_incline === incline || (incline === 25 && value.treadmill_max_incline > 25)}
              onClick={() => onChange({ treadmill_max_incline: incline })}>{incline === 25 ? "25%+" : `${incline}%`}</button>)}
          </div>
          <p className={styles.help}>{t("plan_treadmill_max_incline_help")}</p>
        </div>}
      </div>
    </section>
  );
}
