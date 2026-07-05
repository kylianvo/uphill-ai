import hashlib
import json
from typing import Any

from pydantic import BaseModel

from config import settings
from services.notebooklm_service import NotebookLmService


class NutritionParams(BaseModel):
    distance_km: float | None = None
    elevation_gain_m: float | None = None
    target_time_hours: float | None = None
    weather_temp: str | None = None
    preferred_brands: str | None = None
    target_carb_h: float | None = None
    target_sodium_h: float | None = None
    preferred_format: list[str] | None = None
    athlete_level: str | None = None
    additional_context: str | None = None
    user_profile: str | None = None
    active_plan_context: str | None = None


_NUTRITION_CACHE: dict[str, str] = {}


class NutritionPlannerService:
    def __init__(self):
        self.notebook_id = settings.NOTEBOOKLM_NUTRITION_ID

    def _generate_cache_key(self, params: NutritionParams) -> str:
        param_dict = params.model_dump()
        dict_str = json.dumps(param_dict, sort_keys=True)
        return hashlib.md5(dict_str.encode()).hexdigest()

    async def generate_plan(self, user_profile: str, params: NutritionParams) -> dict[str, Any]:
        cache_key = self._generate_cache_key(params)
        if cache_key in _NUTRITION_CACHE:
            print("[NutritionPlanner] Cache HIT! Returning instant response.")
            return json.loads(_NUTRITION_CACHE[cache_key])

        # 1. Determine target macros
        target_carb = params.target_carb_h if params.target_carb_h else 60.0
        target_sodium = 500.0
        if params.target_sodium_h:
            target_sodium = params.target_sodium_h
        elif params.weather_temp and "hot" in params.weather_temp.lower():
            target_sodium = 1000.0

        # 2. Build JSON-structured query
        nlm_query = f"""You are an expert ultra-endurance nutrition coach searching your documents for a race nutrition plan.

OUTPUT CONTRACT: You MUST output your response EXACTLY as a valid JSON object matching the schema below. NEVER include markdown formatting (like ```json), conversational filler, or plain text outside the JSON. NEVER use emoji icons.
NEVER invent a product, brand, or macro figure that isn't in your documents — if you're not confident a number is accurate, calculate it from the stated Nutrition Goals below instead of guessing.
BRAND CONSTRAINT: If "Preferred Brands" below is not empty, every product in "products" MUST be from that brand (or brands) only — NEVER substitute a different brand. The ONLY exception: if your documents contain zero matching products for the requested brand/format, say so explicitly as the first entry in "tips" and then recommend the closest available alternative from your documents.

Schema:
{{
  "products": [
    {{
      "brand": "Brand Name",
      "name": "Full Product Name (Flavor if applicable)",
      "total_quantity": 4,
      "carbs_per_unit": 27.0,
      "sodium_per_unit": 420.0,
      "protein_per_unit": 2.0,
      "tech_notes": "Key science/tech notes about this product"
    }}
  ],
  "hourly_plan": [
    {{
      "hour": 1,
      "action": "Short action description e.g. 1x Gel A + 1x Gel B",
      "carbs": 57.0,
      "sodium": 545.0
    }}
  ],
  "tips": [
    "Concise critical tip 1",
    "Concise critical tip 2",
    "Concise critical tip 3"
  ]
}}

Search your documents for specific products matching these brands/formats, calculate the required macros, and suggest a race nutrition plan.

Race Profile:
- Distance: {params.distance_km or 'Unknown'} km
- Elevation Gain: {params.elevation_gain_m or 'Unknown'} m
- Target Time: {params.target_time_hours or 'Unknown'} hours
- Weather: {params.weather_temp or 'Unknown'}
- Athlete Level: {params.athlete_level or 'Unknown'}
- Preferences: Brands: {params.preferred_brands or 'Any'}, Format: {', '.join(params.preferred_format) if params.preferred_format else 'Any'}
- Additional Context: {params.additional_context or 'None'}
- Athlete Profile Details: {params.user_profile or user_profile}
- Current Active Plan: {params.active_plan_context or 'None'}

Nutrition Goals:
- Target Carbs/Hour: {target_carb}g
- Target Sodium/Hour: {target_sodium}mg
"""

        nlm_response = ""
        auth_json = settings.NOTEBOOKLM_AUTH_JSON
        if auth_json:
            try:
                print(f"[NutritionPlanner] Cache MISS. Querying NotebookLM ({self.notebook_id})...")
                nlm_response = await NotebookLmService.query_notebook(
                    notebook_id=self.notebook_id, auth_json=auth_json, query=nlm_query, service="nutrition_lab"
                )
                print(f"[NutritionPlanner] NotebookLM Output Response:\n{nlm_response}\n{'-'*40}")

                # Strip markdown fences if present
                cleaned = nlm_response.strip()
                if cleaned.startswith("```json"):
                    cleaned = cleaned[7:]
                if cleaned.startswith("```"):
                    cleaned = cleaned[3:]
                if cleaned.endswith("```"):
                    cleaned = cleaned[:-3]
                cleaned = cleaned.strip()

                try:
                    parsed = json.loads(cleaned)
                except json.JSONDecodeError:
                    print("[NutritionPlanner] WARNING: Could not parse JSON. Returning fallback.")
                    parsed = {
                        "products": [],
                        "hourly_plan": [],
                        "tips": ["Could not parse nutrition plan from NotebookLM. Please try again."],
                    }
                    cleaned = json.dumps(parsed)

                _NUTRITION_CACHE[cache_key] = cleaned
                return parsed
            except Exception as e:
                print(f"[NutritionPlanner] NotebookLM query failed: {e}")
                return {"products": [], "hourly_plan": [], "tips": [f"Could not retrieve plan: {str(e)}"]}
        else:
            return {"products": [], "hourly_plan": [], "tips": ["Error: NotebookLM Auth JSON is missing."]}


nutrition_planner = NutritionPlannerService()
