import os
import hashlib
import json
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from config import settings
from services.notebooklm_service import NotebookLmService

class NutritionParams(BaseModel):
    distance_km: Optional[float] = None
    elevation_gain_m: Optional[float] = None
    target_time_hours: Optional[float] = None
    weather_temp: Optional[str] = None
    preferred_brands: Optional[str] = None
    target_carb_h: Optional[float] = None
    target_sodium_h: Optional[float] = None
    preferred_format: Optional[List[str]] = None
    athlete_level: Optional[str] = None
    additional_context: Optional[str] = None
    user_profile: Optional[str] = None
    active_plan_context: Optional[str] = None

_NUTRITION_CACHE: Dict[str, str] = {}

class NutritionPlannerService:
    def __init__(self):
        self.notebook_id = settings.NOTEBOOKLM_NUTRITION_ID

    def _generate_cache_key(self, params: NutritionParams) -> str:
        param_dict = params.model_dump()
        dict_str = json.dumps(param_dict, sort_keys=True)
        return hashlib.md5(dict_str.encode()).hexdigest()

    async def generate_plan(self, user_profile: str, params: NutritionParams) -> str:
        cache_key = self._generate_cache_key(params)
        if cache_key in _NUTRITION_CACHE:
            print("[NutritionPlanner] Cache HIT! Returning instant response.")
            return _NUTRITION_CACHE[cache_key]

        # 1. Determine target macros
        target_carb = params.target_carb_h if params.target_carb_h else 60.0
        
        target_sodium = 500.0
        if params.target_sodium_h:
            target_sodium = params.target_sodium_h
        elif params.weather_temp and "hot" in params.weather_temp.lower():
            target_sodium = 1000.0

        # 2. Query NotebookLM
        nlm_query = f"""You are an expert ultra-endurance nutrition coach.
Please provide a highly detailed nutrition suggestion based on the following profile and goals:

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

Please search your documents for specific products matching these brands/formats, calculate the required macros, and suggest a race nutrition plan.

TASK:
Reformat and summarize your suggestions into a highly visual, ultra-concise Markdown response.
You MUST use Markdown tables for almost everything. Do NOT use plain text paragraphs.

Strict Format Requirements:

### 1. Total Requirements
(Create a Markdown table with columns: Product Name, Brand, Total Quantity)

### 2. Hourly Fueling Strategy
(Create a Markdown table with columns: Hour, Action/Consumption, Carbs (g), Sodium (mg))

### 3. Product Breakdown
(Create a Markdown table with columns: Brand, Type, Carbs (g), Sodium (mg), Protein (g), Special Tech/Notes)

### 4. Critical Tips
(Provide 2-3 extremely short bullet points)

CRITICAL: Output ONLY the tables and bullet points. No introductory text. No conversational filler. Do not use emoji icons. Focus heavily on {params.preferred_brands or 'any brands'} if specified.
"""
        
        nlm_response = ""
        auth_json = settings.NOTEBOOKLM_AUTH_JSON
        if auth_json:
            try:
                print(f"[NutritionPlanner] Cache MISS. Querying NotebookLM ({self.notebook_id})...")
                print(f"[NutritionPlanner] NotebookLM Input Query:\n{nlm_query}\n{'-'*40}")
                
                nlm_response = await NotebookLmService.query_notebook(
                    notebook_id=self.notebook_id,
                    auth_json=auth_json,
                    query=nlm_query
                )
                print(f"[NutritionPlanner] NotebookLM Output Response:\n{nlm_response}\n{'-'*40}")
                
                if "Could not retrieve" not in nlm_response:
                    _NUTRITION_CACHE[cache_key] = nlm_response
                    
                return nlm_response
            except Exception as e:
                print(f"[NutritionPlanner] NotebookLM query failed: {e}")
                return f"Could not retrieve suggestions from NotebookLM: {str(e)}"
        else:
            return "Error: NotebookLM Auth JSON is missing."

nutrition_planner = NutritionPlannerService()
