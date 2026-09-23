/* eslint-disable @typescript-eslint/no-explicit-any */
import React from "react";
import WorkoutCard from "./WorkoutCard";
import { computeWorkoutDate } from "../utils/planDate";
import { dayLabel } from "../utils/dayLabels";
import {
  ProposalState,
  ProposalStatus,
  applyProposal,
  describeGuard,
  describeWarning,
  discardProposal,
  tr,
} from "../lib/scheduleProposals";

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
const btn: React.CSSProperties = {
  padding: "6px 14px",
  borderRadius: "8px",
  border: "none",
  fontSize: "13px",
  cursor: "pointer",
};

export default function ScheduleProposalCard({ data, lang, isMobile = false, liveState, onApplied }: Props) {
  const [localState, setLocalState] = React.useState<ProposalState>({
    status: (data.status as ProposalStatus) || "proposed",
  });
  const [busy, setBusy] = React.useState(false);
  const [failed, setFailed] = React.useState(false);

  const state = liveState ?? localState;

  const warnings = state.result?.warnings ?? data.warnings ?? [];
  const planForDates = { start_date: data.plan_start_date, race_date: data.race_date };
  const workoutsForDates = (data.diff || []).map((d: any) => d.workout);
  const getWorkoutDate = (wo: any) => {
    const d = computeWorkoutDate(planForDates, workoutsForDates, wo);
    return d ? d.toLocaleDateString(lang === "vi" ? "vi-VN" : "en-US", { month: "short", day: "numeric" }) : "";
  };
  const weekDay = (week: number, day: string) =>
    tr(lang, "sched_week_day").replace("{week}", String(week)).replace("{day}", dayLabel(day, lang));

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
      <div style={{ fontWeight: 600, marginBottom: "6px" }}>{tr(lang, "sched_proposal_title")}</div>
      {data.rationale && (
        <div style={{ fontSize: "13px", color: "var(--text-secondary)", marginBottom: "8px" }}>{data.rationale}</div>
      )}
      <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
        {(data.diff || []).map((d: any) => (
          <div key={d.workout_id}>
            <div style={{ fontSize: "12px", fontWeight: 600, marginBottom: "4px" }}>
              {weekDay(d.from_week, d.from_day)} → {weekDay(d.to_week, d.to_day)}
            </div>
            <WorkoutCard wo={d.workout} lang={lang} isMobile={isMobile} getWorkoutDate={getWorkoutDate} readOnly />
          </div>
        ))}
      </div>
      {warnings.length > 0 && (
        <div style={{ marginTop: "8px", fontSize: "12.5px", color: "#b45309" }}>
          <strong>{tr(lang, "sched_heads_up")}</strong>
          <ul style={{ margin: "4px 0 0 16px", padding: 0 }}>
            {warnings.map((w: any, i: number) => (
              <li key={i}>{describeWarning(lang, w)}</li>
            ))}
          </ul>
        </div>
      )}
      <div style={{ display: "flex", alignItems: "center", gap: "8px", marginTop: "10px", flexWrap: "wrap" }}>
        {state.status === "proposed" && (
          <>
            <button
              onClick={onApply}
              disabled={busy}
              style={{ ...btn, backgroundColor: "var(--accent, #2563eb)", color: "white", opacity: busy ? 0.6 : 1 }}
            >
              {busy ? tr(lang, "sched_applying") : tr(lang, "sched_apply")}
            </button>
            <button
              onClick={onDiscard}
              disabled={busy}
              style={{ ...btn, backgroundColor: "transparent", border: "1px solid rgba(0,0,0,0.15)" }}
            >
              {tr(lang, "sched_discard")}
            </button>
          </>
        )}
        {state.status === "applied" && <span style={{ color: "#059669", fontWeight: 600 }}>{tr(lang, "sched_applied")}</span>}
        {state.status === "discarded" && <span style={{ color: "var(--text-muted)" }}>{tr(lang, "sched_discarded")}</span>}
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
