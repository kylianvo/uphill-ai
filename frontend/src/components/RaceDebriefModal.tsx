"use client";
import React, { useState } from "react";
import BRaceModalShell from "./BRaceModalShell";
import { formatHms, parseHms, type BRace, type Lang } from "../lib/bRace";

type Answers = { fuel?: string; pacing?: string; gear?: string };
interface Props {
  race: BRace;
  lang: Lang;
  submitResult: (seconds: number) => Promise<boolean>;
  submitDebrief: (answers: Answers) => Promise<{ debrief: { text?: string }; goal: { suggested_target_hours: number | null } } | null>;
  onClose: () => void;
}

const T = {
  en: {
    title: (n: string) => `${n} · Debrief`, time: "Finish time (h:mm:ss)", predicted: "Predicted", rehearsal: "How did the rehearsal go?",
    fuel: "Fuel", pacing: "Pacing", gear: "Gear", go: "Get my debrief", badTime: "Enter a time like 3:11:00.",
    target: (h: string) => `Your goal-race estimate moved to ${h}. Review it in Goal.`, done: "Done", failed: "Couldn't save. Try again.",
    options: {
      fuel: [["plan", "Went to plan"], ["stomach", "Stomach trouble"], ["skipped", "Skipped some"]],
      pacing: [["even", "Even"], ["fast_start", "Too fast early"], ["held_back", "Held back"]],
      gear: [["ok", "All good"], ["change", "Something to change"]],
    },
  },
  vi: {
    title: (n: string) => `${n} · Nhìn lại`, time: "Thời gian về đích (h:mm:ss)", predicted: "Dự đoán", rehearsal: "Buổi tập dượt thế nào?",
    fuel: "Dinh dưỡng", pacing: "Nhịp độ", gear: "Trang bị", go: "Xem nhận xét", badTime: "Nhập thời gian dạng 3:11:00.",
    target: (h: string) => `Ước tính cho race mục tiêu đã đổi thành ${h}. Xem lại ở mục Goal.`, done: "Xong", failed: "Chưa lưu được. Thử lại nhé.",
    options: {
      fuel: [["plan", "Đúng kế hoạch"], ["stomach", "Khó chịu bụng"], ["skipped", "Bỏ lỡ vài lần"]],
      pacing: [["even", "Đều"], ["fast_start", "Đầu quá nhanh"], ["held_back", "Dè dặt"]],
      gear: [["ok", "Ổn cả"], ["change", "Cần đổi món"]],
    },
  },
} as const;

/** After a B-race: the time (unless the watch already gave it), three one-tap questions, then the coach's debrief. */
export default function RaceDebriefModal({ race, lang, submitResult, submitDebrief, onClose }: Props) {
  const t = T[lang] ?? T.en;
  const [time, setTime] = useState(race.result_seconds ? formatHms(race.result_seconds) : "");
  const [answers, setAnswers] = useState<Answers>({});
  const [out, setOut] = useState<{ text: string; target: number | null } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const send = async () => {
    const seconds = time.trim() ? parseHms(time) : null;
    if (time.trim() && seconds === null) return setError(t.badTime);
    setBusy(true);
    setError(null);
    if (seconds && seconds !== race.result_seconds && !(await submitResult(seconds).catch(() => false))) {
      setBusy(false);
      return setError(t.failed);
    }
    const res = await submitDebrief(answers).catch(() => null);
    setBusy(false);
    if (!res?.debrief.text) return setError(t.failed);
    setOut({ text: res.debrief.text, target: res.goal.suggested_target_hours });
  };

  const hours = (h: number) => `${Math.floor(h)}:${String(Math.round((h % 1) * 60)).padStart(2, "0")}`;
  const chip = (on: boolean): React.CSSProperties => ({
    minHeight: 40, padding: "0 12px", borderRadius: 999, fontSize: 13, cursor: "pointer",
    border: on ? "1px solid var(--accent-primary, #2f7a55)" : "1px solid var(--border-color, #dfe5e0)",
    background: on ? "#e6f2ea" : "transparent", color: on ? "#1f5a3e" : "inherit", fontWeight: on ? 600 : 400,
  });

  return (
    <BRaceModalShell title={t.title(race.race_name)} onClose={onClose}>
      {out ? (
        <>
          <p style={{ margin: 0, fontSize: 15, lineHeight: 1.5 }}>{out.text}</p>
          {out.target && <p style={{ margin: 0, fontSize: 14, color: "var(--accent-primary, #2f7a55)" }}>{t.target(hours(out.target))}</p>}
          <button type="button" onClick={onClose} className="btn btn-primary" style={{ minHeight: 48, borderRadius: 12 }}>{t.done}</button>
        </>
      ) : (
        <>
          <label style={{ display: "flex", flexDirection: "column", gap: 4, fontSize: 12, fontWeight: 600 }}>
            {t.time}
            <input value={time} onChange={(e) => setTime(e.target.value)} inputMode="numeric" placeholder="3:11:00"
              style={{ minHeight: 44, padding: "8px 10px", borderRadius: 10, border: "1px solid #c9d3cc", fontSize: 15, background: "#ffffff", color: "#17231d", colorScheme: "light" }} />
          </label>
          {race.predicted && (
            <span style={{ fontSize: 13, color: "var(--text-secondary, #5b6b63)" }}>
              {t.predicted}: {formatHms(race.predicted.low_sec)}–{formatHms(race.predicted.high_sec)}
            </span>
          )}
          <span style={{ fontSize: 12, fontWeight: 700, letterSpacing: "0.5px", color: "var(--text-secondary, #5b6b63)" }}>{t.rehearsal}</span>
          {(["fuel", "pacing", "gear"] as const).map((k) => (
            <div key={k} role="group" aria-label={t[k]} style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              <span style={{ fontSize: 14, fontWeight: 600 }}>{t[k]}</span>
              <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                {t.options[k].map(([value, label]) => (
                  <button key={value} type="button" aria-pressed={answers[k] === value} style={chip(answers[k] === value)}
                    onClick={() => setAnswers((a) => ({ ...a, [k]: value }))}>{label}</button>
                ))}
              </div>
            </div>
          ))}
          {error && <p role="alert" style={{ margin: 0, color: "#b42318", fontSize: 13 }}>{error}</p>}
          <button type="button" disabled={busy} onClick={send} className="btn btn-primary" style={{ minHeight: 48, borderRadius: 12 }}>{t.go}</button>
        </>
      )}
    </BRaceModalShell>
  );
}
