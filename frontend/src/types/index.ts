export interface Message {
  role: "user" | "assistant";
  content: string;
}

export interface ParsedSummary {
  distance_km: number;
  duration_mins: number;
  elevation_gain_m: number;
  avg_hr?: number;
  avg_speed?: string;
  source_type: "FIT" | "GPX" | null;
}

export interface RagSource {
  id: number;
  title: string;
  type: "pdf" | "url" | "youtube";
  url_path?: string;
  summary?: string;
  created_at: string;
}

export interface Workout {
  id: number;
  plan_id: number;
  week_number: number;
  day_of_week: string;
  phase: string;
  title: string;
  type: string;
  duration_minutes: number;
  distance_km?: number;
  target_zone: string;
  target_hr_range?: string;
  target_pace?: string;
  // Range strings from the backend ("7.3-9.3" %, "8.1-9.2" kph); plans
  // generated before the range change still carry plain numbers.
  treadmill_incline: number | string;
  treadmill_speed: number | string;
  elevation_gain_m: number;
  grade_percent: number;
  description?: string;
  fueling_tip?: string;
  is_completed: number;
}

export interface ActivePlan {
  id: number;
  race_name: string;
  race_date: string;
  goal_type: string;
  target_time_hours?: number;
  total_weeks: number;
  course_distance_km?: number;
  course_elevation_gain_m?: number;
}

export interface PacedCheckpoint {
  name: string;
  distance_km: number;
  elevation_m: number;
  target_pace: string;
  split_time: string;
  cumulative_time_mins: number;
  flat_equivalent_km: number;
  grade_pct: number;
}

export interface FuelStrategy {
  targets: {
    carbs_grams_per_hour: number;
    sodium_mg_per_hour: number;
    fluid_ml_per_hour: number;
    carb_complexity: string;
  };
  recommended_hourly_recipe: Array<{
    product: string;
    qty: number;
    type: string;
  }>;
  recipe_totals: {
    carbs_grams: number;
    sodium_mg: number;
    caffeine_mg: number;
    fluid_ml: number;
  };
  warnings: string[];
}

export interface Shoe {
  id: number;
  brand: string;
  model: string;
  surface: string;
  cushioning: string;
  drop_mm: number;
  plate: string;
  width: string;
  review_summary: string;
}

export interface User {
  id: number;
  email: string;
  name: string;
  role: "admin" | "user";
  age?: number;
  current_weekly_km?: number;
  max_hr?: number;
  resting_hr?: number;
  aet_hr?: number;
  ant_hr?: number;
  use_treadmill?: number;
  gemini_api_key?: string;
  notebooklm_notebook_id?: string;
  notebooklm_auth_json?: string;
  zone2_pace_min?: string;
  zone2_pace_max?: string;
  provider?: string;
  has_password?: boolean;
}
