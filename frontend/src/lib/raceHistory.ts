export type RoadKey = "5k" | "10k" | "hm" | "fm";
export type RoadPR = {
  time_sec: number;
  stale: boolean;
  result_id?: number;
  date?: string;
};
export type RaceClaim = {
  id: number;
  source: "utmb" | "vbm";
  display_name: string;
  sync_status: string;
  sync_error?: string | null;
  verified: boolean;
  verification_methods: string[];
  meta?: { indexes?: Array<{ piCategory?: string; index?: number }> };
};
export type RaceResult = {
  id: number;
  claim_id: number | null;
  source: string;
  race_name: string;
  race_date: string;
  discipline: string;
  distance_km: number;
  elevation_gain_m: number | null;
  finish_time_sec: number | null;
  is_dnf: boolean;
  bib: string | null;
  selected: boolean;
  hidden: boolean;
  user_note: string | null;
  verified: boolean;
  verification_methods: string[];
  rank_overall?: number | null;
  total_overall?: number | null;
  location?: string | null;
  result_url?: string | null;
  rank_gender?: number | null;
  total_gender?: number | null;
  rank_age_group?: number | null;
  total_age_group?: number | null;
};
export type RaceHistory = {
  claims: RaceClaim[];
  results: RaceResult[];
  summary: {
    trail_finishes: number;
    trail_dnfs: number;
    ultras: number;
    longest_finish: RaceResult | null;
    road_prs?: Partial<Record<RoadKey, RoadPR | null>>;
    road_hm_pr: { time_sec: number; stale: boolean } | null;
    road_fm_pr: { time_sec: number; stale: boolean } | null;
  };
};

export function safeResultUrl(value: string | null | undefined): string | null {
  if (!value) return null;
  try {
    const url = new URL(value);
    return ["http:", "https:"].includes(url.protocol) &&
      url.hostname &&
      !url.username &&
      !url.password
      ? url.href
      : null;
  } catch {
    return null;
  }
}

export function manualResultPayload(
  draft: Record<string, string | boolean>,
  lang: "en" | "vi" = "en"
): Record<string, unknown> {
  const t = (en: string, vi: string) => (lang === "en" ? en : vi);
  const value: Record<string, unknown> = {};
  for (const [key, max] of [
    ["race_name", 200],
    ["location", 200],
    ["bib", 100],
    ["result_url", 2048],
    ["user_note", 2000],
  ] as const) {
    const text = String(draft[key] ?? "").trim();
    if (text.length > max)
      throw new Error(
        t(
          "Check the length of the result fields.",
          "Kiểm tra độ dài các thông tin kết quả."
        )
      );
    value[key] = text || null;
  }
  if (
    !value.race_name ||
    !/^\d{4}-\d{2}-\d{2}$/.test(String(draft.race_date)) ||
    !["road", "trail"].includes(String(draft.discipline))
  )
    throw new Error(
      t(
        "Enter the race name, date, and discipline.",
        "Nhập tên, ngày và loại Race."
      )
    );
  value.race_date = draft.race_date;
  value.discipline = draft.discipline;
  const km = Number(draft.distance_km);
  if (!Number.isFinite(km) || km <= 0 || km > 1000)
    throw new Error(
      t(
        "Enter a distance between 0 and 1,000 km.",
        "Nhập cự ly lớn hơn 0 và không quá 1.000 km."
      )
    );
  value.distance_km = km;
  const gain = String(draft.elevation_gain_m ?? "").trim();
  if (gain && (!Number.isFinite(Number(gain)) || Number(gain) < 0))
    throw new Error(
      t(
        "Elevation must be zero or a positive number.",
        "D+ phải là số không âm."
      )
    );
  value.elevation_gain_m = gain ? Number(gain) : null;
  value.is_dnf = draft.is_dnf === true;
  value.finish_time_sec = null;
  if (!value.is_dnf) {
    const parts = String(draft.finish_time ?? "")
      .trim()
      .split(":");
    if (
      parts.length < 2 ||
      parts.length > 3 ||
      parts.some((p) => !/^\d+$/.test(p)) ||
      parts.slice(1).some((p) => Number(p) >= 60)
    )
      throw new Error(
        t(
          "Enter finish time as h:mm:ss or mm:ss.",
          "Nhập thời gian theo h:mm:ss hoặc mm:ss."
        )
      );
    const numbers = parts.map(Number);
    const seconds =
      numbers.length === 3
        ? numbers[0] * 3600 + numbers[1] * 60 + numbers[2]
        : numbers[0] * 60 + numbers[1];
    if (!Number.isSafeInteger(seconds) || seconds <= 0)
      throw new Error(
        t("Finish time must be greater than zero.", "Thời gian phải lớn hơn 0.")
      );
    value.finish_time_sec = seconds;
  }
  for (const group of ["overall", "gender", "age_group"]) {
    for (const prefix of ["rank", "total"]) {
      const key = `${prefix}_${group}`,
        text = String(draft[key] ?? "").trim();
      if (
        text &&
        (!/^\d+$/.test(text) ||
          !Number.isSafeInteger(Number(text)) ||
          Number(text) < 1)
      )
        throw new Error(
          t(
            "Rank and finishers must be positive whole numbers.",
            "Thứ hạng và số VĐV phải là số nguyên dương."
          )
        );
      value[key] = text ? Number(text) : null;
    }
    const rank = value[`rank_${group}`],
      total = value[`total_${group}`];
    if (rank !== null && total !== null && Number(rank) > Number(total))
      throw new Error(
        t(
          "Rank cannot exceed the number of finishers.",
          "Thứ hạng không được vượt số VĐV về đích."
        )
      );
  }
  if (value.result_url && !safeResultUrl(String(value.result_url)))
    throw new Error(
      t(
        "Use an http or https result link without credentials.",
        "Dùng link http hoặc https, không kèm thông tin đăng nhập."
      )
    );
  return value;
}

export type RaceCourse = {
  id: number;
  race_name: string;
  distance_label: string;
  distance_km: number;
  elevation_gain_m: number | null;
  location: string | null;
  terrain: string[];
  key_climbs: string[];
  climate: {
    avg_temp_c?: number | string;
    humidity_pct?: number | string;
    season?: string;
    notes?: string;
  };
  runner_reviews: string[];
  source_label: string | null;
  source_urls: string[];
  verified_at: string | null;
  edition_year: number | null;
  edition_status: string;
};
export type CourseContext = {
  status: string;
  course: RaceCourse | null;
  candidates: Array<{ id: number; race_name: string; distance_label: string }>;
  message: string | null;
};
export type RaceDetail = {
  result: RaceResult;
  performance: {
    overall_top_pct: number | null;
    gender_top_pct: number | null;
    age_group_top_pct: number | null;
    average_pace_sec_km: number | null;
    road_pb_key: string | null;
  };
  previous_finish: {
    result_id: number;
    race_date: string;
    finish_time_sec: number;
    delta_sec: number;
  } | null;
  course_context: CourseContext;
  historical_field: {
    year?: number;
    distance_label?: string;
    finishers?: number;
    winner_time?: string;
    percentiles?: { overall?: { p50?: string } };
  } | null;
};

export function formatNumber(n: number, lang: "en" | "vi"): string {
  return new Intl.NumberFormat(lang === "vi" ? "vi-VN" : "en-US").format(n);
}

export function formatKm(km: number): string {
  return String(Math.round(km * 10) / 10);
}

export function formatPace(secPerKm: number): string {
  const s = Math.round(secPerKm);
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
}
