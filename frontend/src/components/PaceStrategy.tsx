/* eslint-disable @typescript-eslint/no-explicit-any */
"use client";

import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useAnalytics } from "@/hooks/useAnalytics";
import { useAppContext } from "@/contexts/AppContext";
import { RaceMatch } from "@/hooks/useRaceMatch";
import { RaceNameField } from "@/components/RaceNameField";
import {
  CourseCheckpoint,
  PacedCheckpoint,
  addClockEtas,
  formatDurationHM,
  parsePaceToMinutes,
  parseDurationToMinutes,
  sliderBoundsMins,
  synthesizeCourse,
  tempBucket,
} from "@/lib/paceStrategy";
import {
  Gauge,
  XCircle,
  UploadSimple,
  MapPin,
  PersonSimpleHike,
  Clock,
  MoonStars,
  Thermometer,
  Fire,
  BowlFood,
  Sneaker,
} from "@phosphor-icons/react";

interface PaceStrategyProps {
  isOpen: boolean;
  onClose: () => void;
  lang: "en" | "vi";
  user?: any;
  activePlan?: any;
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

/** Two stacked panels sharing the distance axis: elevation area, pace steps. */
function ProfileChart({ paced, lang }: { paced: PacedCheckpoint[]; lang: "en" | "vi" }) {
  const [hoverIdx, setHoverIdx] = useState<number | null>(null);
  const width = 720;
  const elevH = 120;
  const paceH = 90;
  const padL = 44;
  const padR = 12;
  const gap = 26;
  const height = elevH + paceH + gap + 30;

  const rows = paced.filter((cp) => cp.distance_km > 0 || paced.indexOf(cp) === 0);
  if (rows.length < 2) return null;

  const maxDist = rows[rows.length - 1].distance_km;
  const elevs = rows.map((r) => r.elevation_m);
  const minElev = Math.min(...elevs);
  const maxElev = Math.max(...elevs, minElev + 10);
  const paces = rows.slice(1).map((r) => parsePaceToMinutes(r.target_pace) ?? 0);
  const maxPace = Math.max(...paces, 1);
  const minPace = Math.min(...paces);

  const x = (km: number) => padL + (km / maxDist) * (width - padL - padR);
  const yElev = (e: number) => 10 + (1 - (e - minElev) / (maxElev - minElev)) * (elevH - 10);
  const paceTop = elevH + gap;
  const yPace = (p: number) =>
    paceTop + (1 - (p - minPace * 0.9) / (maxPace - minPace * 0.9 || 1)) * (paceH - 10);

  const elevPath =
    `M ${x(rows[0].distance_km)} ${yElev(rows[0].elevation_m)} ` +
    rows.slice(1).map((r) => `L ${x(r.distance_km)} ${yElev(r.elevation_m)}`).join(" ");
  const elevArea = `${elevPath} L ${x(maxDist)} ${elevH + 10} L ${x(rows[0].distance_km)} ${elevH + 10} Z`;

  // step line: pace of segment i applies from checkpoint i-1 to checkpoint i
  const paceSteps = rows.slice(1).map((r, i) => {
    const x0 = x(rows[i].distance_km);
    const x1 = x(r.distance_km);
    const y = yPace(paces[i]);
    return { x0, x1, y, idx: i + 1 };
  });

  const hover = hoverIdx !== null ? rows[hoverIdx] : null;

  return (
    <div style={{ overflowX: "auto" }}>
      <svg
        viewBox={`0 0 ${width} ${height}`}
        style={{ width: "100%", minWidth: "480px", display: "block" }}
        onMouseLeave={() => setHoverIdx(null)}
      >
        {/* elevation panel */}
        <text x={padL} y={8} fontSize={9} fill="var(--text-muted)" fontWeight={600}>
          {lang === "en" ? "ELEVATION (m)" : "ĐỘ CAO (m)"}
        </text>
        <path d={elevArea} fill="var(--accent-primary)" opacity={0.14} />
        <path d={elevPath} fill="none" stroke="var(--accent-primary)" strokeWidth={2} />
        <text x={padL - 6} y={yElev(maxElev) + 4} fontSize={9} fill="var(--text-muted)" textAnchor="end">
          {Math.round(maxElev)}
        </text>
        <text x={padL - 6} y={elevH + 8} fontSize={9} fill="var(--text-muted)" textAnchor="end">
          {Math.round(minElev)}
        </text>

        {/* pace panel */}
        <text x={padL} y={paceTop - 6} fontSize={9} fill="var(--text-muted)" fontWeight={600}>
          {lang === "en" ? "TARGET PACE (min/km)" : "PACE MỤC TIÊU (min/km)"}
        </text>
        {paceSteps.map((s) => (
          <line
            key={s.idx}
            x1={s.x0}
            x2={s.x1}
            y1={s.y}
            y2={s.y}
            stroke={rows[s.idx].effort === "hike" ? "var(--text-primary)" : "var(--accent-primary)"}
            strokeWidth={3}
            strokeLinecap="round"
          />
        ))}
        <text x={padL - 6} y={yPace(maxPace) + 4} fontSize={9} fill="var(--text-muted)" textAnchor="end">
          {maxPace.toFixed(1)}
        </text>
        <text x={padL - 6} y={yPace(minPace) + 4} fontSize={9} fill="var(--text-muted)" textAnchor="end">
          {minPace.toFixed(1)}
        </text>

        {/* x axis */}
        <line x1={padL} x2={width - padR} y1={paceTop + paceH} y2={paceTop + paceH} stroke="var(--border-color)" />
        {[0, 0.25, 0.5, 0.75, 1].map((f) => (
          <text
            key={f}
            x={x(maxDist * f)}
            y={paceTop + paceH + 14}
            fontSize={9}
            fill="var(--text-muted)"
            textAnchor="middle"
          >
            {Math.round(maxDist * f)}k
          </text>
        ))}

        {/* hover layer */}
        {hover && hoverIdx !== null && hoverIdx > 0 && (
          <g pointerEvents="none">
            <line
              x1={x(hover.distance_km)}
              x2={x(hover.distance_km)}
              y1={10}
              y2={paceTop + paceH}
              stroke="var(--text-muted)"
              strokeDasharray="3 3"
            />
            <rect
              x={Math.min(x(hover.distance_km) + 8, width - 168)}
              y={14}
              width={160}
              height={44}
              rx={8}
              fill="var(--bg-primary, white)"
              stroke="var(--border-color)"
            />
            <text x={Math.min(x(hover.distance_km) + 16, width - 160)} y={31} fontSize={10} fontWeight={700} fill="var(--text-primary)">
              {hover.name} · {hover.distance_km}k · {hover.elevation_m}m
            </text>
            <text x={Math.min(x(hover.distance_km) + 16, width - 160)} y={48} fontSize={10} fill="var(--text-secondary)">
              {hover.target_pace}/km · {hover.split_time}
              {hover.effort === "hike" ? (lang === "en" ? " · hike" : " · leo bộ") : ""}
            </text>
          </g>
        )}
        {rows.map((r, i) => (
          <rect
            key={i}
            x={i === 0 ? padL : (x(rows[i - 1].distance_km) + x(r.distance_km)) / 2}
            y={0}
            width={
              i === 0
                ? (x(rows[1].distance_km) - padL) / 2
                : (x(rows[Math.min(i + 1, rows.length - 1)].distance_km) - x(rows[i - 1].distance_km)) / 2
            }
            height={paceTop + paceH}
            fill="transparent"
            onMouseEnter={() => setHoverIdx(i)}
          />
        ))}
      </svg>
      <div style={{ display: "flex", gap: "16px", fontSize: "11px", color: "var(--text-secondary)", padding: "4px 0 0 4px" }}>
        <span style={{ display: "flex", alignItems: "center", gap: "4px" }}>
          <span style={{ width: 14, height: 3, background: "var(--accent-primary)", borderRadius: 2, display: "inline-block" }} />
          {lang === "en" ? "Run" : "Chạy"}
        </span>
        <span style={{ display: "flex", alignItems: "center", gap: "4px" }}>
          <span style={{ width: 14, height: 3, background: "var(--text-primary)", borderRadius: 2, display: "inline-block" }} />
          {lang === "en" ? "Hike" : "Leo bộ"}
        </span>
      </div>
    </div>
  );
}

export const PaceStrategy: React.FC<PaceStrategyProps> = ({ isOpen, onClose, lang, user, activePlan }) => {
  const [courseSource, setCourseSource] = useState<"gpx" | "race">("race");
  const [raceName, setRaceName] = useState("");
  const [raceMatch, setRaceMatch] = useState<RaceMatch | null>(null);
  const [manualDistance, setManualDistance] = useState("");
  const [manualGain, setManualGain] = useState("");

  const [gpxCheckpoints, setGpxCheckpoints] = useState<CourseCheckpoint[]>([]);
  const [gpxFileName, setGpxFileName] = useState("");
  const [gpxLoading, setGpxLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");

  const [targetTimeMins, setTargetTimeMins] = useState<number | null>(null);
  const [splitBias, setSplitBias] = useState(0);
  const [startClock, setStartClock] = useState("");
  const [raceDate, setRaceDate] = useState("");
  const [weightKg, setWeightKg] = useState("68");
  const [splitInterval, setSplitInterval] = useState<1 | 5 | 10>(1);
  const [restMins, setRestMins] = useState<Record<number, number>>({});

  const [paced, setPaced] = useState<PacedCheckpoint[]>([]);
  const [pacingLoading, setPacingLoading] = useState(false);

  interface RaceResult {
    year: number;
    finishers?: number;
    winner_time?: string;
    winner_time_women?: string;
    conditions_note?: string;
    percentiles?: Record<string, string>;
  }
  const [benchmarks, setBenchmarks] = useState<RaceResult[]>([]);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const { trackEvent } = useAnalytics();
  const { paceHandoff, setPaceHandoff, setIsNutritionLabOpen, setIsGearVaultOpen } = useAppContext();

  // Goal Determiner hands a race + target time into the slider
  useEffect(() => {
    if (!isOpen || !paceHandoff?.target_time_mins) return;
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setCourseSource("race");
    if (paceHandoff.race_name) setRaceName(paceHandoff.race_name);
    if (paceHandoff.distance_km) setManualDistance(String(paceHandoff.distance_km));
    setTargetTimeMins(paceHandoff.target_time_mins);
    setRestMins({});
    setPaceHandoff(null);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen]);

  // Weather needs per-checkpoint coordinates, which only GPX courses have.
  const raceStartIso =
    courseSource === "gpx" && raceDate ? `${raceDate}T${startClock || "05:00"}` : null;

  // Course checkpoints from whichever source is active. Typed numbers beat
  // the KB match — some races change their course every year.
  const checkpoints = useMemo<CourseCheckpoint[]>(() => {
    if (courseSource === "gpx") return gpxCheckpoints;
    const dist = parseFloat(manualDistance) || raceMatch?.distance_km || 0;
    if (dist <= 0) return [];
    const gain = parseFloat(manualGain) || raceMatch?.elevation_gain_m || 0;
    return synthesizeCourse(dist, gain, gain, 0, splitInterval);
  }, [courseSource, gpxCheckpoints, raceMatch, manualDistance, manualGain, splitInterval]);

  const courseStats = useMemo(() => {
    if (checkpoints.length < 2) return null;
    const dist = checkpoints[checkpoints.length - 1].distance_meters / 1000;
    const gain = checkpoints.reduce((s, c) => s + (c.segment_gain_meters || 0), 0);
    return { dist, gain };
  }, [checkpoints]);

  const bounds = useMemo(
    () => (courseStats ? sliderBoundsMins(courseStats.dist, courseStats.gain) : null),
    [courseStats],
  );

  // Finish-time default seeded from stored fitness (aerobic zone pace); the
  // user's slider choice wins while it stays within the course's bounds.
  const effectiveTargetMins = useMemo(() => {
    if (!courseStats || !bounds) return null;
    if (targetTimeMins !== null && targetTimeMins >= bounds.min && targetTimeMins <= bounds.max) {
      return targetTimeMins;
    }
    const zonePace =
      parsePaceToMinutes(user?.zone2_pace_max || "") ?? parsePaceToMinutes(user?.zone2_pace_min || "") ?? 7.0;
    // race effort ≈ a bit quicker than easy aerobic pace on flat equivalents
    const seeded = Math.round((courseStats.dist + courseStats.gain / 100) * zonePace * 0.95);
    return Math.min(Math.max(seeded, bounds.min), bounds.max);
  }, [courseStats, bounds, targetTimeMins, user]);

  const recalc = useCallback(
    (timeMins: number, bias: number, cps: CourseCheckpoint[], startIso: string | null, weight: string) => {
      if (cps.length < 2) return;
      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;
      setPacingLoading(true);
      fetch(`${getBaseUrl()}/api/coach/calculate-pacing`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          checkpoints: cps,
          target_time_mins: timeMins,
          split_bias: bias,
          race_start_iso: startIso,
          runner_weight_kg: parseFloat(weight) || null,
        }),
        signal: controller.signal,
      })
        .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`))))
        .then((rows: PacedCheckpoint[]) => {
          setPaced(rows);
          setErrorMsg("");
        })
        .catch((err) => {
          if (err?.name === "AbortError") return; // superseded by a newer request
          const detail = `${err?.message || "network error"} · ${getBaseUrl()}`;
          const overrideHint = localStorage.getItem("UPHILL_API_URL_OVERRIDE")
            ? lang === "en"
              ? " An ?api= override is active — visit ?api=clear to use the default backend."
              : " Đang có ghi đè ?api= — truy cập ?api=clear để dùng backend mặc định."
            : "";
          setErrorMsg(
            (lang === "en"
              ? `Failed to calculate the plan (${detail}).`
              : `Không thể tính toán kế hoạch (${detail}).`) + overrideHint,
          );
        })
        .finally(() => {
          if (abortRef.current === controller) setPacingLoading(false);
        });
    },
    [lang],
  );

  // Debounced recalc whenever inputs move
  useEffect(() => {
    if (!isOpen || effectiveTargetMins === null || checkpoints.length < 2) return;
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(
      () => recalc(effectiveTargetMins, splitBias, checkpoints, raceStartIso, weightKg),
      250,
    );
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [isOpen, effectiveTargetMins, splitBias, checkpoints, raceStartIso, weightKg, recalc]);

  // Curated past-results benchmarks for the picked race (winner times, field size)
  useEffect(() => {
    if (courseSource !== "race" || !raceMatch?.distance_km) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setBenchmarks([]);
      return;
    }
    const controller = new AbortController();
    const params = new URLSearchParams({ name: raceMatch.race_name, distance_km: String(raceMatch.distance_km) });
    fetch(`${getBaseUrl()}/api/coach/pace-strategy/benchmarks?${params.toString()}`, { signal: controller.signal })
      .then((r) => (r.ok ? r.json() : { matched: false }))
      .then((data) => setBenchmarks(data.matched ? data.results : []))
      .catch(() => setBenchmarks([]));
    return () => controller.abort();
  }, [courseSource, raceMatch]);

  const handleGpxFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setGpxLoading(true);
    setErrorMsg("");
    setGpxFileName(file.name);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const response = await fetch(`${getBaseUrl()}/api/parser/gpx`, { method: "POST", body: formData });
      if (!response.ok) throw new Error(await response.text());
      const result = await response.json();
      const cps: CourseCheckpoint[] = [...(result.checkpoints || [])];
      if (cps.length > 0 && cps[0].distance_meters > 0) {
        // GPX checkpoints start at the first split marker; anchor the course at km 0
        // so the opening segment gets a pace and the chart spans the whole route.
        const first = cps[0];
        cps.unshift({
          name: "Start",
          distance_meters: 0,
          elevation_meters:
            (first.elevation_meters || 0) - (first.segment_gain_meters || 0) + (first.segment_loss_meters || 0),
          segment_gain_meters: 0,
          segment_loss_meters: 0,
        });
      }
      setGpxCheckpoints(cps);
      setPaced([]);
      setRestMins({});
      trackEvent("pace_strategy_gpx_uploaded", { checkpoints: (result.checkpoints || []).length });
    } catch {
      setErrorMsg(lang === "en" ? "Could not parse that GPX file." : "Không thể phân tích tệp GPX.");
      setGpxCheckpoints([]);
    } finally {
      setGpxLoading(false);
    }
  };

  const hasWeather = paced.some((p) => p.temp_c != null);
  const restArray = paced.map((_, idx) => restMins[idx] || 0);

  const handleHandoff = (target: "nutrition" | "gear") => {
    const last = paced[paced.length - 1];
    const totalRestMins = restArray.reduce((s, r) => s + r, 0);
    const peak = hasWeather ? Math.max(...paced.map((p) => p.temp_c ?? -99)) : null;
    setPaceHandoff({
      duration_hours: last ? Math.round(((last.cumulative_time_mins + totalRestMins) / 60) * 10) / 10 : undefined,
      weather_temp: tempBucket(peak),
      race_name: courseSource === "race" ? raceName : gpxFileName.replace(/\.gpx$/i, ""),
      distance_label: courseStats ? `${Math.round(courseStats.dist)}k` : undefined,
    });
    onClose();
    if (target === "nutrition") setIsNutritionLabOpen(true);
    else setIsGearVaultOpen(true);
    trackEvent("pace_strategy_handoff", { target });
  };
  const etas = paced.length > 0 ? addClockEtas(paced, restArray, startClock || undefined) : [];
  const totalRest = restArray.reduce((s, r) => s + r, 0);
  const finishMins = paced.length > 0 ? paced[paced.length - 1].cumulative_time_mins + totalRest : null;

  if (!isOpen) return null;

  const t = (en: string, vi: string) => (lang === "en" ? en : vi);

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
          maxWidth: "860px",
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
          <Gauge size={32} color="var(--accent-primary)" weight="duotone" />
          Pace Strategy
        </h2>
        <p style={{ color: "var(--text-secondary)", marginBottom: "28px", fontSize: "15px" }}>
          {t(
            "Pick a finish time — the engine distributes effort across every climb and descent, grounded in the physiology of grade.",
            "Chọn thời gian về đích — công cụ sẽ phân bổ sức lực trên từng đoạn leo và đổ dốc theo sinh lý học của độ dốc.",
          )}
        </p>

        {/* Course source */}
        <div style={{ display: "flex", gap: "8px", marginBottom: "16px" }}>
          {(["race", "gpx"] as const).map((mode) => (
            <button
              key={mode}
              onClick={() => {
                setCourseSource(mode);
                setPaced([]);
                setRestMins({});
              }}
              style={{
                padding: "8px 20px",
                borderRadius: "20px",
                border: courseSource === mode ? "none" : "1px solid var(--border-color)",
                background: courseSource === mode ? "var(--text-primary)" : "transparent",
                color: courseSource === mode ? "white" : "var(--text-primary)",
                fontSize: "14px",
                fontWeight: 600,
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                gap: "6px",
              }}
            >
              {mode === "race" ? <MapPin size={16} /> : <UploadSimple size={16} />}
              {mode === "race" ? t("Pick a race", "Chọn giải chạy") : t("Upload GPX", "Tải lên GPX")}
            </button>
          ))}
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "16px", marginBottom: "20px" }}>
          {courseSource === "race" && (
            <>
              <div style={{ ...boxStyle, gridColumn: "1 / -1" }}>
                <label style={labelStyle}>{t("Race", "Giải chạy")}</label>
                <RaceNameField
                  placeholder="e.g. VMM 70k, UTMB"
                  value={raceName}
                  onChange={setRaceName}
                  onMatchChange={(m) => {
                    setRaceMatch(m);
                    setRestMins({});
                  }}
                  distanceKm={manualDistance}
                  lang={lang}
                  style={{ width: "100%", background: "transparent", border: "none", fontSize: "16px", fontWeight: 600, color: "var(--text-primary)", outline: "none" }}
                />
              </div>
              {/* Always editable: typed values override the KB match, since
                  some races change their course every year */}
              <div style={boxStyle}>
                <label style={labelStyle}>
                  {t("Distance (km)", "Cự ly (km)")}
                  {raceMatch?.distance_km && !manualDistance ? ` · ${t("from race DB", "theo dữ liệu giải")}` : ""}
                </label>
                <input
                  type="number"
                  min="1"
                  placeholder={raceMatch?.distance_km ? String(raceMatch.distance_km) : "e.g. 70"}
                  value={manualDistance}
                  onChange={(e) => {
                    setManualDistance(e.target.value);
                    setRestMins({});
                  }}
                  style={{ width: "100%", background: "transparent", border: "none", fontSize: "16px", fontWeight: 600, color: "var(--text-primary)", outline: "none" }}
                />
              </div>
              <div style={boxStyle}>
                <label style={labelStyle}>
                  {t("Elevation gain (m)", "Tổng leo (m)")}
                  {raceMatch?.elevation_gain_m && !manualGain ? ` · ${t("from race DB", "theo dữ liệu giải")}` : ""}
                </label>
                <input
                  type="number"
                  min="0"
                  placeholder={raceMatch?.elevation_gain_m ? String(raceMatch.elevation_gain_m) : "e.g. 4000"}
                  value={manualGain}
                  onChange={(e) => {
                    setManualGain(e.target.value);
                    setRestMins({});
                  }}
                  style={{ width: "100%", background: "transparent", border: "none", fontSize: "16px", fontWeight: 600, color: "var(--text-primary)", outline: "none" }}
                />
              </div>
            </>
          )}

          {courseSource === "gpx" && (
            <div
              style={{ ...boxStyle, gridColumn: "1 / -1", textAlign: "center", cursor: "pointer" }}
              onClick={() => fileInputRef.current?.click()}
            >
              <UploadSimple size={28} color="var(--accent-primary)" weight="duotone" />
              <div style={{ fontSize: "14px", fontWeight: 600, color: "var(--text-primary)" }}>
                {gpxLoading
                  ? t("Parsing route…", "Đang phân tích tuyến đường…")
                  : gpxFileName || t("Upload a course GPX", "Tải lên tệp GPX đường chạy")}
              </div>
              <input type="file" ref={fileInputRef} onChange={handleGpxFile} accept=".gpx" style={{ display: "none" }} />
            </div>
          )}
        </div>

        {courseStats && bounds && effectiveTargetMins !== null && (
          <>
            <div style={{ ...boxStyle, marginBottom: "16px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
                <label style={labelStyle}>
                  {t("Target finish time", "Thời gian về đích mục tiêu")} · {Math.round(courseStats.dist)}k / {Math.round(courseStats.gain)}m D+
                </label>
                <span style={{ fontFamily: "var(--font-mono)", fontSize: "24px", fontWeight: 700, color: "var(--accent-primary)" }}>
                  {formatDurationHM(effectiveTargetMins)}
                </span>
              </div>
              <input
                type="range"
                min={bounds.min}
                max={bounds.max}
                step={bounds.step}
                value={effectiveTargetMins}
                onChange={(e) => setTargetTimeMins(parseInt(e.target.value, 10))}
                style={{ width: "100%", accentColor: "var(--accent-primary)" }}
              />
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: "11px", color: "var(--text-muted)" }}>
                <span>{formatDurationHM(bounds.min)}</span>
                <span>{formatDurationHM(bounds.max)}</span>
              </div>
              {benchmarks.length > 0 && (
                <div style={{ marginTop: "10px", borderTop: "1px dashed var(--border-color)", paddingTop: "8px" }}>
                  <div style={{ position: "relative", height: "18px" }}>
                    {[
                      { label: t("Winner", "Vô địch"), time: benchmarks[0].winner_time },
                      { label: t("Winner (F)", "Vô địch nữ"), time: benchmarks[0].winner_time_women },
                      ...Object.entries(benchmarks[0].percentiles || {}).map(([p, v]) => ({
                        label: p.toUpperCase(),
                        time: v,
                      })),
                    ]
                      .map((mk) => ({ ...mk, mins: mk.time ? parseDurationToMinutes(mk.time) : null }))
                      .filter((mk) => mk.mins !== null && mk.mins >= bounds.min && mk.mins <= bounds.max)
                      .map((mk, i) => (
                        <div
                          key={i}
                          title={`${mk.label}: ${mk.time}`}
                          style={{
                            position: "absolute",
                            left: `${(((mk.mins as number) - bounds.min) / (bounds.max - bounds.min)) * 100}%`,
                            transform: "translateX(-50%)",
                            fontSize: "9.5px",
                            fontWeight: 700,
                            color: "var(--accent-primary)",
                            textAlign: "center",
                            lineHeight: 1.1,
                          }}
                        >
                          ▲<br />
                          {mk.label}
                        </div>
                      ))}
                  </div>
                  <div style={{ fontSize: "10.5px", color: "var(--text-muted)", marginTop: "2px" }}>
                    {benchmarks[0].year}: {benchmarks[0].finishers} {t("finishers", "người hoàn thành")}
                    {benchmarks[0].winner_time ? ` · ${t("winner", "vô địch")} ${benchmarks[0].winner_time}` : ""}
                    {benchmarks[0].conditions_note ? ` · ${benchmarks[0].conditions_note}` : ""}
                  </div>
                </div>
              )}
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "16px", marginBottom: "20px" }}>
              <div style={boxStyle}>
                <label style={labelStyle}>{t("Split strategy", "Chiến thuật chia sức")}</label>
                <input
                  type="range"
                  min={-1}
                  max={1}
                  step={0.1}
                  value={splitBias}
                  onChange={(e) => setSplitBias(parseFloat(e.target.value))}
                  style={{ width: "100%", accentColor: "var(--accent-primary)" }}
                />
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: "11px", color: "var(--text-muted)" }}>
                  <span>{t("Fast start", "Xuất phát nhanh")}</span>
                  <span>{t("Even", "Đều")}</span>
                  <span>{t("Fast finish", "Về đích nhanh")}</span>
                </div>
                <div style={{ fontSize: "10.5px", color: "var(--text-muted)", marginTop: "6px" }}>
                  {courseStats.gain / courseStats.dist < 15
                    ? t(
                        "Tip: flat courses reward a slightly negative split — start conservative.",
                        "Gợi ý: đường bằng phẳng nên chia sức âm nhẹ — xuất phát thận trọng.",
                      )
                    : t(
                        "Tip: on mountain courses hold even effort and let terrain set the pace.",
                        "Gợi ý: đường núi nên giữ sức đều, để địa hình quyết định pace.",
                      )}
                </div>
              </div>
              <div style={boxStyle}>
                <label style={labelStyle}>{t("Race start time (optional)", "Giờ xuất phát (tùy chọn)")}</label>
                <input
                  type="time"
                  value={startClock}
                  onChange={(e) => setStartClock(e.target.value)}
                  style={{ width: "100%", background: "transparent", border: "none", fontSize: "16px", fontWeight: 600, color: "var(--text-primary)", outline: "none" }}
                />
              </div>
              {courseSource === "race" && (
                <div style={boxStyle}>
                  <label style={labelStyle}>{t("Split every", "Chia mỗi")}</label>
                  <div style={{ display: "flex", gap: "6px" }}>
                    {([1, 5, 10] as const).map((iv) => (
                      <button
                        key={iv}
                        onClick={() => {
                          setSplitInterval(iv);
                          setRestMins({});
                        }}
                        style={{
                          padding: "6px 14px",
                          borderRadius: "16px",
                          border: splitInterval === iv ? "none" : "1px solid var(--border-color)",
                          background: splitInterval === iv ? "var(--text-primary)" : "transparent",
                          color: splitInterval === iv ? "white" : "var(--text-primary)",
                          fontSize: "13px",
                          fontWeight: 600,
                          cursor: "pointer",
                        }}
                      >
                        {iv}k
                      </button>
                    ))}
                  </div>
                </div>
              )}
              <div style={boxStyle}>
                <label style={labelStyle}>{t("Runner weight (kg)", "Cân nặng (kg)")}</label>
                <input
                  type="number"
                  min="30"
                  max="150"
                  value={weightKg}
                  onChange={(e) => setWeightKg(e.target.value)}
                  style={{ width: "100%", background: "transparent", border: "none", fontSize: "16px", fontWeight: 600, color: "var(--text-primary)", outline: "none" }}
                />
              </div>
              {courseSource === "gpx" && (
                <div style={boxStyle}>
                  <label style={labelStyle}>{t("Race date (for weather)", "Ngày đua (dự báo thời tiết)")}</label>
                  <input
                    type="date"
                    value={raceDate}
                    onChange={(e) => setRaceDate(e.target.value)}
                    style={{ width: "100%", background: "transparent", border: "none", fontSize: "16px", fontWeight: 600, color: "var(--text-primary)", outline: "none" }}
                  />
                  <div style={{ fontSize: "10.5px", color: "var(--text-muted)", marginTop: "4px" }}>
                    {t("Forecast covers ~16 days ahead", "Dự báo trong khoảng ~16 ngày tới")}
                  </div>
                </div>
              )}
            </div>
          </>
        )}

        {errorMsg && (
          <div style={{ color: "var(--accent-alert, #ef4444)", fontSize: "13px", padding: "10px", background: "rgba(239,68,68,0.08)", borderRadius: "10px", marginBottom: "16px" }}>
            {errorMsg}
          </div>
        )}

        {paced.length > 1 && (
          <div style={{ opacity: pacingLoading ? 0.5 : 1, transition: "opacity 0.2s" }}>
            {/* headline */}
            <div style={{ display: "flex", flexWrap: "wrap", gap: "8px", marginBottom: "16px" }}>
              <span style={{ display: "flex", alignItems: "center", gap: "4px", background: "rgba(0,0,0,0.04)", padding: "6px 12px", borderRadius: "10px", fontSize: "13px", fontWeight: 600, color: "var(--text-secondary)" }}>
                <Clock size={15} /> {t("Moving", "Di chuyển")}: {formatDurationHM(paced[paced.length - 1].cumulative_time_mins)}
              </span>
              {totalRest > 0 && (
                <span style={{ display: "flex", alignItems: "center", gap: "4px", background: "rgba(0,0,0,0.04)", padding: "6px 12px", borderRadius: "10px", fontSize: "13px", fontWeight: 600, color: "var(--text-secondary)" }}>
                  {t("With rest", "Kèm nghỉ")}: {finishMins !== null ? formatDurationHM(finishMins) : "—"}
                </span>
              )}
              <span style={{ display: "flex", alignItems: "center", gap: "4px", background: "rgba(0,0,0,0.04)", padding: "6px 12px", borderRadius: "10px", fontSize: "13px", fontWeight: 600, color: "var(--text-secondary)" }}>
                <PersonSimpleHike size={15} /> {t("Hike sections", "Đoạn leo bộ")}: {paced.filter((p) => p.effort === "hike").length}
              </span>
              {(paced[paced.length - 1].energy_kcal ?? 0) > 0 && (
                <span style={{ display: "flex", alignItems: "center", gap: "4px", background: "rgba(0,0,0,0.04)", padding: "6px 12px", borderRadius: "10px", fontSize: "13px", fontWeight: 600, color: "var(--text-secondary)" }}>
                  <Fire size={15} /> ~{paced[paced.length - 1].energy_kcal} kcal
                </span>
              )}
              {hasWeather && (
                <span style={{ display: "flex", alignItems: "center", gap: "4px", background: "rgba(0,0,0,0.04)", padding: "6px 12px", borderRadius: "10px", fontSize: "13px", fontWeight: 600, color: "var(--text-secondary)" }}>
                  <Thermometer size={15} /> {t("Peak heat", "Nóng nhất")}: {Math.max(...paced.map((p) => p.temp_c ?? -99))}°C
                </span>
              )}
              {paced.some((p) => p.after_sunset) && (
                <span style={{ display: "flex", alignItems: "center", gap: "4px", background: "rgba(0,0,0,0.04)", padding: "6px 12px", borderRadius: "10px", fontSize: "13px", fontWeight: 600, color: "var(--text-primary)" }}>
                  <MoonStars size={15} /> {t("Headlamp needed", "Cần đèn đội đầu")}
                </span>
              )}
            </div>

            <ProfileChart paced={paced} lang={lang} />

            <div style={{ marginTop: "16px", border: "1px solid var(--border-color)", borderRadius: "12px", overflow: "hidden" }}>
              <div style={{ maxHeight: "300px", overflowY: "auto" }}>
                <table style={{ width: "100%", fontSize: "12.5px", borderCollapse: "collapse", textAlign: "left" }}>
                  <thead>
                    <tr style={{ borderBottom: "1px solid var(--border-color)", color: "var(--text-muted)", position: "sticky", top: 0, background: "rgba(255,255,255,0.95)" }}>
                      <th style={{ padding: "8px 10px" }}>{t("Waypoint", "Điểm mốc")}</th>
                      <th style={{ padding: "8px 10px" }}>{t("Dist", "Cự ly")}</th>
                      <th style={{ padding: "8px 10px" }}>{t("Grade", "Dốc")}</th>
                      <th style={{ padding: "8px 10px" }}>Pace</th>
                      <th style={{ padding: "8px 10px" }}>{t("Rest (min)", "Nghỉ (phút)")}</th>
                      {hasWeather && <th style={{ padding: "8px 10px" }}>{t("Weather", "Thời tiết")}</th>}
                      <th style={{ padding: "8px 10px" }}>ETA</th>
                    </tr>
                  </thead>
                  <tbody>
                    {paced.map((cp, idx) => (
                      <tr key={idx} style={{ borderBottom: "1px solid rgba(0,0,0,0.04)" }}>
                        <td style={{ padding: "8px 10px", fontWeight: 600, display: "flex", alignItems: "center", gap: "4px" }}>
                          {cp.effort === "hike" && <PersonSimpleHike size={14} color="var(--text-primary)" />}
                          {cp.name}
                        </td>
                        <td style={{ padding: "8px 10px" }}>{cp.distance_km}k</td>
                        <td style={{ padding: "8px 10px", color: cp.grade_pct > 0 ? "var(--text-primary)" : "var(--text-muted)" }}>
                          {cp.grade_pct > 0 ? "+" : ""}
                          {cp.grade_pct}%
                        </td>
                        <td style={{ padding: "8px 10px", fontFamily: "var(--font-mono)" }}>
                          {idx === 0 ? "—" : `${cp.target_pace}/k`}
                        </td>
                        <td style={{ padding: "4px 10px" }}>
                          {idx === 0 || idx === paced.length - 1 ? (
                            "—"
                          ) : (
                            <input
                              type="number"
                              min="0"
                              value={restMins[idx] || ""}
                              placeholder="0"
                              onChange={(e) => setRestMins({ ...restMins, [idx]: Math.max(0, parseInt(e.target.value, 10) || 0) })}
                              style={{ width: "48px", background: "rgba(0,0,0,0.03)", border: "1px solid var(--border-color)", borderRadius: "6px", padding: "3px 6px", fontSize: "12px", color: "var(--text-primary)" }}
                            />
                          )}
                        </td>
                        {hasWeather && (
                          <td style={{ padding: "8px 10px" }}>
                            {cp.temp_c != null ? `${cp.temp_c}°C` : "—"}
                            {cp.after_sunset && <MoonStars size={13} style={{ marginLeft: "4px", verticalAlign: "-2px" }} />}
                          </td>
                        )}
                        <td style={{ padding: "8px 10px", fontFamily: "var(--font-mono)", fontWeight: 700 }}>{etas[idx]}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            <p style={{ fontSize: "11.5px", color: "var(--text-muted)", marginTop: "12px" }}>
              {courseSource === "race"
                ? t(
                    "Course profile is estimated from total distance and climb — upload the official GPX for segment-accurate pacing.",
                    "Biểu đồ đường chạy được ước tính từ tổng cự ly và tổng leo — tải lên GPX chính thức để có pacing chính xác theo từng đoạn.",
                  )
                : t(
                    "Grounded in the Minetti energy-cost curve with altitude, durability and split-strategy adjustments.",
                    "Dựa trên đường cong năng lượng Minetti với hiệu chỉnh độ cao, độ bền và chiến thuật chia sức.",
                  )}
            </p>

            <div style={{ display: "flex", flexWrap: "wrap", gap: "10px", marginTop: "16px" }}>
              <button
                onClick={() => handleHandoff("nutrition")}
                style={{ flex: 1, minWidth: "200px", padding: "12px", borderRadius: "12px", background: "var(--text-primary)", color: "white", fontSize: "14px", fontWeight: 600, border: "none", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center", gap: "6px" }}
              >
                <BowlFood size={17} /> {t("Plan fueling for this race", "Lên kế hoạch dinh dưỡng")}
              </button>
              <button
                onClick={() => handleHandoff("gear")}
                style={{ flex: 1, minWidth: "200px", padding: "12px", borderRadius: "12px", background: "transparent", color: "var(--text-primary)", fontSize: "14px", fontWeight: 600, border: "1px solid var(--border-color)", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center", gap: "6px" }}
              >
                <Sneaker size={17} /> {t("Find shoes for this race", "Tìm giày cho giải này")}
              </button>
            </div>
          </div>
        )}

        {activePlan?.race_name && courseSource === "race" && !raceName && (
          <button
            onClick={() => setRaceName(activePlan.race_name)}
            style={{ marginTop: "4px", background: "none", border: "1px dashed var(--border-color)", borderRadius: "10px", padding: "8px 14px", fontSize: "12.5px", color: "var(--text-secondary)", cursor: "pointer" }}
          >
            {t(`Use my plan's race: ${activePlan.race_name}`, `Dùng giải trong kế hoạch: ${activePlan.race_name}`)}
          </button>
        )}
      </div>
    </div>
  );
};
