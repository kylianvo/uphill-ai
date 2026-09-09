import asyncio
import hashlib
import json
from typing import Any

from google import genai
from google.genai import types
from pydantic import BaseModel

from config import settings
from log_utils import get_logger

_logger = get_logger(__name__)


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

        try:
            return await self._generate_with_gemini(user_profile, params, cache_key)
        except Exception as e:
            _logger.error(
                "gemini engine failed",
                extra={
                    "fields": {
                        "service": "nutrition_lab",
                        "engine": "gemini",
                        "event": "engine_failed",
                        "error": str(e),
                    }
                },
                exc_info=True,
            )
            return {
                "products": [],
                "hourly_plan": [],
                "tips": [f"Could not retrieve plan: {e}"],
            }

    async def _generate_with_gemini(self, user_profile: str, params: NutritionParams, cache_key: str) -> dict[str, Any]:
        import time

        from db import get_kb_chunks
        from services.kb_context import render_catalog_context, render_principles_context
        from telemetry import rag_attempts_total, rag_latency_seconds

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

        _logger.info(
            "gemini prompt sent",
            extra={
                "fields": {
                    "service": "nutrition_lab",
                    "engine": "gemini",
                    "event": "prompt_sent",
                    "chars_sent": len(prompt),
                    "catalog_entries": len(catalog_chunks),
                    "principle_entries": len(principle_chunks),
                }
            },
        )
        client = genai.Client(api_key=api_key)

        rag_attempts_total.labels(service="nutrition_lab", engine="gemini", status="attempt").inc()
        _start = time.time()
        try:
            response = await asyncio.to_thread(
                client.models.generate_content,
                model=settings.GEMINI_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=NutritionResponse,
                    temperature=0.2,
                    thinking_config=types.ThinkingConfig(thinking_level=settings.GEMINI_THINKING_LEVEL),
                ),
            )
            _latency = time.time() - _start
            rag_latency_seconds.labels(service="nutrition_lab", engine="gemini").observe(_latency)
            rag_attempts_total.labels(service="nutrition_lab", engine="gemini", status="success").inc()
            _logger.info(
                "gemini response received",
                extra={
                    "fields": {
                        "service": "nutrition_lab",
                        "engine": "gemini",
                        "event": "response_received",
                        "chars_received": len(response.text),
                        "latency_ms": round(_latency * 1000),
                    }
                },
            )
        except Exception as _gemini_ex:
            rag_attempts_total.labels(service="nutrition_lab", engine="gemini", status="error").inc()
            _logger.error(
                "gemini request failed",
                extra={
                    "fields": {
                        "service": "nutrition_lab",
                        "engine": "gemini",
                        "event": "error",
                        "error": str(_gemini_ex),
                    }
                },
                exc_info=True,
            )
            raise

        parsed = json.loads(response.text)
        _NUTRITION_CACHE[cache_key] = json.dumps(parsed)
        _logger.info(
            "gemini products parsed",
            extra={
                "fields": {
                    "service": "nutrition_lab",
                    "engine": "gemini",
                    "event": "parsed",
                    "product_count": len(parsed.get("products", [])),
                }
            },
        )
        return parsed


nutrition_planner = NutritionPlannerService()
