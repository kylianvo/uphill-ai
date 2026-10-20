/* eslint-disable @typescript-eslint/no-explicit-any */
/** What changed in a week's plan versus the week before, from the plan's own workouts. */

export type WeekDiffChip =
  | { kind: "time"; delta: number }
  | { kind: "long"; from: number; to: number }
  | { kind: "added" | "removed"; type: string; count: number };

const active = (wos: any[]) => wos.filter((w) => w.type !== "Rest");
const mins = (wos: any[]) => wos.reduce((s, w) => s + (w.duration_minutes || 0), 0);
const isLong = (w: any) => (w.type || "").trim().toLowerCase() === "long run";

/** Total-time change, long-run change, and session types gained or lost (max 2). Empty without both weeks. */
export function weekDiffChips(prev: any[], cur: any[]): WeekDiffChip[] {
  const p = active(prev);
  const c = active(cur);
  if (!p.length || !c.length) return [];
  const chips: WeekDiffChip[] = [];
  const delta = Math.round(mins(c) - mins(p));
  if (delta !== 0) chips.push({ kind: "time", delta });
  const from = Math.round(mins(p.filter(isLong)));
  const to = Math.round(mins(c.filter(isLong)));
  if (from !== to) chips.push({ kind: "long", from, to });
  const count = (wos: any[]) => wos.reduce((m: Map<string, number>, w) => m.set(w.type, (m.get(w.type) || 0) + 1), new Map());
  const before = count(p);
  const after = count(c);
  const types = [...new Set([...before.keys(), ...after.keys()])].filter((t) => t && !/^long run$/i.test(t));
  const typeChips: WeekDiffChip[] = [];
  for (const type of types) {
    const d = (after.get(type) || 0) - (before.get(type) || 0);
    if (d !== 0) typeChips.push({ kind: d > 0 ? "added" : "removed", type, count: Math.abs(d) });
  }
  typeChips.sort((a, b) => Number(b.kind === "added") - Number(a.kind === "added"));
  return [...chips, ...typeChips.slice(0, 2)];
}
