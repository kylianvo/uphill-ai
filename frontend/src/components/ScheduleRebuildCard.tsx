/* eslint-disable @typescript-eslint/no-explicit-any */
import React from "react";
import WorkoutCard from "./WorkoutCard";
import { computeWorkoutDate } from "../utils/planDate";
import { dayLabel } from "../utils/dayLabels";
import {
  ProposalDetail,
  ProposalState,
  ProposalStatus,
  RebuildDiff,
  applyProposal,
  describeGuard,
  describeWarning,
  discardProposal,
  fetchProposal,
  tr,
} from "../lib/scheduleProposals";

export const POLL_MS = 3000;
export const POLL_LIMIT_MS = 240000;

interface Props {
  data: any;
  lang: string;
  isMobile?: boolean;
  liveState?: ProposalState;
  onApplied?: (workouts: unknown[]) => void;
}

const wrap: React.CSSProperties = {
  padding: "12px",
  borderRadius: "12px",
  backgroundColor: "rgba(255, 255, 255, 0.6)",
  border: "1px solid rgba(0, 0, 0, 0.08)",
  marginTop: "6px",
  marginBottom: "6px",
  maxWidth: "100%",
};
const btn: React.CSSProperties = { padding: "6px 14px", borderRadius: "8px", border: "none", fontSize: "13px", cursor: "pointer" };

const brief = (w: any) => `${w.title} · ${Math.round(Number(w.duration_minutes) || 0)}′`;
const joined = (rows: any[], lang: string) => (rows.length ? rows.map(brief).join(" + ") : tr(lang, "rebuild_rest"));

function totalsLine(lang: string, t: any): string {
  return tr(lang, "rebuild_totals_line")
    .replace("{min}", String(t?.min ?? 0))
    .replace("{km}", String(t?.km ?? 0))
    .replace("{vert}", String(t?.vert ?? 0));
}

export default function ScheduleRebuildCard({ data, lang, isMobile = false, liveState, onApplied }: Props) {
  const [localState, setLocalState] = React.useState<ProposalState | null>(null);
  const [detail, setDetail] = React.useState<ProposalDetail | null>(null);
  const [timedOut, setTimedOut] = React.useState(false);
  const [busy, setBusy] = React.useState(false);
  const [failed, setFailed] = React.useState(false);
  const [openDay, setOpenDay] = React.useState<string | null>(null);

  React.useEffect(() => {
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout> | undefined;
    const started = Date.now();
    const tick = async () => {
      if (cancelled) return;
      if (typeof document !== "undefined" && document.hidden) {
        timer = setTimeout(tick, POLL_MS);
        return;
      }
      const next = await fetchProposal(data.proposal_id);
      if (cancelled) return;
      if (next) setDetail(next);
      if (next && next.status !== "generating") return;
      if (Date.now() - started >= POLL_LIMIT_MS) {
        setTimedOut(true);
        return;
      }
      timer = setTimeout(tick, POLL_MS);
    };
    tick();
    return () => {
      cancelled = true;
      if (timer) clearTimeout(timer);
    };
  }, [data.proposal_id]);

  const polled: ProposalState | null = detail ? { status: detail.status, stale_reason: detail.stale_reason } : null;
  let state: ProposalState = localState ?? polled ?? liveState ?? { status: (data.status as ProposalStatus) || "generating" };
  if (timedOut && state.status === "generating") state = { status: "failed" };

  const diff = detail && (detail.diff as RebuildDiff).days ? (detail.diff as RebuildDiff) : null;
  const week = diff?.week ?? data.week;
  const planForDates = { start_date: data.plan_start_date, race_date: data.race_date };
  const getWorkoutDate = (wo: any) => {
    const d = computeWorkoutDate(planForDates, [], wo);
    return d ? d.toLocaleDateString(lang === "vi" ? "vi-VN" : "en-US", { month: "short", day: "numeric" }) : "";
  };

  const onApply = async () => {
    setBusy(true);
    setFailed(false);
    const outcome = await applyProposal(data.proposal_id);
    setBusy(false);
    if (outcome.kind === "applied") {
      setLocalState(outcome.state);
      onApplied?.(outcome.workouts);
    } else if (outcome.kind === "stale") {
      setLocalState(outcome.state);
    } else {
      setFailed(true);
    }
  };

  const onDiscard = async () => {
    setBusy(true);
    const status = await discardProposal(data.proposal_id);
    setBusy(false);
    if (status) setLocalState({ status });
  };

  return (
    <div style={wrap}>
      <div style={{ fontWeight: 600, marginBottom: "6px" }}>{tr(lang, "rebuild_title").replace("{week}", String(week))}</div>
      {data.rationale && (
        <div style={{ fontSize: "13px", color: "var(--text-secondary)", marginBottom: "8px" }}>{data.rationale}</div>
      )}

      {state.status === "generating" && (
        <div style={{ fontSize: "13px", color: "var(--text-secondary)" }}>
          {tr(lang, "rebuild_drafting").replace("{week}", String(week))}
        </div>
      )}

      {diff && state.status !== "generating" && state.status !== "failed" && (
        <>
          <div style={{ fontSize: "12.5px", marginBottom: "6px" }}>
            <strong>{tr(lang, "rebuild_totals")}:</strong> {totalsLine(lang, diff.totals.before)} → {totalsLine(lang, diff.totals.after)}
          </div>
          <div style={{ fontSize: "12px", color: "var(--text-muted)", marginBottom: "4px" }}>
            {tr(lang, "rebuild_from").replace("{day}", dayLabel(diff.from_day, lang))}
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
            {diff.days.map((d) => {
              const changed = d.before.length > 0 || d.after.length > 0;
              if (!changed && d.kept.length === 0) return null;
              const same = changed && joined(d.before, lang) === joined(d.after, lang);
              return (
                <div key={d.day} style={{ opacity: !changed || same ? 0.55 : 1 }}>
                  <div
                    role="button"
                    tabIndex={0}
                    onClick={() => d.after.length > 0 && setOpenDay(openDay === d.day ? null : d.day)}
                    onKeyDown={(e) => e.key === "Enter" && d.after.length > 0 && setOpenDay(openDay === d.day ? null : d.day)}
                    style={{ fontSize: "12.5px", cursor: d.after.length ? "pointer" : "default" }}
                  >
                    <strong>{dayLabel(d.day, lang)}</strong>{" "}
                    {d.kept.map((k: any, i: number) => (
                      <span key={`k${i}`}>
                        {brief(k)} <em style={{ color: "var(--text-muted)" }}>({tr(lang, "rebuild_kept")})</em>{" "}
                      </span>
                    ))}
                    {changed && <span>{joined(d.before, lang)} → {joined(d.after, lang)}</span>}
                  </div>
                  {openDay === d.day &&
                    d.after.map((wo: any, i: number) => (
                      <WorkoutCard
                        key={i}
                        wo={{ ...wo, week_number: diff.week }}
                        lang={lang}
                        isMobile={isMobile}
                        getWorkoutDate={getWorkoutDate}
                        readOnly
                      />
                    ))}
                </div>
              );
            })}
          </div>
        </>
      )}

      {state.status === "proposed" && detail?.warnings && detail.warnings.length > 0 && (
        <div style={{ marginTop: "8px", fontSize: "12.5px", color: "#b45309" }}>
          <strong>{tr(lang, "sched_heads_up")}</strong>
          <ul style={{ margin: "4px 0 0 16px", padding: 0 }}>
            {detail.warnings.map((w, i) => (
              <li key={i}>{describeWarning(lang, w)}</li>
            ))}
          </ul>
        </div>
      )}

      <div style={{ display: "flex", alignItems: "center", gap: "8px", marginTop: "10px", flexWrap: "wrap" }}>
        {state.status === "proposed" && diff && (
          <button
            onClick={onApply}
            disabled={busy}
            style={{ ...btn, backgroundColor: "var(--accent, #2563eb)", color: "white", opacity: busy ? 0.6 : 1 }}
          >
            {busy ? tr(lang, "sched_applying") : tr(lang, "sched_apply")}
          </button>
        )}
        {(state.status === "proposed" || state.status === "generating") && (
          <button
            onClick={onDiscard}
            disabled={busy}
            style={{ ...btn, backgroundColor: "transparent", border: "1px solid rgba(0,0,0,0.15)" }}
          >
            {tr(lang, "sched_discard")}
          </button>
        )}
        {state.status === "applied" && <span style={{ color: "#059669", fontWeight: 600 }}>{tr(lang, "sched_applied")}</span>}
        {state.status === "discarded" && <span style={{ color: "var(--text-muted)" }}>{tr(lang, "sched_discarded")}</span>}
        {state.status === "failed" && <span style={{ color: "#dc2626", fontSize: "12.5px" }}>{tr(lang, "rebuild_failed")}</span>}
        {state.status === "stale" && (
          <div style={{ fontSize: "12.5px" }}>
            <span style={{ color: "#b45309", fontWeight: 600 }}>{tr(lang, "sched_stale")}</span>
            {state.stale_reason && <span> — {describeGuard(lang, state.stale_reason)}</span>}
            <div style={{ color: "var(--text-secondary)" }}>{tr(lang, "sched_stale_hint")}</div>
          </div>
        )}
        {failed && <span style={{ color: "#dc2626", fontSize: "12.5px" }}>{tr(lang, "sched_apply_failed")}</span>}
      </div>
    </div>
  );
}
