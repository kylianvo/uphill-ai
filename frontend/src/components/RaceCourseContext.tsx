"use client";
import type { CourseContext } from "../lib/raceHistory";
import { safeResultUrl } from "../lib/raceHistory";
import styles from "./RaceDetail.module.css";
export default function RaceCourseContext({
  context,
  resultYear,
  lang,
  onChooseCourse,
  onRetry,
}: {
  context: CourseContext;
  resultYear: number;
  lang: "en" | "vi";
  onChooseCourse: (id: number) => void;
  onRetry: () => void;
}) {
  const t = (en: string, vi: string) => (lang === "en" ? en : vi);
  const course = context.course;
  if (!course) {
    if (context.status === "ambiguous")
      return (
        <div>
          <p>
            {t(
              "Choose the course for this review. Your race record stays the same.",
              "Chọn đường đua để xem thông tin. Kết quả Race của bạn vẫn giữ nguyên."
            )}
          </p>
          {context.candidates.map((c) => (
            <button
              className={styles.button}
              key={c.id}
              onClick={() => onChooseCourse(c.id)}
            >
              {c.race_name} · {c.distance_label}
            </button>
          ))}
        </div>
      );
    if (context.status === "unavailable")
      return (
        <div>
          <p>
            {t(
              "Course context could not be loaded.",
              "Chưa tải được thông tin đường đua."
            )}
          </p>
          <button className={styles.button} onClick={onRetry}>
            {t("Retry", "Thử lại")}
          </button>
        </div>
      );
    return (
      <p>{t("No course context available", "Chưa có thông tin đường đua")}</p>
    );
  }
  const facts = (heading: string, values: string[]) =>
    values.length > 0 ? (
      <section>
        <h4>{heading}</h4>
        {values.map((v, i) => (
          <p key={i}>{v}</p>
        ))}
      </section>
    ) : null;
  return (
    <div className={styles.context}>
      <h4>
        {course.race_name} · {course.distance_label}
      </h4>
      {course.edition_status === "different" ? (
        <p className={styles.notice}>
          {t(
            `Course profile: ${course.edition_year}; your result: ${resultYear}`,
            `Thông tin đường đua: ${course.edition_year}; kết quả của bạn: ${resultYear}`
          )}
        </p>
      ) : course.edition_status === "unknown" ? (
        <p>
          {t("Course edition not recorded", "Chưa ghi nhận năm của đường đua")}
        </p>
      ) : null}
      {course.location && <p>{course.location}</p>}
      {course.elevation_gain_m !== null && (
        <p>
          {t("Course elevation gain", "D+ đường đua")}:{" "}
          {course.elevation_gain_m.toLocaleString()} m
        </p>
      )}
      {facts(t("Terrain", "Địa hình"), course.terrain)}
      {facts(t("Key climbs", "Các đoạn leo chính"), course.key_climbs)}
      {Object.keys(course.climate).length > 0 && (
        <section>
          <h4>{t("Typical conditions", "Điều kiện thường gặp")}</h4>
          {course.climate.avg_temp_c !== undefined && (
            <p>
              {t("Average temperature", "Nhiệt độ trung bình")}:{" "}
              {course.climate.avg_temp_c} °C
            </p>
          )}
          {course.climate.humidity_pct !== undefined && (
            <p>
              {t("Humidity", "Độ ẩm")}: {course.climate.humidity_pct}
              {typeof course.climate.humidity_pct === "number" ? "%" : ""}
            </p>
          )}
          {course.climate.season && <p>{course.climate.season}</p>}
          {course.climate.notes && <p>{course.climate.notes}</p>}
        </section>
      )}
      {facts(t("Runner reviews", "Nhận xét của VĐV"), course.runner_reviews)}
      <footer>
        {course.source_label && (
          <p>
            {t("Source", "Nguồn")}: <span>{course.source_label}</span>
          </p>
        )}
        {course.verified_at && (
          <p>
            {t("Verified", "Kiểm tra")}: {course.verified_at}
          </p>
        )}
        {course.source_urls.map((source, i) => {
          const url = safeResultUrl(source);
          return url ? (
            <a key={i} href={url} target="_blank" rel="noopener noreferrer">
              {t("Course source", "Nguồn đường đua")} · {new URL(url).hostname}
            </a>
          ) : null;
        })}
      </footer>
    </div>
  );
}
