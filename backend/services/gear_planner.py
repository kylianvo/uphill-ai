import asyncio
import hashlib
import json
import traceback
from typing import Any

import google.generativeai as genai
from pydantic import BaseModel

from config import settings
from services.notebooklm_service import NotebookLmService


class GearParams(BaseModel):
    surface: str | None = None
    cushioning: str | None = None
    width: str | None = None
    carbon_plate: str | None = None
    budget: str | None = None
    terrain: list[str] | None = None
    use_case: str | None = None
    preferred_brands: str | None = None
    additional_context: str | None = None
    race_distance: str | None = None
    user_profile: str | None = None
    active_plan_context: str | None = None


class GearRecommendation(BaseModel):
    model: str
    brand: str
    foam_material: str
    outsole_compound: str
    lug_depth: str
    drop: str
    stack: str
    price: str
    pros: str
    cons: str


class GearResponse(BaseModel):
    recommendations: list[GearRecommendation]
    tips: list[str]


# Simple in-memory cache to skip NotebookLM calls for exact same queries
_GEAR_CACHE: dict[str, str] = {}


class GearPlannerService:
    def __init__(self):
        self.notebook_id = settings.NOTEBOOKLM_GEAR_ID

    def _generate_cache_key(self, params: GearParams) -> str:
        param_dict = params.model_dump()
        # Sort keys to ensure deterministic hashing
        dict_str = json.dumps(param_dict, sort_keys=True)
        return hashlib.md5(dict_str.encode()).hexdigest()

    @staticmethod
    def _criteria_block(params: GearParams) -> str:
        terrain_str = ", ".join(params.terrain) if params.terrain else "Not specified"
        return f"""Return your top 5 shoe recommendations matching this exact criteria:
- Surface: {params.surface or 'Unknown'}
- Cushioning: {params.cushioning or 'Any'}
- Width: {params.width or 'Standard'}
- Carbon Plate: {params.carbon_plate or 'No preference'}
- Budget: {params.budget or 'Any'}
- Trail Terrain (if applicable): {terrain_str}
- Road Use Case (if applicable): {params.use_case or 'Not specified'}
- Race Distance (if applicable): {params.race_distance or 'Not specified'}
- Preferred Brands: {params.preferred_brands or 'Any'}
- Special Requirements/Context: {params.additional_context or 'None'}
- Athlete Profile: {params.user_profile or 'Not specified'}
- Current Training Plan / Goal: {params.active_plan_context or 'Not specified'}
"""

    async def generate_plan(self, user_profile: str, params: GearParams) -> dict[str, Any]:
        cache_key = self._generate_cache_key(params)
        if cache_key in _GEAR_CACHE:
            print("[GearPlanner] Cache HIT! Returning instant response.")
            return json.loads(_GEAR_CACHE[cache_key])

        order = ["gemini", "notebooklm"] if settings.RAG_ENGINE == "gemini" else ["notebooklm", "gemini"]
        last_error: Exception | None = None
        for engine_name in order:
            try:
                if engine_name == "gemini":
                    return await self._generate_with_gemini(params, cache_key)
                return await self._generate_with_notebooklm(params, cache_key)
            except Exception as e:
                print(f"[GearPlanner] {engine_name} engine failed: {e}\n{traceback.format_exc()}")
                last_error = e
        return {
            "recommendations": [],
            "tips": [f"Could not retrieve recommendations: {last_error}"],
        }

    async def _generate_with_gemini(self, params: GearParams, cache_key: str) -> dict[str, Any]:
        import time

        from db import get_kb_chunks
        from services.kb_context import render_catalog_context
        from telemetry import rag_attempts_total, rag_latency_seconds

        api_key = settings.GEMINI_API_KEY
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is missing.")
        chunks = get_kb_chunks("gear", kind="catalog_item")
        if not chunks:
            # Never answer ungrounded — no KB means this engine refuses.
            raise RuntimeError("gear KB is empty — run POST /api/kb/distill or /api/kb/import first.")
        catalog_context = render_catalog_context(chunks, "gear")

        prompt = f"""You are an expert running shoe specialist recommending shoes that match an athlete's criteria.

{catalog_context}
NEVER invent a shoe model, spec, or price that isn't in the knowledge base above — if you're not confident a detail is accurate, omit that field or say so in "cons" rather than guessing.
BRAND CONSTRAINT: If "Preferred Brands" below is not empty, every recommendation MUST be from that brand (or brands) only — NEVER substitute a different brand. The ONLY exception: if the knowledge base contains zero matching shoes for the requested brand, say so explicitly in "tips" and then recommend the closest available alternative from the knowledge base.

Field guidance: "foam_material" names the foam ALONG WITH its material type in parentheses (e.g. ZoomX (PEBA), PWRRUN PB (PEBA), optiFOAM (EVA)); "outsole_compound" e.g. Vibram Megagrip, Contagrip, None for road; "lug_depth"/"drop"/"stack" in mm; "pros" is 2-3 short sentences on what the shoe is best for; "cons" is 1-2 short sentences on drawbacks or who shouldn't buy it; "tips" are 2 short gear tips based on user context.

{self._criteria_block(params)}"""

        print(f"[GearPlanner][Gemini] Querying with {len(chunks)} catalog entries...")
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")

        rag_attempts_total.labels(service="gear_finder", engine="gemini", status="attempt").inc()
        _start = time.time()
        try:
            response = await asyncio.to_thread(
                model.generate_content,
                prompt,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json", response_schema=GearResponse, temperature=0.2
                ),
            )
            rag_latency_seconds.labels(service="gear_finder", engine="gemini").observe(time.time() - _start)
            rag_attempts_total.labels(service="gear_finder", engine="gemini", status="success").inc()
        except Exception:
            rag_attempts_total.labels(service="gear_finder", engine="gemini", status="error").inc()
            raise

        parsed = json.loads(response.text)
        _GEAR_CACHE[cache_key] = json.dumps(parsed)
        print(f"[GearPlanner][Gemini] OK — {len(parsed.get('recommendations', []))} recommendations")
        return parsed

    async def _generate_with_notebooklm(self, params: GearParams, cache_key: str) -> dict[str, Any]:
        auth_json = settings.NOTEBOOKLM_AUTH_JSON
        if not auth_json:
            raise RuntimeError("NotebookLM Auth JSON is missing.")

        # Merged Query: Ask NotebookLM to do strict JSON formatting
        nlm_query = f"""You are an expert running shoe specialist searching your documents for shoes that match an athlete's criteria.

OUTPUT CONTRACT: You MUST output your response EXACTLY as a valid JSON object matching the schema below. NEVER include markdown formatting (like ```json), conversational filler, or plain text paragraphs outside the JSON.
NEVER invent a shoe model, spec, or price that isn't in your documents — if you're not confident a detail is accurate, omit that field or say so in "cons" rather than guessing.
BRAND CONSTRAINT: If "Preferred Brands" below is not empty, every recommendation MUST be from that brand (or brands) only — NEVER substitute a different brand. The ONLY exception: if your documents contain zero matching shoes for the requested brand, say so explicitly in "tips" and then recommend the closest available alternative from your documents.

Schema:
{{
  "recommendations": [
    {{
      "model": "Shoe Model Name",
      "brand": "Brand Name",
      "foam_material": "Name of the foam ALONG WITH its material type in parentheses (e.g. ZoomX (PEBA), PWRRUN PB (PEBA), optiFOAM (EVA))",
      "outsole_compound": "Name of outsole rubber (e.g. Vibram Megagrip, Contagrip, None for road)",
      "lug_depth": "Lug depth in mm (e.g. 4mm, 5mm, None for road)",
      "drop": "Drop in mm (e.g. 6mm)",
      "stack": "Stack height (e.g. 35mm/29mm)",
      "price": "$XXX",
      "pros": "2-3 short sentences about what the shoe is best for and its pros",
      "cons": "1-2 short sentences about the drawbacks or who shouldn't buy this shoe"
    }}
  ],
  "tips": [
    "Short gear tip 1 based on user context",
    "Short gear tip 2 based on user context"
  ]
}}

{self._criteria_block(params)}"""

        print(f"[GearPlanner] Querying NotebookLM ({self.notebook_id})...")
        nlm_response = await NotebookLmService.query_notebook(
            notebook_id=self.notebook_id, auth_json=auth_json, query=nlm_query, service="gear_finder"
        )

        # Clean up response in case it has markdown ticks
        cleaned_response = nlm_response.strip()
        if cleaned_response.startswith("```json"):
            cleaned_response = cleaned_response[7:]
        if cleaned_response.startswith("```"):
            cleaned_response = cleaned_response[3:]
        if cleaned_response.endswith("```"):
            cleaned_response = cleaned_response[:-3]
        cleaned_response = cleaned_response.strip()

        try:
            parsed_json = json.loads(cleaned_response)
        except json.JSONDecodeError:
            print("[GearPlanner] WARNING: Could not parse response as JSON. Returning fallback.")
            parsed_json = {
                "recommendations": [],
                "tips": ["Could not parse recommendations from NotebookLM. Please try again."],
            }
            cleaned_response = json.dumps(parsed_json)

        _GEAR_CACHE[cache_key] = cleaned_response
        return parsed_json


gear_planner = GearPlannerService()
