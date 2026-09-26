"use client";

import React, { useCallback, useEffect, useState } from "react";
import { ArrowsClockwise, Target } from "@phosphor-icons/react";
import ConfirmActionModal from "@/components/ConfirmActionModal";
import { GoalKey, GoalResult } from "@/components/GoalResult";
import {
  applyPlanGoal,
  formatGoalTime,
  getPlanGoal,
  goalPillLabel,
  Lang,
  PlanGoal,
  reassessPlanGoal,
} from "@/lib/goalAssessment";

/** Plan-header Goal pill: latest goal assessment vs Time Target, styled like
 *  the Coach notes pill next to it. Replaces the old "After this block" block. */
export function GoalPill({
  planId,
  lang,
  athleteId,
  onTargetChange,
}: {
  planId: number;
  lang: Lang;
  athleteId?: number | null;
  onTargetChange?: (targetTimeHours: number) => void;
}) {
  const t = (en: string, vi: string) => (lang === "en" ? en : vi);
  const [goal, setGoal] = useState<PlanGoal | null>(null);
  const [expanded, setExpanded] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [confirming, setConfirming] = useState(false);

  const load = useCallback(() => {
    getPlanGoal(planId, lang, athleteId).then(setGoal).catch(() => setGoal(null));
  }, [planId, lang, athleteId]);

  useEffect(() => {
    load();
  }, [load]);

  if (!goal) return null;
  const { text, dot } = goalPillLabel(goal, lang);
  const assessment = goal.assessment;
  const suggested = goal.status.suggested_mins;

  const target = goal.target_time_hours ? goal.target_time_hours * 60 : null;
  let highlight: GoalKey | null = null;
  if (assessment?.goals && target) {
    const keys: GoalKey[] = ["a", "b", "c"];
    const closest = keys.reduce((best, k) =>
      Math.abs(assessment.goals![k] - target) < Math.abs(assessment.goals![best] - target) ? k : best,
    );
    if (Math.abs(assessment.goals[closest] - target) / target <= 0.03) highlight = closest;
  }

  const reassess = async () => {
    setBusy(true);
    setError("");
    try {
      setGoal(await reassessPlanGoal(planId, lang, athleteId));
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  };

  const apply = async () => {
    if (suggested == null) return;
    setBusy(true);
    setError("");
    try {
      const next = await applyPlanGoal(planId, suggested, athleteId);
      setGoal(next);
      if (next.target_time_hours) onTargetChange?.(next.target_time_hours);
      setConfirming(false);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  };

  const assessedLine = assessment
    ? `${t("Assessed", "Đánh giá")} ${new Date(assessment.created_at).toLocaleDateString(lang === "en" ? "en-GB" : "vi-VN", { day: "numeric", month: "short" })}` +
      (assessment.plan_week ? ` · ${t("after week", "sau tuần")} ${assessment.plan_week}` : "")
    : "";

  return (
    <div style={{ marginTop: "6px" }}>
      <button
        type="button"
        onClick={() => setExpanded(!expanded)}
        aria-expanded={expanded}
        style={{
          display: "flex",
          alignItems: "center",
          gap: "6px",
          padding: "6px 10px",
          background: "rgba(16,185,129,0.08)",
          border: "1px solid var(--border-color)",
          borderRadius: "8px",
          fontSize: "12px",
          color: "var(--text-secondary)",
          cursor: "pointer",
        }}
      >
        <span aria-hidden="true" style={{ width: "8px", height: "8px", borderRadius: "50%", background: dot }} />
        {text}
      </button>

      {expanded && (
        <div
          style={{
            marginTop: "8px",
            padding: "12px",
            border: "1px solid var(--border-color)",
            borderRadius: "8px",
            background: "rgba(255,255,255,0.5)",
            display: "flex",
            flexDirection: "column",
            gap: "12px",
            maxWidth: "560px",
          }}
        >
          {assessment ? (
            <GoalResult assessment={assessment} lang={lang} highlight={highlight} compact />
          ) : (
            <p style={{ fontSize: "12px", color: "var(--text-muted)", margin: 0 }}>
              {t(
                "No goal assessment for this plan yet. Run one to compare your target with your data.",
                "Plan này chưa có đánh giá mục tiêu. Chạy đánh giá để so mục tiêu với dữ liệu của bạn.",
              )}
            </p>
          )}

          {error && <div style={{ fontSize: "12px", color: "#ef4444" }}>{error}</div>}

          <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", alignItems: "center" }}>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={reassess}
              disabled={busy}
              style={{ padding: "6px 12px", fontSize: "12px", display: "inline-flex", alignItems: "center", gap: "6px", borderRadius: "999px" }}
            >
              <ArrowsClockwise size={14} className={busy ? "match-spin" : undefined} />
              {t("Re-assess with my training", "Đánh giá lại theo buổi tập")}
            </button>
            {suggested != null && (
              <button
                type="button"
                className="btn btn-primary"
                onClick={() => setConfirming(true)}
                disabled={busy}
                style={{ padding: "6px 12px", fontSize: "12px", display: "inline-flex", alignItems: "center", gap: "6px", borderRadius: "999px" }}
              >
                <Target size={14} />
                {t(`Update target to ${formatGoalTime(suggested)}`, `Đổi mục tiêu thành ${formatGoalTime(suggested)}`)}
              </button>
            )}
            {assessedLine && <span style={{ fontSize: "11px", color: "var(--text-muted)" }}>{assessedLine}</span>}
          </div>
        </div>
      )}

      <ConfirmActionModal
        isOpen={confirming}
        onClose={() => setConfirming(false)}
        onConfirm={apply}
        isLoading={busy}
        title={t("Update Time Target?", "Đổi Time Target?")}
        message={t(
          `Your plan's Time Target becomes ${suggested != null ? formatGoalTime(suggested) : ""}. Future blocks use the new target; workouts already scheduled stay as they are.`,
          `Time Target của plan sẽ là ${suggested != null ? formatGoalTime(suggested) : ""}. Các block sau dùng mục tiêu mới; các buổi tập đã lên lịch giữ nguyên.`,
        )}
        confirmLabel={t("Update target", "Đổi mục tiêu")}
        cancelLabel={t("Cancel", "Huỷ")}
      />
    </div>
  );
}
