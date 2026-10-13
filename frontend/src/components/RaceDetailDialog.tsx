"use client";
import { useEffect, useId, useRef, useState } from "react";
import { X } from "@phosphor-icons/react";
import { getApiBaseUrl } from "@/lib/apiUrlOverride";
import { formatKm, formatNumber, formatPace, safeResultUrl } from "../lib/raceHistory";
import type { RaceDetail, RaceResult } from "../lib/raceHistory";
import RaceCourseContext from "./RaceCourseContext";
import styles from "./RaceDetail.module.css";
const duration = (seconds: number | null) =>
  seconds === null
    ? "DNF"
    : `${Math.floor(seconds / 3600)}:${String(
        Math.floor(seconds / 60) % 60
      ).padStart(2, "0")}:${String(seconds % 60).padStart(2, "0")}`;
export default function RaceDetailDialog({
  result,
  athleteId,
  lang,
  onClose,
  onChanged,
  onEdit,
}: {
  result: RaceResult;
  athleteId?: number;
  lang: "en" | "vi";
  onClose: () => void;
  onChanged: () => void;
  onEdit?: (result: RaceResult) => void;
}) {
  const t = (en: string, vi: string) => (lang === "en" ? en : vi);
  const ref = useRef<HTMLDialogElement>(null),
    title = useId();
  const [detail, setDetail] = useState<RaceDetail | null>(null),
    [courseId, setCourseId] = useState<number | null>(null),
    [retry, setRetry] = useState(0),
    [loading, setLoading] = useState(true),
    [error, setError] = useState<"load" | "mutate" | null>(null),
    [busy, setBusy] = useState(false),
    [deleting, setDeleting] = useState(false);
  useEffect(() => {
    const opener = document.activeElement as HTMLElement | null;
    const dialog = ref.current;
    dialog?.showModal();
    return () => {
      dialog?.close();
      opener?.focus();
    };
  }, []);
  useEffect(() => {
    const controller = new AbortController();
    let active = true;
    const prefix =
      athleteId === undefined
        ? "/api/race-history"
        : `/api/coaching/athletes/${athleteId}/race-history`;
    fetch(
      `${getApiBaseUrl()}${prefix}/results/${result.id}/detail${
        courseId === null ? "" : `?course_id=${courseId}`
      }`,
      {
        signal: controller.signal,
        headers: {
          Authorization: `Bearer ${localStorage.getItem(
            "uphill_session_token"
          )}`,
        },
      }
    )
      .then(async (r) => {
        const body = await r.json();
        if (!r.ok) throw new Error(body.detail || `HTTP ${r.status}`);
        return body as RaceDetail;
      })
      .then((body) => {
        if (active) setDetail(body);
      })
      .catch((err) => {
        if (active && err.name !== "AbortError") {
          console.error(err);
          setError("load");
        }
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
      controller.abort();
    };
  }, [result.id, athleteId, courseId, retry]);
  const refresh = () => {
    setLoading(true);
    setError(null);
    setRetry((r) => r + 1);
  };
  const choose = (id: number) => {
    setLoading(true);
    setError(null);
    setCourseId(id);
  };
  const recorded = detail?.result.id === result.id ? detail.result : result;
  const mutate = async (remove = false) => {
    setBusy(true);
    setError(null);
    try {
      const response = await fetch(
        `${getApiBaseUrl()}/api/race-history/results/${result.id}`,
        {
          method: remove ? "DELETE" : "PATCH",
          headers: {
            Authorization: `Bearer ${localStorage.getItem(
              "uphill_session_token"
            )}`,
            "Content-Type": "application/json",
          },
          ...(!remove
            ? { body: JSON.stringify({ selected: !recorded.selected }) }
            : {}),
        }
      );
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      onChanged();
      if (remove) onClose();
      else refresh();
    } catch (err) {
      console.error(err);
      setError("mutate");
    } finally {
      setBusy(false);
    }
  };
  const rank = (
    label: string,
    value: number | null | undefined,
    total: number | null | undefined,
    pct: number | null | undefined
  ) =>
    value ? (
      <div>
        <dt>{label}</dt>
        <dd>
          #{value}
          {total && total >= value ? ` / ${total}` : ""}
          {!recorded.is_dnf && typeof pct === "number" && (
            <small>
              {t(`Top ${pct}% of the field`, `Trong ${pct}% đầu bảng`)}
            </small>
          )}
        </dd>
      </div>
    ) : null;
  const link = safeResultUrl(recorded.result_url),
    prior = detail?.previous_finish,
    field = detail?.historical_field;
  return (
    <dialog
      ref={ref}
      aria-labelledby={title}
      className={styles.dialog}
      onCancel={(e) => {
        e.preventDefault();
        onClose();
      }}
    >
      <header className={styles.header}>
        <h2 id={title}>{recorded.race_name}</h2>
        <button
          className={styles.close}
          aria-label={t("Close", "Đóng")}
          onClick={onClose}
        >
          <X size={22} />
        </button>
      </header>
      <div className={styles.body}>
        <p>
          {recorded.race_date} ·{" "}
          {recorded.discipline === "road"
            ? t("Road", "Road")
            : t("Trail", "Trail")}{" "}
          ·{" "}
          {recorded.source === "manual"
            ? t("Manual entry", "Tự nhập")
            : recorded.source === "vbm"
            ? "VBM"
            : recorded.source === "utmb"
            ? "UTMB"
            : recorded.source.toUpperCase()}
        </p>
        {!recorded.selected && (
          <p className={styles.notice}>
            {t("Awaiting confirmation", "Chờ xác nhận")}
          </p>
        )}
        <dl className={styles.metrics}>
          <div>
            <dt>{t("Finish time", "Thời gian")}</dt>
            <dd>
              {recorded.is_dnf ? "DNF" : duration(recorded.finish_time_sec)}
            </dd>
          </div>
          <div>
            <dt>{t("Recorded distance", "Cự ly đã ghi nhận")}</dt>
            <dd>{formatKm(recorded.distance_km)} km</dd>
          </div>
          {recorded.elevation_gain_m !== null && (
            <div>
              <dt>{t("Recorded elevation gain", "D+ đã ghi nhận")}</dt>
              <dd>{formatNumber(recorded.elevation_gain_m, lang)} m</dd>
            </div>
          )}
          {rank(
            t("Overall rank", "Thứ hạng chung"),
            recorded.rank_overall,
            recorded.total_overall,
            detail?.performance.overall_top_pct
          )}
          {rank(
            t("Gender rank", "Thứ hạng theo giới tính"),
            recorded.rank_gender,
            recorded.total_gender,
            detail?.performance.gender_top_pct
          )}
          {rank(
            t("Age group rank", "Thứ hạng nhóm tuổi"),
            recorded.rank_age_group,
            recorded.total_age_group,
            detail?.performance.age_group_top_pct
          )}
        </dl>
        {recorded.location && <p>{recorded.location}</p>}
        {recorded.bib && <p>Bib: {recorded.bib}</p>}
        {detail?.performance.road_pb_key && (
          <p>
            {detail.performance.road_pb_key.toUpperCase()} ·{" "}
            {t("Personal best", "PR")}
          </p>
        )}
        {detail?.performance.average_pace_sec_km != null && (
          <p>
            {t("Average pace", "Pace trung bình")}:{" "}
            {formatPace(detail.performance.average_pace_sec_km)} /km
          </p>
        )}
        {link && (
          <a href={link} target="_blank" rel="noopener noreferrer">
            {t("Open result source", "Mở nguồn kết quả")}
          </a>
        )}
        {recorded.user_note && (
          <section>
            <h3>{t("Your notes", "Ghi chú của bạn")}</h3>
            <p>{recorded.user_note}</p>
          </section>
        )}
        {athleteId === undefined && (
          <div className={styles.actions}>
            {recorded.source === "manual" ? (
              <>
                <button
                  className={styles.button}
                  disabled={busy}
                  onClick={() => onEdit?.(recorded)}
                >
                  {t("Edit result", "Sửa kết quả")}
                </button>
                <button
                  className={styles.button}
                  disabled={busy}
                  onClick={() => setDeleting(true)}
                >
                  {t("Delete result", "Xóa kết quả")}
                </button>
              </>
            ) : recorded.source === "vbm" ? (
              <button
                className={styles.button}
                disabled={busy}
                onClick={() => void mutate()}
              >
                {recorded.selected
                  ? t("Not my result", "Không phải của tôi")
                  : t("This is my result", "Của tôi")}
              </button>
            ) : null}
          </div>
        )}
        {deleting && (
          <div role="alert">
            <p>
              {t("Delete this manual result?", "Xóa kết quả nhập tay này?")}
            </p>
            <button
              className={styles.button}
              disabled={busy}
              onClick={() => void mutate(true)}
            >
              {t("Delete", "Xóa")}
            </button>
            <button
              className={styles.button}
              onClick={() => setDeleting(false)}
            >
              {t("Cancel", "Hủy")}
            </button>
          </div>
        )}
        <section className={styles.review}>
          <h3>{t("Race Review", "Nhìn lại Race")}</h3>
          {loading && (
            <p role="status">{t("Loading review…", "Đang tải thông tin…")}</p>
          )}
          {error && (
            <div role="alert">
              <p>
                {error === "load"
                  ? t(
                      "Couldn't load the race review. Your recorded result is unchanged.",
                      "Không tải được phần nhìn lại Race. Kết quả đã ghi nhận của bạn vẫn giữ nguyên."
                    )
                  : t(
                      "Couldn't save that change. Your recorded result is unchanged.",
                      "Không lưu được thay đổi. Kết quả đã ghi nhận của bạn vẫn giữ nguyên."
                    )}
              </p>
              {error === "load" && (
                <button className={styles.button} onClick={refresh}>
                  {t("Retry", "Thử lại")}
                </button>
              )}
            </div>
          )}
          {!recorded.is_dnf && recorded.selected && prior && (
            <p>
              {prior.delta_sec === 0
                ? t("Same finish time", "Cùng thời gian về đích")
                : `${duration(Math.abs(prior.delta_sec))} ${
                    prior.delta_sec < 0
                      ? t("faster", "nhanh hơn")
                      : t("slower", "chậm hơn")
                  }`}{" "}
              · {prior.race_date}.{" "}
              {t(
                "Courses and conditions can vary between editions.",
                "Đường đua và điều kiện có thể khác giữa các năm."
              )}
            </p>
          )}
          {detail && (
            <RaceCourseContext
              context={detail.course_context}
              resultYear={Number(recorded.race_date.slice(0, 4))}
              lang={lang}
              onChooseCourse={choose}
              onRetry={refresh}
            />
          )}
          {!recorded.is_dnf && field && (
            <section>
              <h4>
                {t("Historical field", "Kết quả chung")} · {field.year} ·{" "}
                {field.distance_label}
              </h4>
              {field.finishers != null && (
                <p>
                  {field.finishers} {t("finishers", "VĐV về đích")}
                </p>
              )}
              {field.winner_time && (
                <p>
                  {t("Winner", "VĐV về nhất")}: {field.winner_time}
                </p>
              )}
              {field.percentiles?.overall?.p50 && (
                <p>
                  {t("Median finish", "Thời gian trung vị")}:{" "}
                  {field.percentiles.overall.p50}
                </p>
              )}
            </section>
          )}
        </section>
      </div>
    </dialog>
  );
}
