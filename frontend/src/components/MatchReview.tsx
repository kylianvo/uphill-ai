"use client";

import { useState } from "react";
import {
  ListChecks,
  ArrowsClockwise,
  CheckCircle,
  WarningCircle,
  MinusCircle,
  Warning,
} from "@phosphor-icons/react";
import { useAppContext } from "../contexts/AppContext";
import { useMatching, type MatchCounts } from "../hooks/useMatching";
import CorosAttribution from "./CorosAttribution";

export type MatchConfidenceBand = "auto" | "suggest" | "unmatched";

/**
 * One completed activity as the matcher last scored it. There is no GET
 * endpoint yet that lists these (only POST run, which returns counts, and
 * PATCH for a correction) -- this task built the review UI and the run/patch
 * plumbing, not a listing endpoint, so the caller supplies the rows it wants
 * reviewed (e.g. from wherever it already renders the athlete's activity
 * history). `confidence` is the backend's real score; for `unmatched` rows it
 * is always 0.0 by backend contract (see services/matching/assigner.py), not
 * a genuine "closest miss" score, so this component never renders it as one.
 */
export type MatchItem = {
  activityId: number;
  workoutId: number | null;
  workoutTitle: string | null;
  activitySummary: string;
  activityDate: string;
  confidence: number;
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
  "Activity not found.": "Không tìm thấy hoạt động này.",
};

function summaryLine(counts: MatchCounts, lang: "en" | "vi"): string {
  return lang === "vi"
    ? `${counts.matched} đã khớp tự động, ${counts.suggested} cần bạn xác nhận, ${counts.unmatched} chưa tìm được khớp.`
    : `${counts.matched} matched automatically, ${counts.suggested} need your confirmation, ${counts.unmatched} without a match.`;
}

function BandPill({ band, confidence, lang }: { band: MatchConfidenceBand; confidence: number; lang: "en" | "vi" }) {
  const pct = Math.round(confidence * 100);
  if (band === "auto") {
    return (
      <span className="match-badge match-badge-auto">
        <CheckCircle size={13} weight="fill" />
        {lang === "vi" ? "Đã khớp" : "Matched"}
        <span className="match-badge-pct">{lang === "vi" ? `${pct}% tin cậy` : `${pct}% confidence`}</span>
      </span>
    );
  }
  if (band === "suggest") {
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

export default function MatchReview({ items }: { items: MatchItem[] }) {
  const { lang } = useAppContext();
  const { running, error, runMatching, confirmMatch, clearMatch } = useMatching();
  const [counts, setCounts] = useState<MatchCounts | null>(null);
  const [savingId, setSavingId] = useState<number | null>(null);
  const [resolved, setResolved] = useState<Record<number, "confirmed" | "cleared">>({});

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
        <button type="button" className="btn btn-primary" style={{ height: "32px", fontSize: "12.5px", padding: "0 14px" }} onClick={handleRun} disabled={running}>
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

      {running && (
        <div className="match-list">
          <SkeletonCard />
          <SkeletonCard />
        </div>
      )}

      {!running && items.length === 0 && (
        <p className="match-empty">
          {lang === "vi"
            ? "Chưa có hoạt động nào để xem xét. Chạy kiểm tra để khớp các buổi tập gần đây với kế hoạch của bạn."
            : "No activities to review yet. Run a check to match your recent sessions against your plan."}
        </p>
      )}

      {!running && suggested.length > 0 && (
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

      {!running && auto.length > 0 && (
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

      {!running && unmatched.length > 0 && (
        <div className="match-group">
          <h4 className="match-group-heading">{lang === "vi" ? "Không tìm thấy khớp" : "No match found"}</h4>
          <div className="match-list">
            {unmatched.map((item) => (
              <div key={item.activityId} className="match-card">
                <div className="match-card-body">
                  <span className="match-activity">{item.activitySummary}</span>
                  <span className="match-date">{item.activityDate}</span>
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
  return (
    <div className="match-card">
      <div className="match-card-body">
        {item.workoutTitle && <strong className="match-workout">{item.workoutTitle}</strong>}
        <span className="match-activity">{item.activitySummary}</span>
        <span className="match-date">{item.activityDate}</span>
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
                className="btn btn-primary"
                style={{ height: "30px", fontSize: "12px", padding: "0 12px" }}
                onClick={onConfirm}
                disabled={saving}
              >
                {saving
                  ? lang === "vi"
                    ? "Đang lưu..."
                    : "Saving..."
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
