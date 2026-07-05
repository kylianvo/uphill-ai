import hashlib
import json
from typing import Any

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

    async def generate_plan(self, user_profile: str, params: GearParams) -> dict[str, Any]:
        cache_key = self._generate_cache_key(params)
        if cache_key in _GEAR_CACHE:
            print("[GearPlanner] Cache HIT! Returning instant response.")
            return json.loads(_GEAR_CACHE[cache_key])

        terrain_str = ", ".join(params.terrain) if params.terrain else "Not specified"

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

Return your top 5 shoe recommendations matching this exact criteria:
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

        nlm_response = ""
        auth_json = settings.NOTEBOOKLM_AUTH_JSON
        if auth_json:
            try:
                print(f"[GearPlanner] Cache MISS. Querying NotebookLM ({self.notebook_id})...")
                print(f"[GearPlanner] NotebookLM Input Query:\n{nlm_query}\n{'-'*40}")

                # Single LLM call!
                nlm_response = await NotebookLmService.query_notebook(
                    notebook_id=self.notebook_id, auth_json=auth_json, query=nlm_query, service="gear_finder"
                )
                print(f"[GearPlanner] NotebookLM Output Response:\n{nlm_response}\n{'-'*40}")

                # Clean up response in case it has markdown ticks
                cleaned_response = nlm_response.strip()
                if cleaned_response.startswith("```json"):
                    cleaned_response = cleaned_response[7:]
                if cleaned_response.startswith("```"):
                    cleaned_response = cleaned_response[3:]
                if cleaned_response.endswith("```"):
                    cleaned_response = cleaned_response[:-3]
                cleaned_response = cleaned_response.strip()

                # Validate JSON parse
                try:
                    parsed_json = json.loads(cleaned_response)
                except json.JSONDecodeError:
                    print("[GearPlanner] WARNING: Could not parse response as JSON. Returning fallback.")
                    # Return a fallback JSON structure in case the LLM failed to format
                    parsed_json = {
                        "recommendations": [],
                        "tips": ["Could not parse recommendations from NotebookLM. Please try again."],
                    }
                    cleaned_response = json.dumps(parsed_json)

                # Save to cache
                _GEAR_CACHE[cache_key] = cleaned_response
                return parsed_json
            except Exception as e:
                print(f"[GearPlanner] NotebookLM query failed: {e}")
                return {
                    "recommendations": [],
                    "tips": [f"Could not retrieve recommendations from NotebookLM: {str(e)}"],
                }
        else:
            return {"recommendations": [], "tips": ["Error: NotebookLM Auth JSON is missing."]}


gear_planner = GearPlannerService()
