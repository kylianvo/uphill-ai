"use client";

import React, { useEffect, useState } from "react";
import { useAppContext } from "@/contexts/AppContext";
import { getApiBaseUrl } from "@/lib/apiUrlOverride";
import { Flag, ArrowRight } from "@phosphor-icons/react";
import styles from "./RaceHistory.module.css";

export default function RaceHistoryPlanInfo({ lang, planId }: { lang: "en" | "vi"; planId?: number | null }) {
  const { setProfileSettingsOpen, actingAsAthleteId } = useAppContext();
  const [data, setData] = useState<{ selected: number; target?: { adjusted_time_mins: number }; improvement?: number } | null>(null);
  useEffect(() => {
    if (actingAsAthleteId) return;
    const token = localStorage.getItem("uphill_session_token");
    if (!token) return;
    fetch(`${getApiBaseUrl()}/api/race-history`, { headers: { Authorization: `Bearer ${token}` } })
      .then((response) => response.ok ? response.json() : null)
      .then((history) => {
        if (!history) return;
        setData({ selected: (history.results || []).filter((result: { selected: boolean }) => result.selected).length,
          target: history.scenarios?.plan_id === planId ? history.scenarios?.target : undefined,
          improvement: history.scenarios?.improvement_pct });
      }).catch(() => {});
  }, [actingAsAthleteId, planId]);
  if (actingAsAthleteId || !data) return null;
  if (!data.selected) return <button type="button" onClick={() => setProfileSettingsOpen(true)} className={styles.button}>
    <Flag size={16} weight="duotone" style={{ color: "var(--accent-primary)" }} />
    {lang === "en" ? "Link a past race result to inform this plan" : "Liên kết kết quả Race trước để bổ sung cho Plan"}
    <ArrowRight size={14} />
  </button>;
  if (!data.target) return null;
  const total = Math.round(data.target.adjusted_time_mins * 60);
  const time = `${Math.floor(total / 3600)}:${String(Math.floor(total % 3600 / 60)).padStart(2, "0")}`;
  return <div className={styles.scenario}>
    <strong>{lang === "en" ? "After this block: scenario" : "Sau Block này: kịch bản"}</strong>
    <div className={styles.scenarioTime}>{time}</div>
    <small className={styles.muted}>{lang === "en" ? `Assumes ${data.improvement}% improvement. No gain is guaranteed.` : `Giả định cải thiện ${data.improvement}%. Không bảo đảm thành tích.`}</small>
  </div>;
}
