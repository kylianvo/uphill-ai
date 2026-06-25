import asyncio
from backend.services.plan_generator import PlanGenerator
from backend.config import settings

async def main():
    race_info = {"name": "Test Race", "date": "2026-10-10", "terrain": "trail"}
    user_profile = {"age": 30}
    workouts = await PlanGenerator.generate_plan_workouts(
        plan_id=1,
        user_profile=user_profile,
        race_info=race_info,
        total_weeks=2,
        api_key=settings.GEMINI_API_KEY
    )
    print(f"Generated {len(workouts)} workouts")
    if len(workouts) > 0:
        print(workouts[0])

asyncio.run(main())
