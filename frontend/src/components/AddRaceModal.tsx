"use client";
import React, { useEffect, useState } from "react";
import BRaceModalShell from "./BRaceModalShell";
import { LEVELS, REASONS, formatHms, suggestionLabel, type BRace, type BRaceAssessment, type BRaceEffort, type BRaceInput, type Lang } from "../lib/bRace";

interface Props {
  lang: Lang;
  race?: BRace; // editing an existing race
  assess: (input: BRaceInput) => Promise<BRaceAssessment | { error: string }>;
  save: (input: BRaceInput) => Promise<boolean>;
  onCancelRace?: () => void;
  onClose: () => void;
}

const T = {
  en: {
    title: "Add a race", edit: "Your B-race", race: "Race", date: "Date", distance: "Distance (km)", gain: "Climbing (m)",
    effort: "How will you run it?", racing: "Race it", training: "As a training run", checking: "Coach Uphill is checking…",
    add: "Add race", save: "Save", addAs: (s: string) => `Add it as ${s}`, keep: (km: number) => `Keep ${km} km anyway`,
    addTraining: "Add as a training run", cancelRace: "Cancel this race", cost: "What it would change",
    plan: (t: number, r: number) => `${t} easy days before, ${r} easy days after.`, predicted: "Predicted",
    distanceRequired: "We couldn't find this race in our list: add its distance.", dateOut: "Pick a date after today and before your goal race.",
    tooMany: "A plan holds up to 3 B-races.", failed: "Couldn't check this race. Try again.", confirmCancel: "Cancel this race? Your plan goes back to normal.",
  },
  vi: {
    title: "Thêm race", edit: "B-race của bạn", race: "Race", date: "Ngày", distance: "Cự ly (km)", gain: "Độ cao (m)",
    effort: "Bạn sẽ chạy thế nào?", racing: "Chạy hết sức", training: "Như buổi tập", checking: "Coach Uphill đang xem…",
    add: "Thêm race", save: "Lưu", addAs: (s: string) => `Thêm với ${s}`, keep: (km: number) => `Vẫn giữ ${km} km`,
    addTraining: "Thêm như buổi tập", cancelRace: "Huỷ race này", cost: "Những gì sẽ thay đổi",
    plan: (t: number, r: number) => `${t} ngày nhẹ trước, ${r} ngày nhẹ sau.`, predicted: "Dự đoán",
    distanceRequired: "Không tìm thấy race này trong danh sách: hãy nhập cự ly.", dateOut: "Chọn ngày sau hôm nay và trước race mục tiêu.",
    tooMany: "Mỗi plan có tối đa 3 B-race.", failed: "Chưa kiểm tra được race này. Thử lại nhé.", confirmCancel: "Huỷ race này? Plan sẽ trở lại như cũ.",
  },
} as const;

const ERRORS: Record<string, "distanceRequired" | "dateOut" | "tooMany"> = {
  distance_required: "distanceRequired", date_out_of_range: "dateOut", too_many_races: "tooMany",
};

const inputStyle: React.CSSProperties = { width: "100%", minHeight: 44, padding: "8px 10px", borderRadius: 10, border: "1px solid #c9d3cc", fontSize: 15, boxSizing: "border-box", background: "#ffffff", color: "#17231d", colorScheme: "light" };
const labelStyle: React.CSSProperties = { display: "flex", flexDirection: "column", gap: 4, fontSize: 12, fontWeight: 600, color: "var(--text-secondary, #5b6b63)" };

export default function AddRaceModal({ lang, race, assess, save, onCancelRace, onClose }: Props) {
  const t = T[lang] ?? T.en;
  const [input, setInput] = useState<BRaceInput>({
    race_name: race?.race_name ?? "", race_date: race?.race_date ?? "", distance_km: race?.distance_km ?? null,
    elevation_gain_m: race?.elevation_gain_m ?? null, effort: race?.effort ?? "race",
  });
  const [result, setResult] = useState<BRaceAssessment | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const ready = input.race_name.trim().length >= 3 && /^\d{4}-\d{2}-\d{2}$/.test(input.race_date);

  useEffect(() => {
    if (!ready) return;
    let live = true;
    const timer = setTimeout(async () => {
      const r = await assess(input).catch(() => ({ error: "failed" }));
      if (!live) return;
      if ("error" in r) { setResult(null); setError(t[ERRORS[r.error] ?? "failed"]); } else { setResult(r); setError(null); }
    }, 400);
    return () => { live = false; clearTimeout(timer); };
  }, [input, ready]); // eslint-disable-line react-hooks/exhaustive-deps

  const set = <K extends keyof BRaceInput>(k: K, v: BRaceInput[K]) => setInput((p) => ({ ...p, [k]: v }));
  const num = (v: string) => (v.trim() === "" ? null : Number(v));
  const commit = async (body: BRaceInput) => {
    setBusy(true);
    const ok = await save(body).catch(() => false);
    setBusy(false);
    if (ok) onClose(); else setError(t.failed);
  };

  const v = result?.verdict;
  const level = v ? LEVELS[v.level] : null;
  const km = result?.race.distance_km ?? input.distance_km ?? 0;
  const gain = result?.race.elevation_gain_m ?? input.elevation_gain_m ?? null;
  const resolved: BRaceInput = { ...input, distance_km: km || input.distance_km, elevation_gain_m: gain };
  const suggested = v?.suggestion
    ? { ...resolved, distance_km: v.suggestion.distance_km, effort: v.suggestion.effort,
        elevation_gain_m: gain != null && km ? Math.round((gain * v.suggestion.distance_km) / km) : gain }
    : null;
  const primary = { minHeight: 48, borderRadius: 12, border: "none", background: "var(--accent-primary, #2f7a55)", color: "#fff", fontSize: 15, fontWeight: 600, cursor: "pointer" } as const;
  const secondary = { minHeight: 44, borderRadius: 12, border: "1px solid #c9d3cc", background: "#ffffff", color: "#17231d", fontSize: 14, cursor: "pointer" } as const;

  return (
    <BRaceModalShell title={race ? t.edit : t.title} onClose={onClose}>
      <label style={labelStyle}>{t.race}<input style={inputStyle} value={input.race_name} onChange={(e) => set("race_name", e.target.value)} /></label>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, minmax(0, 1fr))", gap: 8 }}>
        <label style={labelStyle}>{t.date}<input type="date" style={inputStyle} value={input.race_date} onChange={(e) => set("race_date", e.target.value)} /></label>
        <label style={labelStyle}>{t.distance}<input type="number" inputMode="decimal" style={inputStyle} value={input.distance_km ?? ""} onChange={(e) => set("distance_km", num(e.target.value))} /></label>
        <label style={labelStyle}>{t.gain}<input type="number" inputMode="numeric" style={inputStyle} value={input.elevation_gain_m ?? ""} onChange={(e) => set("elevation_gain_m", num(e.target.value))} /></label>
      </div>
      {!!result?.race.options_km?.length && (
        <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
          {result.race.options_km.map((o) => (
            <button key={o} type="button" aria-pressed={o === km} onClick={() => set("distance_km", o)}
              style={{ minHeight: 40, padding: "0 12px", borderRadius: 999, cursor: "pointer", fontSize: 13,
                border: o === km ? "2px solid var(--text-primary, #17231d)" : "1px solid var(--border-color, #dfe5e0)", background: "transparent" }}>
              {o} km
            </button>
          ))}
        </div>
      )}
      <fieldset style={{ border: "none", padding: 0, margin: 0, display: "flex", flexDirection: "column", gap: 6 }}>
        <legend style={{ ...labelStyle, marginBottom: 4 }}>{t.effort}</legend>
        <div style={{ display: "flex", gap: 6 }}>
          {(["race", "training"] as BRaceEffort[]).map((e) => (
            <button key={e} type="button" aria-pressed={input.effort === e} onClick={() => set("effort", e)}
              style={{ ...secondary, flex: 1, border: `1px solid ${input.effort === e ? "#2f7a55" : "#c9d3cc"}`, background: input.effort === e ? "#e6f2ea" : "#ffffff", color: input.effort === e ? "#1f5a3e" : "#17231d", fontWeight: input.effort === e ? 600 : 400 }}>
              {e === "race" ? t.racing : t.training}
            </button>
          ))}
        </div>
      </fieldset>

      {race?.opinion && (
        <div style={{ border: "1px solid #dfe5e0", borderRadius: 14, padding: 12, display: "flex", flexDirection: "column", gap: 4 }}>
          <span style={{ fontSize: 11, fontWeight: 700, letterSpacing: "0.5px", color: "#5b6b63" }}>COACH UPHILL</span>
          <p style={{ margin: 0, fontSize: 14, lineHeight: 1.5 }}>{race.opinion}</p>
        </div>
      )}
      {error && <p role="alert" style={{ margin: 0, color: "#b42318", fontSize: 13 }}>{error}</p>}
      {ready && !result && !error && <p style={{ margin: 0, fontSize: 13, color: "var(--text-secondary, #5b6b63)" }}>{t.checking}</p>}
      {v && level && (
        <div style={{ background: level.bg, border: `1px solid ${level.line}`, borderRadius: 14, padding: 12, display: "flex", flexDirection: "column", gap: 8, color: level.fg }}>
          <span style={{ alignSelf: "flex-start", fontSize: 12, fontWeight: 700, padding: "3px 9px", borderRadius: 999, background: level.fg, color: "#fff" }}>{level[lang]}</span>
          {v.reasons.length > 0 && (
            <ul style={{ margin: 0, paddingLeft: 18, fontSize: 14, lineHeight: 1.4 }}>
              {v.reasons.map((r) => <li key={r}>{REASONS[r]?.[lang] ?? r}</li>)}
            </ul>
          )}
          <span style={{ fontSize: 13 }}>{t.plan(v.taper_days, v.recovery_days)}</span>
          {result?.predicted && <span style={{ fontSize: 13 }}>{t.predicted}: {formatHms(result.predicted.low_sec)}–{formatHms(result.predicted.high_sec)}</span>}
          {!!v.cost?.changed.length && (
            <div style={{ fontSize: 13 }}>
              <strong>{t.cost}</strong>
              <ul style={{ margin: "4px 0 0", paddingLeft: 18 }}>
                {v.cost.changed.slice(0, 5).map((c) => (
                  <li key={`${c.week}-${c.day}`}>{`W${c.week} ${c.day.slice(0, 3)}: ${c.title_before} → ${c.title_after}`}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {v && (
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {v.level === "good" && <button type="button" disabled={busy} style={primary} onClick={() => commit(resolved)}>{race ? t.save : t.add}</button>}
          {v.level === "not_recommended" && (
            <button type="button" disabled={busy} style={primary} onClick={() => commit({ ...resolved, effort: "training" })}>{t.addTraining}</button>
          )}
          {(v.level === "conditions" || v.level === "risky") && (
            <>
              {suggested && v.suggestion && (
                <button type="button" disabled={busy} style={primary} onClick={() => commit(suggested)}>{t.addAs(suggestionLabel(v.suggestion, lang))}</button>
              )}
              <button type="button" disabled={busy} style={{ ...secondary, color: v.level === "risky" ? "#b42318" : undefined }} onClick={() => commit(resolved)}>
                {t.keep(km)}
              </button>
            </>
          )}
        </div>
      )}
      {race && onCancelRace && (
        <button type="button" style={{ ...secondary, color: "#b42318" }} onClick={() => { if (window.confirm(t.confirmCancel)) onCancelRace(); }}>
          {t.cancelRace}
        </button>
      )}
    </BRaceModalShell>
  );
}
