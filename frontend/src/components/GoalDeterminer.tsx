/* eslint-disable @typescript-eslint/no-explicit-any */
"use client";

import React, { useState } from "react";
import { useAnalytics } from "@/hooks/useAnalytics";
import { useAppContext } from "@/contexts/AppContext";
import { RaceMatch } from "@/hooks/useRaceMatch";
import { RaceNameField } from "@/components/RaceNameField";
import { formatDurationHM, parsePaceToMinutes } from "@/lib/paceStrategy";
import { Crosshair, XCircle, Gauge, TrendUp, ShieldCheck, Lightning } from "@phosphor-icons/react";

interface GoalDeterminerProps {
  isOpen: boolean;
  onClose: () => void;
  lang: "en" | "vi";
  user?: any;
  activePlan?: any;
}

interface GoalEstimate {
  base_flat_pace_min_km: number;
  predicted_time_mins: number;
  adjusted_time_mins: number;
  improvement_pct: number;
  goals: { ambitious: number; realistic: number; safe: number };
  distance_km: number;
  elevation_gain_m: number;
  race_name?: string;
  benchmarks?: { year: number; finishers?: number; winner_time?: string; conditions_note?: string }[];
  rank_transfer_mins?: number;
}

function getBaseUrl(): string {
  let baseUrl = "http://localhost:8000";
  if (typeof window !== "undefined") {
    if (window.location.hostname !== "localhost") baseUrl = "";
    baseUrl = localStorage.getItem("UPHILL_API_URL_OVERRIDE") || process.env.NEXT_PUBLIC_API_URL || baseUrl;
  }
  return baseUrl;
}

const boxStyle: React.CSSProperties = {
  background: "rgba(0,0,0,0.03)",
  padding: "16px",
  borderRadius: "16px",
  border: "1px solid rgba(0,0,0,0.05)",
};

const labelStyle: React.CSSProperties = {
  display: "block",
  fontSize: "12px",
  textTransform: "uppercase",
  letterSpacing: "0.5px",
  color: "var(--text-muted)",
  marginBottom: "8px",
  fontWeight: 600,
};

const inputStyle: React.CSSProperties = {
  width: "100%",
  background: "transparent",
  border: "none",
  fontSize: "16px",
  fontWeight: 600,
  color: "var(--text-primary)",
  outline: "none",
};

export const GoalDeterminer: React.FC<GoalDeterminerProps> = ({ isOpen, onClose, lang, user }) => {
  const [raceName, setRaceName] = useState("");
  const [raceMatch, setRaceMatch] = useState<RaceMatch | null>(null);
  const [distance, setDistance] = useState("");
  const [gain, setGain] = useState("");
  const [weeks, setWeeks] = useState("");

  // Stored aerobic zone pace from onboarding/profile — the zero-input default
  const profileZonePace =
    parsePaceToMinutes(user?.zone2_pace_max || "") ?? parsePaceToMinutes(user?.zone2_pace_min || "") ?? null;
  const [fitnessMode, setFitnessMode] = useState<"profile" | "result" | "pace">(
    profileZonePace ? "profile" : "result",
  );
  const [refRaceName, setRefRaceName] = useState("");
  const [refMatch, setRefMatch] = useState<RaceMatch | null>(null);
  const [refDistance, setRefDistance] = useState("");
  const [refGain, setRefGain] = useState("");
  const [refTime, setRefTime] = useState("");
  const [flatPace, setFlatPace] = useState("");

  const [estimate, setEstimate] = useState<GoalEstimate | null>(null);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");

  const { trackEvent } = useAnalytics();
  const { setPaceHandoff, setIsPaceStrategyOpen } = useAppContext();

  const t = (en: string, vi: string) => (lang === "en" ? en : vi);

  // Typed numbers override the KB match — some races change course yearly
  const targetDistance = parseFloat(distance) || raceMatch?.distance_km || null;
  const targetGain = parseFloat(gain) || raceMatch?.elevation_gain_m || 0;
  const refDistanceKm = parseFloat(refDistance) || refMatch?.distance_km || null;
  const refGainM = parseFloat(refGain) || refMatch?.elevation_gain_m || 0;
  const profileBasePace = profileZonePace ? Math.round(profileZonePace * 0.95 * 100) / 100 : null;
  const canEstimate =
    !!targetDistance &&
    (fitnessMode === "pace"
      ? !!parseFloat(flatPace)
      : fitnessMode === "profile"
        ? !!profileBasePace
        : !!refTime && !!refDistanceKm);

  const handleEstimate = async () => {
    setLoading(true);
    setErrorMsg("");
    setEstimate(null);
    try {
      const payload: Record<string, unknown> = {
        race_name: raceName || null,
        distance_km: targetDistance,
        elevation_gain_m: targetGain,
        weeks_to_race: parseFloat(weeks) || null,
      };
      if (fitnessMode === "pace") {
        payload.flat_pace_min_km = parseFloat(flatPace);
      } else if (fitnessMode === "profile") {
        payload.flat_pace_min_km = profileBasePace;
      } else {
        payload.reference_race_name = refRaceName || null;
        payload.reference_distance_km = refDistanceKm;
        payload.reference_elevation_gain_m = refGainM;
        payload.reference_time = refTime;
      }
      const response = await fetch(`${getBaseUrl()}/api/coach/goal-estimate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!response.ok) {
        const detail = await response.json().catch(() => null);
        throw new Error(typeof detail?.detail === "string" ? detail.detail : `HTTP ${response.status}`);
      }
      setEstimate(await response.json());
      trackEvent("goal_determiner_used", { fitness_mode: fitnessMode });
    } catch (err: any) {
      const detail = `${err?.message || "network error"} · ${getBaseUrl()}`;
      const overrideHint = localStorage.getItem("UPHILL_API_URL_OVERRIDE")
        ? t(
            " An ?api= override is active — visit ?api=clear to use the default backend.",
            " Đang có ghi đè ?api= — truy cập ?api=clear để dùng backend mặc định.",
          )
        : "";
      setErrorMsg(
        t(`Could not estimate a goal (${detail}).`, `Không thể ước tính mục tiêu (${detail}).`) + overrideHint,
      );
    } finally {
      setLoading(false);
    }
  };

  const handlePlanPacing = (targetTimeMins: number) => {
    setPaceHandoff({
      race_name: estimate?.race_name || raceName,
      distance_km: estimate?.distance_km ?? targetDistance ?? undefined,
      target_time_mins: Math.round(targetTimeMins),
    });
    onClose();
    setIsPaceStrategyOpen(true);
    trackEvent("goal_determiner_to_pace_strategy", {});
  };

  if (!isOpen) return null;

  const goalCards = estimate
    ? ([
        {
          key: "ambitious",
          icon: <Lightning size={20} weight="duotone" />,
          label: t("Ambitious", "Tham vọng"),
          note: t("Everything goes right", "Khi mọi thứ thuận lợi"),
          mins: estimate.goals.ambitious,
        },
        {
          key: "realistic",
          icon: <TrendUp size={20} weight="duotone" />,
          label: t("Realistic", "Thực tế"),
          note: t("Your most likely day", "Khả năng cao nhất"),
          mins: estimate.goals.realistic,
        },
        {
          key: "safe",
          icon: <ShieldCheck size={20} weight="duotone" />,
          label: t("Safe", "An toàn"),
          note: t("Margin for problems", "Dự phòng sự cố"),
          mins: estimate.goals.safe,
        },
      ] as const)
    : [];

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 1000,
        background: "rgba(255, 255, 255, 0.4)",
        backdropFilter: "blur(30px)",
        WebkitBackdropFilter: "blur(30px)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "20px",
      }}
    >
      <div
        style={{
          width: "100%",
          maxWidth: "800px",
          maxHeight: "90vh",
          overflowY: "auto",
          background: "rgba(255, 255, 255, 0.8)",
          border: "1px solid rgba(0,0,0,0.1)",
          borderRadius: "24px",
          padding: "32px",
          position: "relative",
          boxShadow: "0 20px 40px rgba(0,0,0,0.05)",
        }}
      >
        <button
          onClick={onClose}
          style={{ position: "absolute", top: "20px", right: "20px", background: "none", border: "none", cursor: "pointer", color: "var(--text-secondary)" }}
        >
          <XCircle size={32} weight="duotone" />
        </button>

        <h2 style={{ fontSize: "28px", fontWeight: 700, marginBottom: "8px", color: "var(--text-primary)", display: "flex", alignItems: "center", gap: "10px" }}>
          <Crosshair size={32} color="var(--accent-primary)" weight="duotone" />
          Goal Determiner
        </h2>
        <p style={{ color: "var(--text-secondary)", marginBottom: "28px", fontSize: "15px" }}>
          {t(
            "What could you realistically run at your target race? Grounded in the same physics as Pace Strategy, anchored by real field history.",
            "Bạn có thể chạy được bao nhiêu ở giải mục tiêu? Dựa trên cùng mô hình vật lý với Pace Strategy, đối chiếu với kết quả thực tế.",
          )}
        </p>

        {/* Target race */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "16px", marginBottom: "24px" }}>
          <div style={{ ...boxStyle, gridColumn: "1 / -1" }}>
            <label style={labelStyle}>{t("Target race", "Giải mục tiêu")}</label>
            <RaceNameField
              placeholder="e.g. VMM 70k, UTMB"
              value={raceName}
              onChange={setRaceName}
              onMatchChange={setRaceMatch}
              distanceKm={distance}
              lang={lang}
              style={inputStyle}
            />
          </div>
          {/* Always editable: typed values override the KB match */}
          <div style={boxStyle}>
            <label style={labelStyle}>
              {t("Distance (km)", "Cự ly (km)")}
              {raceMatch?.distance_km && !distance ? ` · ${t("from race DB", "theo dữ liệu giải")}` : ""}
            </label>
            <input
              type="number"
              min="1"
              placeholder={raceMatch?.distance_km ? String(raceMatch.distance_km) : "e.g. 70"}
              value={distance}
              onChange={(e) => setDistance(e.target.value)}
              style={inputStyle}
            />
          </div>
          <div style={boxStyle}>
            <label style={labelStyle}>
              {t("Elevation gain (m)", "Tổng leo (m)")}
              {raceMatch?.elevation_gain_m && !gain ? ` · ${t("from race DB", "theo dữ liệu giải")}` : ""}
            </label>
            <input
              type="number"
              min="0"
              placeholder={raceMatch?.elevation_gain_m ? String(raceMatch.elevation_gain_m) : "e.g. 4000"}
              value={gain}
              onChange={(e) => setGain(e.target.value)}
              style={inputStyle}
            />
          </div>
          <div style={boxStyle}>
            <label style={labelStyle}>{t("Weeks until race", "Số tuần tới giải")}</label>
            <input type="number" min="0" max="52" placeholder="e.g. 16" value={weeks} onChange={(e) => setWeeks(e.target.value)} style={inputStyle} />
          </div>
        </div>

        {/* Fitness source */}
        <div style={{ display: "flex", gap: "8px", marginBottom: "16px", flexWrap: "wrap" }}>
          {(["profile", "result", "pace"] as const).map((mode) => {
            const disabled = mode === "profile" && !profileBasePace;
            return (
              <button
                key={mode}
                onClick={() => !disabled && setFitnessMode(mode)}
                disabled={disabled}
                title={disabled ? t("Sign in and set your pace zones first", "Đăng nhập và thiết lập vùng pace trước") : undefined}
                style={{
                  padding: "8px 20px",
                  borderRadius: "20px",
                  border: fitnessMode === mode ? "none" : "1px solid var(--border-color)",
                  background: fitnessMode === mode ? "var(--text-primary)" : "transparent",
                  color: fitnessMode === mode ? "white" : "var(--text-primary)",
                  fontSize: "14px",
                  fontWeight: 600,
                  cursor: disabled ? "not-allowed" : "pointer",
                  opacity: disabled ? 0.45 : 1,
                }}
              >
                {mode === "profile"
                  ? t("My current fitness", "Thể lực hiện tại")
                  : mode === "result"
                    ? t("A recent race result", "Kết quả giải gần đây")
                    : t("My flat pace", "Pace đường bằng")}
              </button>
            );
          })}
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "16px", marginBottom: "24px" }}>
          {fitnessMode === "profile" ? (
            <div style={{ ...boxStyle, gridColumn: "1 / -1" }}>
              <label style={labelStyle}>{t("From your profile", "Từ hồ sơ của bạn")}</label>
              <div style={{ fontSize: "14.5px", color: "var(--text-primary)", fontWeight: 600 }}>
                {t("Aerobic zone pace", "Pace vùng hiếu khí")}: {profileZonePace?.toFixed(1)} min/km →{" "}
                {t("race-effort base", "pace nền khi đua")} {profileBasePace?.toFixed(1)} min/km
              </div>
              <div style={{ fontSize: "11.5px", color: "var(--text-muted)", marginTop: "4px" }}>
                {t(
                  "Same seeding as Pace Strategy. Update your zones in Profile Settings to refine it.",
                  "Cùng cách tính với Pace Strategy. Cập nhật vùng pace trong Cài đặt hồ sơ để chính xác hơn.",
                )}
              </div>
            </div>
          ) : fitnessMode === "result" ? (
            <>
              <div style={{ ...boxStyle, gridColumn: "1 / -1" }}>
                <label style={labelStyle}>{t("Race you finished", "Giải bạn đã hoàn thành")}</label>
                <RaceNameField
                  placeholder={t("e.g. VMM 50k — or leave blank and enter numbers", "vd. VMM 50k — hoặc bỏ trống và nhập số")}
                  value={refRaceName}
                  onChange={setRefRaceName}
                  onMatchChange={setRefMatch}
                  distanceKm={refDistance}
                  lang={lang}
                  style={inputStyle}
                />
              </div>
              <div style={boxStyle}>
                <label style={labelStyle}>
                  {t("Its distance (km)", "Cự ly (km)")}
                  {refMatch?.distance_km && !refDistance ? ` · ${t("from race DB", "theo dữ liệu giải")}` : ""}
                </label>
                <input
                  type="number"
                  min="1"
                  placeholder={refMatch?.distance_km ? String(refMatch.distance_km) : "e.g. 50"}
                  value={refDistance}
                  onChange={(e) => setRefDistance(e.target.value)}
                  style={inputStyle}
                />
              </div>
              <div style={boxStyle}>
                <label style={labelStyle}>
                  {t("Its elevation gain (m)", "Tổng leo (m)")}
                  {refMatch?.elevation_gain_m && !refGain ? ` · ${t("from race DB", "theo dữ liệu giải")}` : ""}
                </label>
                <input
                  type="number"
                  min="0"
                  placeholder={refMatch?.elevation_gain_m ? String(refMatch.elevation_gain_m) : "e.g. 2500"}
                  value={refGain}
                  onChange={(e) => setRefGain(e.target.value)}
                  style={inputStyle}
                />
              </div>
              <div style={boxStyle}>
                <label style={labelStyle}>{t("Your finish time", "Thời gian hoàn thành")}</label>
                <input type="text" placeholder="e.g. 7:30:00" value={refTime} onChange={(e) => setRefTime(e.target.value)} style={inputStyle} />
              </div>
            </>
          ) : (
            <div style={boxStyle}>
              <label style={labelStyle}>{t("Flat pace (min/km)", "Pace đường bằng (min/km)")}</label>
              <input type="number" step="0.1" min="3" max="15" placeholder="e.g. 6.5" value={flatPace} onChange={(e) => setFlatPace(e.target.value)} style={inputStyle} />
            </div>
          )}
        </div>

        <button
          onClick={handleEstimate}
          disabled={loading || !canEstimate}
          style={{
            width: "100%",
            padding: "16px",
            borderRadius: "16px",
            background: "var(--text-primary)",
            color: "white",
            fontSize: "16px",
            fontWeight: 600,
            border: "none",
            cursor: loading || !canEstimate ? "not-allowed" : "pointer",
            opacity: loading || !canEstimate ? 0.6 : 1,
            transition: "0.2s",
          }}
        >
          {loading ? t("Estimating…", "Đang ước tính…") : t("Estimate my goal", "Ước tính mục tiêu")}
        </button>

        {errorMsg && (
          <div style={{ color: "var(--accent-alert, #ef4444)", fontSize: "13px", padding: "10px", background: "rgba(239,68,68,0.08)", borderRadius: "10px", marginTop: "16px" }}>
            {errorMsg}
          </div>
        )}

        {estimate && (
          <div style={{ marginTop: "28px", paddingTop: "24px", borderTop: "1px solid rgba(0,0,0,0.1)" }}>
            <p style={{ fontSize: "13.5px", color: "var(--text-secondary)", marginBottom: "16px" }}>
              {t("Current predicted time on", "Dự đoán hiện tại tại")}{" "}
              <strong>
                {estimate.race_name || `${Math.round(estimate.distance_km)}k / ${Math.round(estimate.elevation_gain_m)}m D+`}
              </strong>
              : <strong style={{ fontFamily: "var(--font-mono)" }}>{formatDurationHM(estimate.predicted_time_mins)}</strong>
              {estimate.improvement_pct > 0 &&
                ` · ${t("with your training block", "sau chu kỳ tập luyện")}: ${formatDurationHM(estimate.adjusted_time_mins)} (−${estimate.improvement_pct}%)`}
              {` · ${t("base flat pace", "pace nền")} ${estimate.base_flat_pace_min_km.toFixed(1)} min/km`}
            </p>

            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "12px" }}>
              {goalCards.map((g) => (
                <div key={g.key} className="snow-glass" style={{ borderRadius: "16px", padding: "16px", border: "1px solid rgba(0,0,0,0.06)" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "6px", color: "var(--accent-primary)", fontWeight: 700, fontSize: "13px", textTransform: "uppercase", letterSpacing: "0.5px" }}>
                    {g.icon} {g.label}
                  </div>
                  <div style={{ fontFamily: "var(--font-mono)", fontSize: "28px", fontWeight: 700, color: "var(--text-primary)", margin: "8px 0 2px" }}>
                    {formatDurationHM(g.mins)}
                  </div>
                  <div style={{ fontSize: "11.5px", color: "var(--text-muted)", marginBottom: "2px" }}>
                    {(() => {
                      const paceSecs = Math.round((g.mins / estimate.distance_km) * 60);
                      return `${Math.floor(paceSecs / 60)}:${String(paceSecs % 60).padStart(2, "0")}/km ${t("average", "trung bình")}`;
                    })()}
                  </div>
                  <div style={{ fontSize: "11.5px", color: "var(--text-muted)", marginBottom: "10px" }}>{g.note}</div>
                  <button
                    onClick={() => handlePlanPacing(g.mins)}
                    style={{ width: "100%", padding: "8px", borderRadius: "10px", background: "transparent", border: "1px solid var(--border-color)", color: "var(--text-primary)", fontSize: "12.5px", fontWeight: 600, cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center", gap: "5px" }}
                  >
                    <Gauge size={15} /> {t("Plan pacing", "Lên pacing")}
                  </button>
                </div>
              ))}
            </div>

            <div style={{ marginTop: "16px", background: "rgba(0,0,0,0.02)", border: "1px dashed rgba(0,0,0,0.1)", borderRadius: "14px", padding: "14px", fontSize: "12px", color: "var(--text-secondary)", lineHeight: 1.55 }}>
              <div style={{ fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.5px", fontSize: "11px", color: "var(--text-primary)", marginBottom: "6px" }}>
                {t("How this was computed", "Cách tính")}
              </div>
              <div>
                {t("Physics model", "Mô hình vật lý")}: {formatDurationHM(estimate.predicted_time_mins)}{" "}
                {t("at a", "với")} {estimate.base_flat_pace_min_km.toFixed(1)} min/km{" "}
                {t("flat base pace over", "pace nền trên")} {Math.round(estimate.distance_km)}k /{" "}
                {Math.round(estimate.elevation_gain_m)}m D+ ({t("Minetti grade curve + fatigue", "đường cong Minetti + mệt mỏi")}).
              </div>
              {estimate.improvement_pct > 0 && (
                <div>
                  {t("Training block", "Chu kỳ tập luyện")}: −{estimate.improvement_pct}%{" "}
                  {t("plausible gain before race day", "cải thiện khả thi trước ngày đua")} →{" "}
                  {formatDurationHM(estimate.adjusted_time_mins)}.
                </div>
              )}
              <div>
                {t(
                  "Ambitious = −5% (everything goes right) · Safe = +8% (banked margin for problems).",
                  "Tham vọng = −5% (mọi thứ thuận lợi) · An toàn = +8% (dự phòng sự cố).",
                )}
              </div>
              {estimate.rank_transfer_mins != null && (
                <div>
                  {t("Cross-check — field history puts a runner of your rank at", "Đối chiếu — theo lịch sử giải, thứ hạng của bạn tương ứng")}{" "}
                  ~{formatDurationHM(estimate.rank_transfer_mins)}.
                </div>
              )}
              {estimate.benchmarks?.length ? (
                <div>
                  {t("Field", "Giải")} {estimate.benchmarks[0].year}: {estimate.benchmarks[0].finishers}{" "}
                  {t("finishers", "người hoàn thành")}
                  {estimate.benchmarks[0].winner_time ? ` · ${t("winner", "vô địch")} ${estimate.benchmarks[0].winner_time}` : ""}
                  {estimate.benchmarks[0].conditions_note ? ` · ${estimate.benchmarks[0].conditions_note}` : ""}.
                </div>
              ) : null}
            </div>
            <p style={{ fontSize: "11.5px", color: "var(--text-muted)", marginTop: "8px" }}>
              {t(
                "Same engine as Pace Strategy — the two tools will never disagree about the same runner on the same course.",
                "Cùng một mô hình với Pace Strategy — hai công cụ luôn thống nhất về cùng một runner trên cùng một đường đua.",
              )}
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
