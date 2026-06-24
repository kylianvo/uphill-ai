import os
import hashlib
import json
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from config import settings
from services.notebooklm_service import NotebookLmService

class GearParams(BaseModel):
    surface: Optional[str] = None
    cushioning: Optional[str] = None
    width: Optional[str] = None
    carbon_plate: Optional[str] = None
    budget: Optional[str] = None
    terrain: Optional[List[str]] = None
    use_case: Optional[str] = None
    preferred_brands: Optional[str] = None
    additional_context: Optional[str] = None
    race_distance: Optional[str] = None

# Simple in-memory cache to skip NotebookLM calls for exact same queries
_GEAR_CACHE: Dict[str, str] = {}

class GearPlannerService:
    def __init__(self):
        self.notebook_id = settings.NOTEBOOKLM_GEAR_ID

    def _generate_cache_key(self, params: GearParams) -> str:
        param_dict = params.model_dump()
        # Sort keys to ensure deterministic hashing
        dict_str = json.dumps(param_dict, sort_keys=True)
        return hashlib.md5(dict_str.encode()).hexdigest()

    async def generate_plan(self, user_profile: str, params: GearParams) -> str:
        cache_key = self._generate_cache_key(params)
        if cache_key in _GEAR_CACHE:
            print("[GearPlanner] Cache HIT! Returning instant response.")
            return _GEAR_CACHE[cache_key]

        terrain_str = ", ".join(params.terrain) if params.terrain else "Not specified"
        
        # Merged Query: We now ask NotebookLM to do the strict Markdown formatting directly.
        nlm_query = f"""You are an expert running shoe specialist. 
Please search your documents for shoes that match the following specific criteria:

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

TASK: 
Reformat and summarize your top 5 shoe recommendations based on these exact criteria.
You MUST output your response exactly in the following highly visual, ultra-concise Markdown format. 
Do NOT use plain text paragraphs or conversational filler. Output ONLY the tables and bullet points.

### Top Recommendations
(Create a Markdown table with columns: Model, Brand, Cushion & Foam (e.g. EVA, PEBA, TPE), Drop/Specs, Price, Best For/Pros)

### Critical Gear Tips
(Provide 2-3 extremely short bullet points based on the user's specific context, e.g., sizing up for trails)
"""

        nlm_response = ""
        auth_json = settings.NOTEBOOKLM_AUTH_JSON
        if auth_json:
            try:
                print(f"[GearPlanner] Cache MISS. Querying NotebookLM ({self.notebook_id})...")
                print(f"[GearPlanner] NotebookLM Input Query:\n{nlm_query}\n{'-'*40}")
                
                # Single LLM call!
                nlm_response = await NotebookLmService.query_notebook(
                    notebook_id=self.notebook_id,
                    auth_json=auth_json,
                    query=nlm_query
                )
                print(f"[GearPlanner] NotebookLM Output Response:\n{nlm_response}\n{'-'*40}")
                
                # Save to cache
                if "Could not retrieve" not in nlm_response:
                    _GEAR_CACHE[cache_key] = nlm_response

                return nlm_response
            except Exception as e:
                print(f"[GearPlanner] NotebookLM query failed: {e}")
                return f"Could not retrieve recommendations from NotebookLM: {str(e)}"
        else:
            return "Error: NotebookLM Auth JSON is missing."

gear_planner = GearPlannerService()
