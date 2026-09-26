"use client";

import React from "react";
import { Calculator, CalendarCheck, ChartLineUp, Flag, Trophy, User, Watch } from "@phosphor-icons/react";
import { formatGoalTime, GoalAnchor, GoalPromptContext, Lang } from "@/lib/goalAssessment";

/** What Coach Uphill was given for this estimate: the CONTEXT block sent to
 *  Gemini, grouped for reading, plus the calculated estimates (ANCHORS). */

const METHOD_LABELS: Record<string, [string, string]> = {
  physics: ["Course physics from this result", "Mô hình cung đường từ kết quả này"],
  field_rank: ["Your finishing rank on this field", "Thứ hạng của bạn áp vào giải này"],
  percentile_transfer: ["Field percentile transfer", "Quy đổi theo percentile"],
  field_prior: ["Field position from weekly volume", "Vị trí trong đoàn theo khối lượng tuần"],
  easy_pace: ["Course physics from your easy pace", "Mô hình cung đường từ pace Easy"],
  base_pace: ["Course physics from your flat pace", "Mô hình cung đường từ pace đường bằng"],
};

type Row = [string, React.ReactNode];

const mono: React.CSSProperties = { fontFamily: "var(--font-mono)", fontWeight: 700, color: "var(--text-primary)" };
const muted: React.CSSProperties = { color: "var(--text-muted)", fontSize: "11px" };

function pace(minPerKm: unknown): string | null {
  if (typeof minPerKm !== "number" || !minPerKm) return null;
  const total = Math.round(minPerKm * 60);
  return `${Math.floor(total / 60)}:${String(total % 60).padStart(2, "0")}/km`;
}

function present(rows: [string, unknown][]): Row[] {
  return rows.filter(([, v]) => v !== null && v !== undefined && v !== "") as Row[];
}

function climbName(climb: unknown): string | null {
  if (typeof climb === "string") return climb;
  if (climb && typeof climb === "object" && "name" in climb) return String((climb as { name: unknown }).name);
  return null;
}

function Card({
  icon,
  title,
  wide = false,
  children,
}: {
  icon: React.ReactNode;
  title: string;
  wide?: boolean;
  children: React.ReactNode;
}) {
  return (
    <section
      style={{
        gridColumn: wide ? "1 / -1" : undefined,
        border: "1px solid var(--border-color)",
        borderRadius: "12px",
        background: "rgba(255,255,255,0.6)",
        padding: "12px 14px",
        display: "flex",
        flexDirection: "column",
        gap: "8px",
        minWidth: 0,
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: "6px", color: "var(--accent-primary)", fontWeight: 700, fontSize: "11px", textTransform: "uppercase", letterSpacing: "0.4px" }}>
        {icon}
        <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{title}</span>
      </div>
      {children}
    </section>
  );
}

/** Label / value pairs as a compact two-column grid of small stats. */
function Stats({ rows }: { rows: Row[] }) {
  return (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(96px, 1fr))", gap: "8px 12px" }}>
      {rows.map(([label, value]) => (
        <div key={label} style={{ display: "flex", flexDirection: "column", gap: "1px", minWidth: 0 }}>
          <span style={muted}>{label}</span>
          <span style={{ fontWeight: 600, color: "var(--text-primary)", fontSize: "13px" }}>{value}</span>
        </div>
      ))}
    </div>
  );
}

function Chips({ items }: { items: string[] }) {
  return (
    <div style={{ display: "flex", flexWrap: "wrap", gap: "4px" }}>
      {items.map((item) => (
        <span key={item} style={{ padding: "2px 8px", borderRadius: "999px", background: "rgba(16,185,129,0.08)", color: "var(--text-secondary)", fontSize: "11px" }}>
          {item}
        </span>
      ))}
    </div>
  );
}

/** A list row: title and meta on the left, a finish time on the right. */
function ListRow({ title, meta, value }: { title: React.ReactNode; meta?: string; value: string }) {
  return (
    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: "12px", padding: "6px 0", borderTop: "1px solid rgba(0,0,0,0.05)" }}>
      <div style={{ display: "flex", flexDirection: "column", gap: "1px", minWidth: 0 }}>
        <span style={{ color: "var(--text-primary)", fontWeight: 500 }}>{title}</span>
        {meta && <span style={muted}>{meta}</span>}
      </div>
      <span style={{ ...mono, fontSize: "14px" }}>{value}</span>
    </div>
  );
}

export function GoalContextView({
  context,
  anchors,
  lang,
}: {
  context: GoalPromptContext | null | undefined;
  anchors: GoalAnchor[];
  lang: Lang;
}) {
  const t = (en: string, vi: string) => (lang === "en" ? en : vi);
  const estimates = <AnchorList anchors={anchors} lang={lang} />;
  if (!context) return <Grid>{estimates}</Grid>; // assessments saved before the context was stored

  const race = context.race || {};
  const field = race.field;
  const a = context.athlete || {};
  const watch = a.watch_8wk as Record<string, number | string | null> | undefined;
  const recovery = a.recovery as Record<string, number | string | null> | undefined;
  const block = context.block;
  const pct = field?.percentile_mins || {};
  const climbs = (race.key_climbs || []).map(climbName).filter((c): c is string => !!c);
  const history = context.history || [];

  const raceRows = present([
    [t("Distance", "Cự ly"), race.distance_km != null ? `${Math.round(race.distance_km)} km` : null],
    ["D+", race.gain_m != null ? `${Math.round(race.gain_m)} m` : null],
    [t("Race date", "Ngày race"), race.date?.slice(0, 10)],
    [t("Weeks to race", "Số tuần tới race"), context.weeks_to_race],
    [t("Course profile", "Profile cung đường"), race.profile_source === "gpx" ? "GPX" : race.profile_source ? t("Estimated", "Ước tính") : null],
    [t("Time Target", "Time Target"), context.current_target_mins ? formatGoalTime(context.current_target_mins) : null],
  ]);

  const fieldStats = present([
    [t("Winner", "Người thắng"), field?.winner_mins ? formatGoalTime(field.winner_mins) : null],
    [t("10% finished", "10% về đích"), pct.p10 ? formatGoalTime(pct.p10) : null],
    [t("Half finished", "50% về đích"), pct.p50 ? formatGoalTime(pct.p50) : null],
    [t("90% finished", "90% về đích"), pct.p90 ? formatGoalTime(pct.p90) : null],
  ]);

  const athleteRows = present([
    [t("Age", "Tuổi"), a.age],
    [t("Sex", "Giới tính"), a.sex],
    [t("Weight", "Cân nặng"), a.weight_kg != null ? `${a.weight_kg} kg` : null],
    [t("Weekly km", "Km/tuần"), a.profile_weekly_km],
    ["Max HR", a.max_hr],
    ["AeT HR", a.aet_hr],
    ["AnT HR", a.ant_hr],
    ["Threshold pace", a.threshold_pace ? `${a.threshold_pace}/km` : null],
    ["Easy pace", pace(a.easy_pace_min_km)],
    ["VO2max", a.vo2max],
    ["UTMB index", a.utmb_index],
  ]);

  const watchRows = watch
    ? present([
        [t("Runs", "Số buổi"), `${watch.runs} / ${watch.weeks ?? 8} ${t("wk", "tuần")}`],
        [t("Km / week", "Km / tuần"), watch.avg_weekly_km],
        [t("D+ / week", "D+ / tuần"), watch.avg_weekly_vert_m != null ? `${watch.avg_weekly_vert_m} m` : null],
        [t("Last run", "Buổi gần nhất"), watch.last_activity],
        ["Resting HR", recovery?.resting_hr],
        ["HRV", recovery?.hrv_ms != null ? `${recovery.hrv_ms} ms` : null],
        [t("Recovery", "Hồi phục"), recovery?.recovery_percent != null ? `${recovery.recovery_percent}%` : null],
        [t("Load ratio", "Tỷ lệ tải"), recovery?.load_ratio],
      ])
    : [];

  const blockRows = block
    ? present([
        [t("Weeks done", "Tuần đã tập"), `${block.weeks_done}/${block.total_weeks ?? "?"}`],
        [t("Sessions", "Buổi tập"), `${block.sessions_completed}/${block.sessions_planned}`],
        [t("Distance", "Cự ly"), `${block.completed_km}/${block.planned_km} km`],
        ["D+", `${block.completed_vert_m}/${block.planned_vert_m} m`],
        [t("Block grade", "Đánh giá Block"), block.latest_block_quality_grade as string | null],
        ["RPE", block.latest_block_rpe as number | null],
      ])
    : [];
  const completion = typeof block?.completion_pct === "number" ? block.completion_pct : null;
  const blockNotes = (block?.coach_notes as string[] | undefined) || [];

  return (
    <Grid>
      <Card icon={<Flag size={14} weight="duotone" />} title={race.name || t("Target race", "Race mục tiêu")}>
        <Stats rows={raceRows} />
        {!!race.terrain?.length && <Chips items={race.terrain} />}
        {climbs.length > 0 && (
          <span style={muted}>
            {t("Key climbs", "Dốc chính")}: {climbs.join(", ")}
          </span>
        )}
      </Card>

      <Card icon={<ChartLineUp size={14} weight="duotone" />} title={t("Past results on this race", "Kết quả các năm trước")}>
        {fieldStats.length ? (
          <>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(2, minmax(0, 1fr))", gap: "8px" }}>
              {fieldStats.map(([label, value]) => (
                <div key={label} style={{ borderRadius: "8px", background: "rgba(0,0,0,0.03)", padding: "6px 8px" }}>
                  <div style={muted}>{label}</div>
                  <div style={{ ...mono, fontSize: "16px" }}>{value}</div>
                </div>
              ))}
            </div>
            <span style={muted}>
              {[field?.years?.length ? field.years.join(", ") : null, field?.finishers ? `${field.finishers} ${t("finishers", "người về đích")}` : null]
                .filter(Boolean)
                .join(" · ")}
            </span>
          </>
        ) : (
          <span style={muted}>
            {t("No past results for this distance yet, so the field can't be used.", "Chưa có kết quả các năm trước cho cự ly này.")}
          </span>
        )}
      </Card>

      {athleteRows.length > 0 && (
        <Card icon={<User size={14} weight="duotone" />} title={t("You", "Bạn")}>
          <Stats rows={athleteRows} />
        </Card>
      )}

      {watchRows.length > 0 && (
        <Card icon={<Watch size={14} weight="duotone" />} title={t("Watch · last 8 weeks", "Đồng hồ · 8 tuần gần nhất")}>
          <Stats rows={watchRows} />
        </Card>
      )}

      {block && (
        <Card icon={<CalendarCheck size={14} weight="duotone" />} title="Training Block" wide>
          {completion != null && (
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <div style={{ flex: 1, height: "6px", borderRadius: "999px", background: "rgba(0,0,0,0.06)", overflow: "hidden" }}>
                <div style={{ width: `${Math.min(completion, 100)}%`, height: "100%", background: "var(--accent-primary)" }} />
              </div>
              <span style={{ ...mono, fontSize: "12px" }}>{completion}%</span>
            </div>
          )}
          <Stats rows={blockRows} />
          {blockNotes.map((note, i) => (
            <span key={i} style={muted}>
              · {note}
            </span>
          ))}
        </Card>
      )}

      <Card icon={<Trophy size={14} weight="duotone" />} title={`${t("Race history", "Lịch sử race")} (${history.length})`} wide>
        {history.length === 0 ? (
          <span style={muted}>{t("No results linked yet.", "Chưa có kết quả nào.")}</span>
        ) : (
          <div>
            {history.map((r, i) => (
              <ListRow
                key={i}
                title={r.race}
                meta={[
                  r.date.slice(0, 7),
                  `${Math.round(r.distance_km)} km`,
                  r.gain_m ? `${Math.round(r.gain_m)} m D+` : null,
                  r.discipline === "road" ? "Road" : null,
                  r.rank ? `#${r.rank}` : null,
                ]
                  .filter(Boolean)
                  .join(" · ")}
                value={r.time || "—"}
              />
            ))}
          </div>
        )}
      </Card>

      {estimates}
    </Grid>
  );
}

function Grid({ children }: { children: React.ReactNode }) {
  return (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: "10px", marginTop: "10px", fontSize: "12.5px" }}>
      {children}
    </div>
  );
}

function AnchorList({ anchors, lang }: { anchors: GoalAnchor[]; lang: Lang }) {
  if (!anchors.length) return null;
  return (
    <Card icon={<Calculator size={14} weight="duotone" />} title={lang === "en" ? "Calculated estimates" : "Ước tính đã tính sẵn"} wide>
      <div>
        {anchors.map((anchor) => (
          <ListRow
            key={anchor.id}
            title={(METHOD_LABELS[anchor.method] || [anchor.method, anchor.method])[lang === "en" ? 0 : 1]}
            meta={anchor.notes.join(" · ")}
            value={formatGoalTime(anchor.minutes)}
          />
        ))}
      </div>
    </Card>
  );
}
