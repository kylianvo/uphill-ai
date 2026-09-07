"use client";

import { useEffect, useRef, useState } from "react";
import {
  ListChecks,
  ArrowsClockwise,
  CheckCircle,
  WarningCircle,
  MinusCircle,
  Warning,
} from "@phosphor-icons/react";
import { useAppContext } from "../contexts/AppContext";
import { useMatching, type MatchCounts, type RawMatchActivity } from "../hooks/useMatching";
import CorosAttribution from "./CorosAttribution";

export type MatchConfidenceBand = "auto" | "suggest" | "unmatched";

/**
 * One completed activity as the matcher last scored it, in view-model shape.
 * Every measurement is a RAW value (never a pre-formatted string) so this
 * component can format it per-locale where `lang` is known -- a Vietnamese
 * athlete gets Vietnamese number and date conventions, not English units
 * concatenated into a string server-side. `confidence` is the backend's real
 * score; for `unmatched` rows it is always 0.0 by backend contract (see
 * services/matching/assigner.py), never a genuine "closest miss", so this
 * component never renders it as one. It is `null` for a manually-confirmed
 * match (the athlete's own correction has no numeric score) -- rendered as
 * "Matched" with no percentage, the same no-fabricated-number rule.
 */
export type MatchItem = {
  activityId: number;
  workoutId: number | null;
  workoutTitle: string | null;
  distanceKm: number | null;
  durationSeconds: number;
  avgHr: number | null;
  elevationGainM: number | null;
  startTime: string;
  confidence: number | null;
  confidenceBand: MatchConfidenceBand;
  reasons: string[];
  deviceModel: string | null;
  provider: string;
};

// Fallback strings the hook itself can surface (network failure, or a backend
// response with no `detail`). Arbitrary backend `detail` text is passed
// through untranslated, same precedent as ConnectedAccounts.tsx -- the
// backend does not yet return bilingual error detail.
const ERROR_TRANSLATIONS_VI: Record<string, string> = {
  "Could not match your activities.": "Không thể khớp các hoạt động của bạn. Vui lòng thử lại.",
  "Could not update the match.": "Không thể cập nhật kết quả khớp. Vui lòng thử lại.",
  "Could not load your matches.": "Không thể tải danh sách khớp. Vui lòng thử lại.",
  "Activity not found.": "Không tìm thấy hoạt động này.",
};

// How long the "tap again to confirm" state stays armed before reverting --
// long enough to read on a phone, short enough that a stray second tap
// minutes later can't land on a still-armed button.
const CONFIRM_ARM_TIMEOUT_MS = 4000;

// A manually-confirmed match (match_method = 'manual') displays like an
// automatic "auto" match -- it IS the resolved match -- but its
// match_confidence is always NULL (see db.set_manual_match), so it must
// never be lumped in with an unrun/never-matched activity (match_method
// NULL), which genuinely has no match at all.
function bandFromMethod(method: string | null): MatchConfidenceBand {
  if (method === "auto" || method === "manual") return "auto";
  if (method === "suggest") return "suggest";
  return "unmatched";
}

function toMatchItem(raw: RawMatchActivity): MatchItem {
  return {
    activityId: raw.activity_id,
    workoutId: raw.workout_id,
    workoutTitle: raw.workout_title,
    distanceKm: raw.distance_km,
    durationSeconds: raw.duration_seconds,
    avgHr: raw.avg_hr,
    elevationGainM: raw.elevation_gain_m,
    startTime: raw.start_time,
    confidence: raw.match_confidence,
    confidenceBand: bandFromMethod(raw.match_method),
    // GET /api/integrations/matching does not return match_details/reasons
    // today (see backend/routers/integrations.py) -- only POST run's
    // in-session result carries per-match reasons.
    reasons: [],
    deviceModel: raw.device_model,
    provider: raw.source_provider,
  };
}

function formatDuration(totalSeconds: number): string {
  const total = Math.max(0, Math.round(totalSeconds));
  const hours = Math.floor(total / 3600);
  const minutes = Math.floor((total % 3600) / 60);
  const seconds = total % 60;
  const ss = String(seconds).padStart(2, "0");
  if (hours > 0) {
    return `${hours}:${String(minutes).padStart(2, "0")}:${ss}`;
  }
  return `${minutes}:${ss}`;
}

function formatActivitySummary(item: MatchItem, lang: "en" | "vi"): string {
  const locale = lang === "vi" ? "vi-VN" : "en-US";
  const parts: string[] = [];
  if (item.distanceKm !== null) {
    const km = item.distanceKm.toLocaleString(locale, { minimumFractionDigits: 1, maximumFractionDigits: 1 });
    parts.push(`${km} km`);
  }
  parts.push(formatDuration(item.durationSeconds));
  if (item.avgHr !== null) {
    parts.push(lang === "vi" ? `nhịp tim TB ${item.avgHr}` : `avg HR ${item.avgHr}`);
  }
  return parts.join(", ");
}

function formatActivityDate(startTime: string, lang: "en" | "vi"): string {
  const locale = lang === "vi" ? "vi-VN" : "en-US";
  const parsed = new Date(startTime);
  if (Number.isNaN(parsed.getTime())) return "";
  return parsed.toLocaleDateString(locale, { month: "short", day: "numeric" });
}

function summaryLine(counts: MatchCounts, lang: "en" | "vi"): string {
  return lang === "vi"
    ? `${counts.matched} đã khớp tự động, ${counts.suggested} cần bạn xác nhận, ${counts.unmatched} chưa tìm được khớp.`
    : `${counts.matched} matched automatically, ${counts.suggested} need your confirmation, ${counts.unmatched} without a match.`;
}

function BandPill({ band, confidence, lang }: { band: MatchConfidenceBand; confidence: number | null; lang: "en" | "vi" }) {
  if (band === "auto") {
    return (
      <span className="match-badge match-badge-auto">
        <CheckCircle size={13} weight="fill" />
        {lang === "vi" ? "Đã khớp" : "Matched"}
        {confidence !== null && (
          <span className="match-badge-pct">
            {lang === "vi" ? `${Math.round(confidence * 100)}% tin cậy` : `${Math.round(confidence * 100)}% confidence`}
          </span>
        )}
      </span>
    );
  }
  if (band === "suggest") {
    const pct = Math.round((confidence ?? 0) * 100);
    return (
      <span className="match-badge match-badge-suggest">
        <WarningCircle size={13} weight="fill" />
        {lang === "vi" ? "Cần xác nhận" : "Needs confirming"}
        <span className="match-badge-pct">{lang === "vi" ? `${pct}% tin cậy` : `${pct}% confidence`}</span>
      </span>
    );
  }
  // Unmatched: the backend's score for this row is a hard-coded 0.0, never a
  // real "closest miss" -- rendering a percentage here would fabricate a
  // number the matcher never computed, so this pill carries no figure at all.
  return (
    <span className="match-badge match-badge-unmatched">
      <MinusCircle size={13} weight="fill" />
      {lang === "vi" ? "Không khớp" : "No match"}
    </span>
  );
}

function SkeletonCard() {
  return (
    <div className="match-card match-card-skeleton" aria-hidden="true">
      <div className="match-card-body">
        <span className="match-skeleton-line match-skeleton-line-wide" />
        <span className="match-skeleton-line match-skeleton-line-narrow" />
        <span className="match-skeleton-line match-skeleton-line-badge" />
      </div>
      <span className="match-skeleton-line match-skeleton-line-actions" />
    </div>
  );
}

/**
 * `items` is optional and exists for direct control (e.g. tests). When
 * omitted -- the normal case, mounted as `<MatchReview />` in
 * ProfileSettingsModal.tsx -- this fetches its own data via useMatching's
 * fetchMatches, the same self-contained pattern ConnectedAccounts.tsx uses
 * with useDeviceConnection.
 */
export default function MatchReview({ items: itemsProp }: { items?: MatchItem[] } = {}) {
  const { lang } = useAppContext();
  const { running, error, runMatching, confirmMatch, clearMatch, fetchMatches } = useMatching();
  const [counts, setCounts] = useState<MatchCounts | null>(null);
  const [savingId, setSavingId] = useState<number | null>(null);
  const [resolved, setResolved] = useState<Record<number, "confirmed" | "cleared">>({});
  const [fetchedItems, setFetchedItems] = useState<MatchItem[]>([]);
  const [loadingMatches, setLoadingMatches] = useState(itemsProp === undefined);

  useEffect(() => {
    if (itemsProp !== undefined) return; // controlled by the caller (tests)
    let cancelled = false;
    (async () => {
      const raw = await fetchMatches(30);
      if (cancelled) return;
      setFetchedItems(raw ? raw.map(toMatchItem) : []);
      setLoadingMatches(false);
    })();
    return () => {
      cancelled = true;
    };
    // Runs once on mount only -- itemsProp's presence is fixed for the
    // lifetime of a given render mode (controlled vs self-fetching), and
    // fetchMatches is a stable useCallback from the hook.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const items = itemsProp ?? fetchedItems;
  const busy = running || loadingMatches;

  const displayError = error ? (lang === "vi" ? ERROR_TRANSLATIONS_VI[error] ?? error : error) : "";

  const handleRun = async () => {
    const result = await runMatching(30);
    if (result) setCounts(result);
  };

  const handleConfirm = async (activityId: number, workoutId: number) => {
    setSavingId(activityId);
    const ok = await confirmMatch(activityId, workoutId);
    setSavingId(null);
    if (ok) setResolved((r) => ({ ...r, [activityId]: "confirmed" }));
  };

  const handleClear = async (activityId: number) => {
    setSavingId(activityId);
    const ok = await clearMatch(activityId);
    setSavingId(null);
    if (ok) setResolved((r) => ({ ...r, [activityId]: "cleared" }));
  };

  const suggested = items.filter((i) => i.confidenceBand === "suggest");
  const auto = items.filter((i) => i.confidenceBand === "auto");
  const unmatched = items.filter((i) => i.confidenceBand === "unmatched");

  return (
    <div className="match-section">
      <div className="match-header">
        <h3 className="match-heading">
          <ListChecks size={16} weight="duotone" style={{ color: "var(--accent-primary)" }} />
          {lang === "vi" ? "Khớp hoạt động" : "Activity matching"}
        </h3>
        <button type="button" className="btn btn-primary" style={{ height: "32px", fontSize: "12.5px", padding: "0 14px" }} onClick={handleRun} disabled={busy}>
          <ArrowsClockwise size={14} className={running ? "match-spin" : undefined} />
          {running
            ? lang === "vi"
              ? "Đang kiểm tra..."
              : "Checking..."
            : lang === "vi"
              ? "Kiểm tra lại"
              : "Re-check my runs"}
        </button>
      </div>

      <p className="match-help">
        {lang === "vi"
          ? "Uphill AI vẫn đang hiệu chỉnh bộ khớp này. Xác nhận một khớp ở đây chưa đánh dấu buổi tập là hoàn thành."
          : "Uphill AI is still calibrating this matcher. Confirming a match here does not mark the workout complete yet."}
      </p>

      {counts && <p className="match-summary">{summaryLine(counts, lang)}</p>}
      {displayError && (
        <p className="match-error">
          <Warning size={14} weight="fill" />
          {displayError}
        </p>
      )}

      {busy && (
        <div className="match-list">
          <SkeletonCard />
          <SkeletonCard />
        </div>
      )}

      {!busy && items.length === 0 && (
        <p className="match-empty">
          {lang === "vi"
            ? "Chưa có hoạt động nào để xem xét. Chạy kiểm tra để khớp các buổi tập gần đây với kế hoạch của bạn."
            : "No activities to review yet. Run a check to match your recent sessions against your plan."}
        </p>
      )}

      {!busy && suggested.length > 0 && (
        <div className="match-group">
          <h4 className="match-group-heading">{lang === "vi" ? "Cần bạn xác nhận" : "Needs your confirmation"}</h4>
          <div className="match-list">
            {suggested.map((item) => (
              <MatchCard
                key={item.activityId}
                item={item}
                lang={lang}
                saving={savingId === item.activityId}
                resolution={resolved[item.activityId]}
                onConfirm={() => item.workoutId !== null && handleConfirm(item.activityId, item.workoutId)}
                onClear={() => handleClear(item.activityId)}
                showConfirm
              />
            ))}
          </div>
        </div>
      )}

      {!busy && auto.length > 0 && (
        <div className="match-group">
          <h4 className="match-group-heading">{lang === "vi" ? "Đã khớp tự động" : "Matched automatically"}</h4>
          <div className="match-list">
            {auto.map((item) => (
              <MatchCard
                key={item.activityId}
                item={item}
                lang={lang}
                saving={savingId === item.activityId}
                resolution={resolved[item.activityId]}
                onClear={() => handleClear(item.activityId)}
                showConfirm={false}
              />
            ))}
          </div>
        </div>
      )}

      {!busy && unmatched.length > 0 && (
        <div className="match-group">
          <h4 className="match-group-heading">{lang === "vi" ? "Không tìm thấy khớp" : "No match found"}</h4>
          <div className="match-list">
            {unmatched.map((item) => (
              <div key={item.activityId} className="match-card">
                <div className="match-card-body">
                  <span className="match-activity">{formatActivitySummary(item, lang)}</span>
                  <span className="match-date">{formatActivityDate(item.startTime, lang)}</span>
                  <BandPill band="unmatched" confidence={0} lang={lang} />
                  <p className="match-unmatched-note">
                    {lang === "vi"
                      ? "Không có buổi tập nào trong kế hoạch khớp với buổi này. Lần kiểm tra sau có thể vẫn tìm được khớp."
                      : "No planned workout matched this session. A future re-check may still find one."}
                  </p>
                  <CorosAttribution deviceModel={item.deviceModel} provider={item.provider} />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function MatchCard({
  item,
  lang,
  saving,
  resolution,
  onConfirm,
  onClear,
  showConfirm,
}: {
  item: MatchItem;
  lang: "en" | "vi";
  saving: boolean;
  resolution: "confirmed" | "cleared" | undefined;
  onConfirm?: () => void;
  onClear: () => void;
  showConfirm: boolean;
}) {
  // Two-step confirm: this write is permanent (no automatic re-check ever
  // touches a manual match again -- see db.set_manual_match), the athlete is
  // often on a phone where mis-taps happen, and a silently-corrupted match is
  // hard to notice. The first tap only "arms" the button; it takes a second,
  // deliberate tap within CONFIRM_ARM_TIMEOUT_MS to actually issue the PATCH.
  // A native window.confirm() is deliberately not used -- unstyled, not
  // translatable through the lang pattern, and behaves poorly in the
  // Capacitor webview.
  const [armed, setArmed] = useState(false);
  const armTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    return () => {
      if (armTimeoutRef.current) clearTimeout(armTimeoutRef.current);
    };
  }, []);

  const handleConfirmTap = () => {
    if (!armed) {
      setArmed(true);
      armTimeoutRef.current = setTimeout(() => setArmed(false), CONFIRM_ARM_TIMEOUT_MS);
      return;
    }
    if (armTimeoutRef.current) clearTimeout(armTimeoutRef.current);
    setArmed(false);
    onConfirm?.();
  };

  return (
    <div className="match-card">
      <div className="match-card-body">
        {item.workoutTitle && <strong className="match-workout">{item.workoutTitle}</strong>}
        <span className="match-activity">{formatActivitySummary(item, lang)}</span>
        <span className="match-date">{formatActivityDate(item.startTime, lang)}</span>
        <BandPill band={item.confidenceBand} confidence={item.confidence} lang={lang} />
        {item.reasons.length > 0 && (
          <span className="match-reason">
            {lang === "vi" ? "Lý do: " : "Why: "}
            {item.reasons[0]}
          </span>
        )}
        <CorosAttribution deviceModel={item.deviceModel} provider={item.provider} />
      </div>

      {resolution ? (
        <span className="match-resolved">
          <CheckCircle size={14} weight="fill" />
          {lang === "vi" ? "Đã lưu" : "Saved"}
        </span>
      ) : (
        <div className="match-actions">
          <p className="match-permanent-note">
            {lang === "vi"
              ? "Điều này là vĩnh viễn. Các lần kiểm tra tự động sẽ không bao giờ thay đổi sau khi bạn chọn."
              : "This is permanent. Automatic re-checks will never change it once you choose."}
          </p>
          <div className="match-action-buttons">
            {showConfirm && (
              <button
                type="button"
                className={`btn btn-primary${armed ? " match-btn-armed" : ""}`}
                style={{ height: "30px", fontSize: "12px", padding: "0 12px" }}
                onClick={handleConfirmTap}
                disabled={saving}
              >
                {saving
                  ? lang === "vi"
                    ? "Đang lưu..."
                    : "Saving..."
                  : armed
                    ? lang === "vi"
                      ? "Nhấn lần nữa để xác nhận"
                      : "Tap again to confirm"
                    : lang === "vi"
                      ? "Đúng rồi"
                      : "Yes, that's it"}
              </button>
            )}
            <button type="button" className="match-btn-secondary" onClick={onClear} disabled={saving}>
              {saving && !showConfirm
                ? lang === "vi"
                  ? "Đang lưu..."
                  : "Saving..."
                : lang === "vi"
                  ? "Không đúng"
                  : "Not this one"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
