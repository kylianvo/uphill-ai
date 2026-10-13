"use client";

import React, { useCallback, useEffect, useId, useRef, useState } from "react";
import { ArrowClockwise, CaretDown, CheckCircle, Flag, LinkSimple, MagnifyingGlass, Mountains, Plus, Trophy, X } from "@phosphor-icons/react";
import styles from "./RaceHistory.module.css";
import RaceDetailDialog from "./RaceDetailDialog";
import { getApiBaseUrl } from "@/lib/apiUrlOverride";

import { manualResultPayload, safeResultUrl } from "../lib/raceHistory";
import type { RaceResult as Result, RaceHistory as History, RoadKey } from "../lib/raceHistory";

function duration(seconds: number | null): string {
  if (!seconds) return "DNF";
  return `${Math.floor(seconds / 3600)}:${String(Math.floor(seconds % 3600 / 60)).padStart(2, "0")}:${String(seconds % 60).padStart(2, "0")}`;
}

function parseDuration(value: string): number | null {
  const parts = value.trim().split(":").map(Number);
  if (parts.length < 2 || parts.length > 3 || parts.some((part) => !Number.isInteger(part) || part < 0) || parts.slice(1).some((part) => part >= 60)) return null;
  return parts[0] * 3600 + parts[1] * 60 + (parts[2] || 0);
}

export default function RaceHistoryPanel({ lang, athleteId, initiallyOpen = false }: {
  lang: "en" | "vi"; athleteId?: number; initiallyOpen?: boolean;
}) {
  const t = (en: string, vi: string) => lang === "en" ? en : vi;
  const readOnly = athleteId !== undefined;
  const [open, setOpen] = useState(initiallyOpen);
  const [history, setHistory] = useState<History | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [source, setSource] = useState<"utmb" | "vbm">("utmb");
  const [query, setQuery] = useState("");
  const [candidates, setCandidates] = useState<Array<{ external_id: string; display_name: string; age_group?: string; index?: number }>>([]);
  const [showManual, setShowManual] = useState(false);
  const [showImport, setShowImport] = useState(false);
  const [searched, setSearched] = useState(false);
  const [activeBib, setActiveBib] = useState<number | null>(null);
  const [bibValue, setBibValue] = useState("");
  const [confirmation, setConfirmation] = useState<{ kind: "claim" | "result"; id: number } | null>(null);
  const panelId = useId();
  const manualRef = useRef<HTMLDivElement>(null);
  const [detailResult, setDetailResult] = useState<Result | null>(null);
  const [editingId, setEditingId] = useState<number | null>(null);
  const emptyManual = { location: "", bib: "", result_url: "", user_note: "", rank_gender: "", total_gender: "", rank_age_group: "", total_age_group: "", race_name: "", race_date: "", discipline: "trail", distance_km: "", elevation_gain_m: "", finish_time: "", is_dnf: false, rank_overall: "", total_overall: "" };
  const [manual, setManual] = useState(emptyManual);

  const api = useCallback(async (path: string, init?: RequestInit) => {
    const token = localStorage.getItem("uphill_session_token");
    const response = await fetch(`${getApiBaseUrl()}${path}`, {
      ...init, headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json", ...init?.headers },
    });
    const data = await response.json().catch(() => null);
    if (!response.ok) throw new Error(data?.detail || `HTTP ${response.status}`);
    return data;
  }, []);
  const load = useCallback(async () => {
    const path = readOnly ? `/api/coaching/athletes/${athleteId}/race-history` : "/api/race-history";
    try { setHistory(await api(path)); setError(""); }
    catch (err) { setError(String(err)); throw err; }
  }, [api, athleteId, readOnly]);

  useEffect(() => {
    if (!open) return;
    const timer = window.setTimeout(() => void load().catch(() => {}), 0);
    return () => window.clearTimeout(timer);
  }, [open, load]);
  useEffect(() => {
    if (!open || !history?.claims.some((claim) => claim.sync_status === "pending")) return;
    const timer = window.setInterval(() => void load().catch(() => {}), 5000);
    return () => window.clearInterval(timer);
  }, [open, history?.claims, load]);

  const run = async (action: () => Promise<unknown>) => {
    setBusy(true); setError("");
    try {
      await action();
      try { await load(); }
      catch { setError(t("Saved, but refresh failed. Retry.", "Đã lưu. Tải lại dữ liệu thất bại. Thử lại.")); }
    }
    catch (err) { setError(err instanceof Error ? err.message : String(err)); }
    finally { setBusy(false); }
  };
  const changeResult = (id: number, changes: Record<string, unknown>) => run(() => api(`/api/race-history/results/${id}`, { method: "PATCH", body: JSON.stringify(changes) }));
  const visible = (history?.results || []).filter((result) => result.selected);
  const pendingVBM = (history?.results || []).filter((result) => result.source === "vbm" && !result.selected);
  const utmbIndexes = (history?.claims || []).flatMap((claim) => claim.source === "utmb" ? (claim.meta?.indexes || []) : [])
    .filter((value) => value.index && value.index > 0);

  const search = () => run(async () => {
    setCandidates(await api(`/api/race-history/search?source=${source}&q=${encodeURIComponent(query)}`));
    setSearched(true);
  });
  const selectedCount = (history?.results || []).filter((result) => result.selected).length;
  const dateLabel = (value: string) => new Date(`${value}T12:00:00`).toLocaleDateString(lang === "vi" ? "vi-VN" : "en-GB", { day: "numeric", month: "short", year: "numeric" });
  const edit = (result: Result) => {
    setEditingId(result.id); setShowManual(true); setShowImport(false);
    setManual({ race_name: result.race_name, race_date: result.race_date, discipline: result.discipline,
      distance_km: String(result.distance_km), elevation_gain_m: result.elevation_gain_m == null ? "" : String(result.elevation_gain_m),
      location: result.location || "", bib: result.bib || "", result_url: result.result_url || "", user_note: result.user_note || "",
      rank_gender: result.rank_gender?.toString() || "", total_gender: result.total_gender?.toString() || "",
      rank_age_group: result.rank_age_group?.toString() || "", total_age_group: result.total_age_group?.toString() || "",
      finish_time: result.finish_time_sec ? duration(result.finish_time_sec) : "", is_dnf: result.is_dnf,
      rank_overall: result.rank_overall == null ? "" : String(result.rank_overall), total_overall: result.total_overall == null ? "" : String(result.total_overall) });
    window.setTimeout(() => { manualRef.current?.scrollIntoView({ block: "nearest" }); manualRef.current?.querySelector("input")?.focus(); }, 0);
  };
  const remove = () => run(async () => {
    if (!confirmation) return;
    await api(`/api/race-history/${confirmation.kind === "claim" ? "claims" : "results"}/${confirmation.id}`, { method: "DELETE" });
    setConfirmation(null);
  });
  const confirmRemoval = (kind: "claim" | "result", id: number) => confirmation?.kind === kind && confirmation.id === id && <div className={styles.error}>
    <p>{kind === "claim" ? t("Unlink this profile and remove its imported results?", "Hủy liên kết và xóa kết quả đã nhập?") : t("Delete this result?", "Xóa kết quả này?")}</p>
    <div className={styles.actions}>
      <button type="button" className={styles.danger} disabled={busy} onClick={() => void remove()}>{t("Confirm", "Xác nhận")}</button>
      <button type="button" className={styles.quiet} disabled={busy} onClick={() => setConfirmation(null)}>{t("Cancel", "Hủy")}</button>
    </div>
  </div>;

  return (
    <section className={styles.panel} aria-label={t("Race history", "Lịch sử Race")}>
      <button type="button" className={styles.heading} aria-expanded={open} aria-controls={panelId} onClick={() => setOpen(!open)}>
        <span className={styles.headingIcon}><Flag size={22} weight="duotone" /></span>
        <span className={styles.headingText}><strong>{t("Race history", "Lịch sử Race")}</strong><small>{t("Your races, all in one place", "Các Race bạn đã tham gia")}</small></span>
        <CaretDown size={16} style={{ transform: open ? "rotate(180deg)" : undefined }} />
      </button>
      {open && <div id={panelId} className={styles.body}>
        {error && <div role="alert" className={styles.error}>{error}</div>}
        {error && <button type="button" className={styles.button} onClick={() => void load().catch(() => {})}>{t("Retry", "Thử lại")}</button>}
        {!history && !error && <div className={styles.loading} role="status"><ArrowClockwise className={styles.spin} size={18} />{t("Loading race history…", "Đang tải lịch sử Race…")}</div>}
        {history && <>
          <section className={styles.pbSection} aria-label={t("Road personal bests", "PR Road")}>
            <h3>{t("Road personal bests", "PR Road")}</h3>
            <div className={styles.pbGrid}>{(["5k", "10k", "hm", "fm"] as RoadKey[]).map((key) => {
              const best = history.summary.road_prs ? history.summary.road_prs[key] : key === "hm" ? history.summary.road_hm_pr : key === "fm" ? history.summary.road_fm_pr : null;
              return <button type="button" key={key} className={styles.pbItem} disabled={!best || !("result_id" in best) || !best.result_id} onClick={() => { if (best && "result_id" in best) setDetailResult(history.results.find(r => r.id === best.result_id) || null); }}>
                <span>{key === "hm" ? "HM" : key === "fm" ? "FM" : key === "5k" ? "5 km" : "10 km"}</span>
                <strong>{best ? duration(best.time_sec) : "—"}</strong>
                <small>{best && "date" in best ? String(best.date) : best ? t("Recorded finish", "Kết quả đã lưu") : t("No confirmed result", "Chưa xác nhận")}</small>
              </button>;
            })}</div>
          </section>
          {selectedCount > 0 && <div>
            <div className={styles.stats}>
              <div className={styles.stat}><strong>{history.summary.trail_finishes}</strong><small>{t("Trail finishes", "Hoàn thành Trail")}</small></div>
              <div className={styles.stat}><strong>{history.summary.ultras}</strong><small>{t("Ultra finishes", "Hoàn thành Ultra")}</small></div>
              <div className={styles.stat}><strong>{history.summary.longest_finish ? <>{history.summary.longest_finish.distance_km}<span> km</span></> : "—"}</strong><small>{t("Longest trail", "Trail dài nhất")}</small></div>
            </div>
            {(history.summary.road_hm_pr || history.summary.road_fm_pr || utmbIndexes.length > 0) && <div className={styles.records} style={{ marginTop: 12 }}>
              {history.summary.road_hm_pr && <span><Trophy size={14} />HM PR <b>{duration(history.summary.road_hm_pr.time_sec)}</b>{history.summary.road_hm_pr.stale && t("· over 2 years ago", "· hơn 2 năm")}</span>}
              {history.summary.road_fm_pr && <span><Trophy size={14} />FM PR <b>{duration(history.summary.road_fm_pr.time_sec)}</b>{history.summary.road_fm_pr.stale && t("· over 2 years ago", "· hơn 2 năm")}</span>}
              {utmbIndexes.map((value, index) => <span key={`${value.piCategory}-${index}`}>UTMB {value.piCategory || ""} <b>{value.index}</b></span>)}
            </div>}
          </div>}

          {!readOnly && <div className={styles.toolbar}>
            <button type="button" className={styles.primary} aria-expanded={showImport} onClick={() => { setShowImport(!showImport); setShowManual(false); }}><LinkSimple size={15} />{t("Link a profile", "Liên kết hồ sơ")}</button>
            <button type="button" className={styles.button} aria-expanded={showManual} onClick={() => { setEditingId(null); setManual(emptyManual); setShowManual(!showManual); setShowImport(false); }}><Plus size={15} />{t("Add result", "Thêm kết quả")}</button>
          </div>}

          {!readOnly && showImport && <div className={styles.surface}>
            <div className={styles.sectionHead}><h3>{t("Find your profile", "Tìm hồ sơ của bạn")}</h3><button type="button" className={styles.quiet} aria-label={t("Close profile search", "Đóng tìm kiếm")} onClick={() => setShowImport(false)}><X size={16} /></button></div>
            <div className={styles.segmented} role="group" aria-label={t("Source", "Nguồn")}>
              {(["utmb", "vbm"] as const).map((value) => <button type="button" key={value} aria-pressed={source === value} onClick={() => { setSource(value); setCandidates([]); setSearched(false); }}>{value.toUpperCase()}</button>)}
            </div>
            <p>{source === "vbm" ? t("VBM includes qualifying results only. Names may be shared, so choose only your own races after linking.", "VBM chỉ có kết quả đạt chuẩn. Tên có thể trùng; chỉ chọn Race của bạn sau khi liên kết.") : t("Search the name on your UTMB profile, then check the details before linking.", "Tìm theo tên trên UTMB và kiểm tra hồ sơ trước khi liên kết.")}</p>
            <div className={styles.searchRow}>
              <label className={styles.field}>{t("Runner name", "Tên VĐV")}<input className={styles.input} value={query} onChange={(event) => { setQuery(event.target.value); setSearched(false); }} onKeyDown={(event) => { if (event.key === "Enter") { event.preventDefault(); if (!busy && query.trim().length >= 2) void search(); } }} placeholder={t("Enter your name", "Nhập tên bạn")} /></label>
              <button type="button" className={styles.primary} disabled={busy || query.trim().length < 2} onClick={() => void search()}><MagnifyingGlass size={15} />{busy ? t("Searching…", "Đang tìm…") : t("Search", "Tìm")}</button>
            </div>
            {searched && candidates.length === 0 && <p role="status">{t("No profiles found. Try another spelling or add your result manually.", "Chưa tìm thấy hồ sơ. Thử cách viết khác hoặc nhập kết quả bằng tay.")}</p>}
            {candidates.map((candidate) => <div key={candidate.external_id} className={styles.candidate}>
              <div><strong>{candidate.display_name}</strong><small className={styles.muted}>{candidate.age_group || ""}{candidate.index ? ` · UTMB ${candidate.index}` : ""}</small></div>
              <button type="button" className={styles.button} disabled={busy} onClick={() => void run(async () => { await api("/api/race-history/claims", { method: "POST", body: JSON.stringify({ source, external_id: candidate.external_id }) }); setCandidates([]); setShowImport(false); })}>{t("Link", "Liên kết")}</button>
            </div>)}
          </div>}

          {!readOnly && showManual && <div className={styles.surface} ref={manualRef}>
            <div className={styles.sectionHead}><h3>{editingId ? t("Edit result", "Sửa kết quả") : t("Add a race result", "Thêm kết quả Race")}</h3><button type="button" className={styles.quiet} aria-label={t("Close manual entry", "Đóng nhập tay")} onClick={() => setShowManual(false)}><X size={16} /></button></div>
            <div className={styles.formGrid}>
              <label className={`${styles.field} ${styles.full}`}>{t("Race name", "Tên Race")}<input className={styles.input} placeholder={t("e.g. Vietnam Mountain Marathon", "VD: Vietnam Mountain Marathon")} value={manual.race_name} onChange={(e) => setManual({ ...manual, race_name: e.target.value })} /></label>
              <label className={styles.field}>{t("Race date", "Ngày Race")}<input type="date" className={styles.input} value={manual.race_date} onChange={(e) => setManual({ ...manual, race_date: e.target.value })} /></label>
              <label className={styles.field}>{t("Discipline", "Loại Race")}<select className={styles.input} value={manual.discipline} onChange={(e) => setManual({ ...manual, discipline: e.target.value })}><option value="trail">Trail</option><option value="road">Road</option></select></label>
              <label className={styles.field}>{t("Distance (km)", "Cự ly (km)")}<input type="number" min="0.01" step="0.01" className={styles.input} placeholder="50" value={manual.distance_km} onChange={(e) => setManual({ ...manual, distance_km: e.target.value })} /></label>
              <label className={styles.field}>{t("Elevation gain (m)", "D+ (m)")}<input type="number" min="0" className={styles.input} placeholder={t("Optional", "Tùy chọn")} value={manual.elevation_gain_m} onChange={(e) => setManual({ ...manual, elevation_gain_m: e.target.value })} /></label>
              <label className={styles.field}>{t("Finish time", "Thời gian")}<input className={styles.input} placeholder="h:mm:ss" value={manual.finish_time} onChange={(e) => setManual({ ...manual, finish_time: e.target.value })} disabled={manual.is_dnf} /></label>
              <label className={styles.check}><input type="checkbox" checked={manual.is_dnf} onChange={(e) => setManual({ ...manual, is_dnf: e.target.checked })} />{t("Did not finish (DNF)", "Không hoàn thành (DNF)")}</label>
              <label className={styles.field}>{t("Overall rank", "Thứ hạng chung")}<input type="number" min="1" className={styles.input} placeholder={t("Optional", "Tùy chọn")} value={manual.rank_overall} onChange={(e) => setManual({ ...manual, rank_overall: e.target.value })} /></label>
              <label className={styles.field}>{t("Total finishers", "Tổng VĐV về đích")}<input type="number" min="1" className={styles.input} placeholder={t("Optional", "Tùy chọn")} value={manual.total_overall} onChange={(e) => setManual({ ...manual, total_overall: e.target.value })} /></label>
              {([['location', 'Location', 'Địa điểm'], ['bib', 'Bib', 'Bib'], ['result_url', 'Result link', 'Link kết quả'], ['user_note', 'Race note', 'Ghi chú Race'], ['rank_gender', 'Gender rank', 'Hạng giới tính'], ['total_gender', 'Gender finishers', 'VĐV cùng giới'], ['rank_age_group', 'Age-group rank', 'Hạng nhóm tuổi'], ['total_age_group', 'Age-group finishers', 'VĐV nhóm tuổi']] as const).map(([key, en, vi]) => <label key={key} className={styles.field}>
                {t(en, vi)}<input className={styles.input} value={manual[key]} type={key.startsWith('rank_') || key.startsWith('total_') ? 'number' : key === 'result_url' ? 'url' : 'text'} min={key.startsWith('rank_') || key.startsWith('total_') ? 1 : undefined} maxLength={key === 'location' ? 200 : key === 'bib' ? 100 : key === 'result_url' ? 2048 : key === 'user_note' ? 2000 : undefined} onChange={(event) => setManual({ ...manual, [key]: event.target.value })} />
              </label>)}
              <p className={styles.full}>{t("A result link supports your record; it does not verify your identity.", "Link hỗ trợ kết quả đã nhập; không xác minh danh tính.")}</p>
            </div>
            <div className={styles.actions}>
              <button type="button" className={styles.primary} disabled={busy || !manual.race_name.trim() || !manual.race_date || Number(manual.distance_km) <= 0 || (!manual.is_dnf && !parseDuration(manual.finish_time))} onClick={() => void run(async () => {
                await api(editingId ? `/api/race-history/results/${editingId}` : "/api/race-history/results", { method: editingId ? "PATCH" : "POST", body: JSON.stringify(manualResultPayload(manual, lang))  }); setShowManual(false); setEditingId(null); setManual(emptyManual);
              })}>{busy ? t("Saving…", "Đang lưu…") : editingId ? t("Save changes", "Lưu thay đổi") : t("Save result", "Lưu kết quả")}</button>
              <button type="button" className={styles.quiet} onClick={() => setShowManual(false)}>{t("Cancel", "Hủy")}</button>
            </div>
          </div>}

          {history.claims.length > 0 && <div>
            {history.claims.map((claim) => <div key={claim.id} className={styles.claim}>
              <div className={styles.claimMain}>
                <span className={styles.sourceIcon}><LinkSimple size={18} /></span>
                <div className={styles.claimName}><strong>{claim.display_name}</strong><div className={styles.row}><span className={styles.badge}>{claim.source.toUpperCase()}</span><span className={`${styles.badge} ${claim.sync_status === "ok" ? styles.success : ""}`}>{claim.sync_status === "pending" ? t("Syncing…", "Đang đồng bộ…") : claim.sync_status === "ok" ? t("Synced", "Đã đồng bộ") : t("Sync failed", "Lỗi đồng bộ")}</span>
                  {claim.verified && <span className={`${styles.badge} ${styles.success}`} title={t("Evidence applies to matching results, not every race in this profile.", "Chỉ áp dụng cho kết quả khớp, không phải toàn bộ hồ sơ.")}><CheckCircle size={12} />{t("Evidence matched", "Đã khớp")}</span>}
                </div></div>
                {!readOnly && <button type="button" className={styles.quiet} title={t("Refresh profile", "Cập nhật hồ sơ")} aria-label={t("Refresh profile", "Cập nhật hồ sơ")} disabled={busy || claim.sync_status === "pending"} onClick={() => void run(() => api(`/api/race-history/claims/${claim.id}/refresh`, { method: "POST" }))}><ArrowClockwise size={17} className={claim.sync_status === "pending" ? styles.spin : undefined} /></button>}
              </div>
              {claim.sync_status === "error" && <p className={styles.error}>{claim.sync_error || t("Please try refreshing this profile.", "Thử cập nhật lại hồ sơ.")}</p>}
              {!readOnly && <div className={styles.actions}>
                {claim.source === "vbm" && <button type="button" className={styles.quiet} onClick={() => { setActiveBib(activeBib === claim.id ? null : claim.id); setBibValue(""); }}>{t("Check bib", "Kiểm tra bib")}</button>}
                <button type="button" className={styles.quiet} disabled={busy} onClick={() => setConfirmation({ kind: "claim", id: claim.id })}>{t("Unlink profile", "Hủy liên kết")}</button>
              </div>}
              {activeBib === claim.id && <div className={styles.surface}><p>{t("Enter a bib from one of your selected races. This checks a public result; it does not prove identity.", "Nhập bib của Race đã chọn. Kết quả công khai không xác minh danh tính.")}</p><div className={styles.searchRow}><label className={styles.field}>Bib<input className={styles.input} value={bibValue} onChange={(event) => setBibValue(event.target.value)} /></label><button type="button" className={styles.button} disabled={busy || !bibValue.trim()} onClick={() => void run(async () => { await api(`/api/race-history/claims/${claim.id}/verify-bib`, { method: "POST", body: JSON.stringify({ bib: bibValue.trim() }) }); setActiveBib(null); })}>{t("Check bib", "Kiểm tra bib")}</button></div></div>}
              {confirmRemoval("claim", claim.id)}
            </div>)}
          </div>}

          {!readOnly && pendingVBM.length > 0 && <div className={styles.surface}>
            <div className={styles.sectionHead}><h3>{t("Confirm your VBM results", "Xác nhận kết quả VBM")}</h3><span className={styles.badge}>{pendingVBM.length}</span></div>
            <p>{t("Only selected races become part of your history.", "Chỉ Race đã chọn được thêm vào lịch sử.")}</p>
            <div className={styles.selection}>{pendingVBM.map((result) => <div key={result.id} className={styles.pendingResult}>
              <span><strong>{result.race_name}</strong><br /><span className={styles.muted}>{dateLabel(result.race_date)} · {result.distance_km} km · {duration(result.finish_time_sec)}{result.bib ? ` · bib ${result.bib}` : ""}</span></span>
              <button type="button" className={styles.button} onClick={() => setDetailResult(result)}>{t("View details", "Xem chi tiết")}</button>
              <button type="button" className={styles.primary} disabled={busy} onClick={() => void changeResult(result.id, { selected: true })}>{t("This is my result", "Của tôi")}</button>
            </div>)}</div>
          </div>}

          {selectedCount === 0 ? <div className={styles.empty}><Mountains size={34} weight="duotone" /><strong>{t("Every race tells your story", "Mỗi Race, một dấu mốc")}</strong><p>{readOnly ? t("No race results have been added yet.", "Chưa có kết quả Race.") : t("Link UTMB or VBM, or add a finish yourself. Your history gives Coach more context for your training.", "Liên kết UTMB, VBM hoặc tự thêm kết quả để Coach hiểu kinh nghiệm của bạn.")}</p></div> : <div>
            <div className={styles.sectionHead}><h3>{t("Your races", "Các Race của bạn")} <span className={styles.muted}>({selectedCount})</span></h3>

            </div>
            <div className={styles.results}>{visible.map((result) => <details key={result.id} className={styles.result}>
              <summary><div className={styles.resultMain}><div className={styles.resultMeta}><span>{dateLabel(result.race_date)}</span><span className={styles.badge}>{result.source === "manual" ? t("Manual", "Nhập tay") : result.source.toUpperCase()}</span>{result.verified && <CheckCircle size={13} color="#147653" aria-label={t("Evidence matched", "Đã khớp")} />}{result.hidden && <span className={styles.badge}>{t("Excluded from text", "Ẩn khỏi lời Coach")}</span>}</div>
                <h4>{result.race_name}</h4><span className={styles.badge}>{result.discipline === "road" ? "Road" : "Trail"}</span><div className={styles.resultNumbers}><strong>{duration(result.finish_time_sec)}</strong><span>{result.distance_km} km</span>{result.elevation_gain_m != null && <span>{result.elevation_gain_m.toLocaleString()} m D+</span>}</div>
              </div><CaretDown className={styles.chevron} size={15} /></summary>
              <div className={styles.resultDetail}>
                <button type="button" className={styles.button} onClick={() => setDetailResult(result)}>{t("View details", "Xem chi tiết")}</button>
                {safeResultUrl(result.result_url) && <a className={styles.sourceLink} href={safeResultUrl(result.result_url)!} target="_blank" rel="noopener noreferrer">{t("View result source", "Xem nguồn kết quả")}</a>}
                {result.location && <p>{result.location}</p>}
                {result.rank_overall && <p>{t("Overall rank", "Thứ hạng chung")}: {result.rank_overall}{result.total_overall ? ` / ${result.total_overall}` : ""}</p>}
                {result.verified && <p>{result.verification_methods.includes("bib") ? t("Bib matches a public VBM result; identity is not proven.", "Bib khớp kết quả VBM công khai; chưa xác minh danh tính.") : ""} {result.verification_methods.includes("coros") ? t("Matched a COROS activity.", "Khớp hoạt động COROS.") : ""}</p>}
                {readOnly ? <p>{result.user_note || t("No note added.", "Chưa có ghi chú.")}</p> : <>
                  <label className={styles.field}>{t("Race note", "Ghi chú Race")}<input className={styles.input} defaultValue={result.user_note || ""} placeholder={t("e.g. Ran as a pacer", "VD: Chạy làm pacer")} disabled={busy} onBlur={(event) => { if (event.target.value !== (result.user_note || "")) void changeResult(result.id, { user_note: event.target.value }); }} /></label>
                  <div><label className={styles.check}><input type="checkbox" checked={result.hidden} disabled={busy} onChange={(event) => void changeResult(result.id, { hidden: event.target.checked })} />{t("Exclude from coach text", "Ẩn khỏi lời Coach")}</label><p>{t("Still included in your stats and estimates.", "Vẫn dùng để tính số liệu và ước tính.")}</p></div>
                  <div className={styles.actions}>
                    {result.source === "vbm" && <button type="button" className={styles.button} disabled={busy} onClick={() => void changeResult(result.id, { selected: false })}>{t("Not my result", "Không phải của tôi")}</button>}
                    {result.source === "manual" && <><button type="button" className={styles.button} disabled={busy} onClick={() => edit(result)}>{t("Edit result", "Sửa kết quả")}</button><button type="button" className={styles.quiet} disabled={busy} onClick={() => setConfirmation({ kind: "result", id: result.id })}>{t("Delete", "Xóa")}</button></>}
                  </div>
                  {confirmRemoval("result", result.id)}
                </>}
              </div>
            </details>)}</div>
          </div>}

        </>}
      </div>}
    {detailResult && <RaceDetailDialog key={detailResult.id} result={detailResult} lang={lang} athleteId={athleteId} onClose={() => setDetailResult(null)} onChanged={() => void load().catch(() => {})} onEdit={result => { setDetailResult(null); edit(result); }} />}
    </section>
  );
}
