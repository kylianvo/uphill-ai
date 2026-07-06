import asyncio
import hashlib
import json
import traceback
from typing import Any

import google.generativeai as genai
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


class NutritionProduct(BaseModel):
    brand: str
    name: str
    total_quantity: int
    carbs_per_unit: float
    sodium_per_unit: float
    protein_per_unit: float
    tech_notes: str


class HourlyStep(BaseModel):
    hour: int
    action: str
    carbs: float
    sodium: float


class NutritionResponse(BaseModel):
    products: list[NutritionProduct]
    hourly_plan: list[HourlyStep]
    tips: list[str]


_NUTRITION_CACHE: dict[str, str] = {}


class NutritionPlannerService:
    def __init__(self):
        self.notebook_id = settings.NOTEBOOKLM_NUTRITION_ID

    def _generate_cache_key(self, params: NutritionParams) -> str:
        param_dict = params.model_dump()
        dict_str = json.dumps(param_dict, sort_keys=True)
        return hashlib.md5(dict_str.encode()).hexdigest()

    @staticmethod
    def _macro_targets(params: NutritionParams) -> tuple[float, float]:
        target_carb = params.target_carb_h if params.target_carb_h else 60.0
        target_sodium = 500.0
        if params.target_sodium_h:
            target_sodium = params.target_sodium_h
        elif params.weather_temp and "hot" in params.weather_temp.lower():
            target_sodium = 1000.0
        return target_carb, target_sodium

    @staticmethod
    def _race_profile_block(
        user_profile: str, params: NutritionParams, target_carb: float, target_sodium: float
    ) -> str:
        return f"""Race Profile:
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

    async def generate_plan(self, user_profile: str, params: NutritionParams) -> dict[str, Any]:
        cache_key = self._generate_cache_key(params)
        if cache_key in _NUTRITION_CACHE:
            print("[NutritionPlanner] Cache HIT! Returning instant response.")
            return json.loads(_NUTRITION_CACHE[cache_key])

        order = ["gemini", "notebooklm"] if settings.RAG_ENGINE == "gemini" else ["notebooklm", "gemini"]
        last_error: Exception | None = None
        for engine_name in order:
            try:
                if engine_name == "gemini":
                    return await self._generate_with_gemini(user_profile, params, cache_key)
                return await self._generate_with_notebooklm(user_profile, params, cache_key)
            except Exception as e:
                print(f"[NutritionPlanner] {engine_name} engine failed: {e}\n{traceback.format_exc()}")
                last_error = e
        return {
            "products": [],
            "hourly_plan": [],
            "tips": [f"Could not retrieve plan: {last_error}"],
        }

    async def _generate_with_gemini(self, user_profile: str, params: NutritionParams, cache_key: str) -> dict[str, Any]:
        from db import get_kb_chunks
        from services.kb_context import render_catalog_context, render_principles_context

        api_key = settings.GEMINI_API_KEY
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is missing.")
        catalog_chunks = get_kb_chunks("nutrition", kind="catalog_item")
        if not catalog_chunks:
            raise RuntimeError("nutrition KB is empty — run POST /api/kb/distill or /api/kb/import first.")
        principle_chunks = get_kb_chunks("nutrition", kind="principle")
        catalog_context = render_catalog_context(catalog_chunks, "nutrition")
        principles_context = render_principles_context(principle_chunks, heading="FUELING SCIENCE PRINCIPLES")

        target_carb, target_sodium = self._macro_targets(params)
        prompt = f"""You are an expert ultra-endurance nutrition coach building a race nutrition plan.

{catalog_context}
{principles_context}
NEVER invent a product, brand, or macro figure that isn't in the knowledge base above — if you're not confident a number is accurate, calculate it from the stated Nutrition Goals below instead of guessing. NEVER use emoji icons.
BRAND CONSTRAINT: If "Preferred Brands" below is not empty, every product in "products" MUST be from that brand (or brands) only — NEVER substitute a different brand. The ONLY exception: if the knowledge base contains zero matching products for the requested brand/format, say so explicitly as the first entry in "tips" and then recommend the closest available alternative from the knowledge base.

Pick specific products from the knowledge base matching the requested brands/formats, calculate the required macros, and suggest a race nutrition plan with an hourly schedule and 3 concise critical tips.

{self._race_profile_block(user_profile, params, target_carb, target_sodium)}"""

        print(
            f"[NutritionPlanner][Gemini] Querying with {len(catalog_chunks)} products, {len(principle_chunks)} principles..."
        )
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = await asyncio.to_thread(
            model.generate_content,
            prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json", response_schema=NutritionResponse, temperature=0.2
            ),
        )
        parsed = json.loads(response.text)
        _NUTRITION_CACHE[cache_key] = json.dumps(parsed)
        print(f"[NutritionPlanner][Gemini] OK — {len(parsed.get('products', []))} products")
        return parsed

    async def _generate_with_notebooklm(
        self, user_profile: str, params: NutritionParams, cache_key: str
    ) -> dict[str, Any]:
        auth_json = settings.NOTEBOOKLM_AUTH_JSON
        if not auth_json:
            raise RuntimeError("NotebookLM Auth JSON is missing.")

        target_carb, target_sodium = self._macro_targets(params)
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

{self._race_profile_block(user_profile, params, target_carb, target_sodium)}"""

        print(f"[NutritionPlanner] Querying NotebookLM ({self.notebook_id})...")
        nlm_response = await NotebookLmService.query_notebook(
            notebook_id=self.notebook_id, auth_json=auth_json, query=nlm_query, service="nutrition_lab"
        )

        # Clean up response in case it has markdown ticks
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
            print("[NutritionPlanner] WARNING: Could not parse response as JSON. Returning fallback.")
            parsed = {
                "products": [],
                "hourly_plan": [],
                "tips": ["Could not parse nutrition plan from NotebookLM. Please try again."],
            }
            cleaned = json.dumps(parsed)

        _NUTRITION_CACHE[cache_key] = cleaned
        return parsed


nutrition_planner = NutritionPlannerService()
