"""
Workout Type Extractor
──────────────────────
For each workout type, queries NotebookLM for grounded content from the
Training for the Uphill Athlete source material, then uses Gemini to
structure it into the exact schema the frontend WorkoutCard expects.
"""

import asyncio
import json
from typing import Any

# Zone → hex color (matches frontend workoutLibrary.ts)
ZONE_COLORS: dict[str, str] = {
    "easy": "#3b82f6",
    "moderate": "#10b981",
    "tempo": "#f59e0b",
    "hard": "#ef4444",
    "strength": "#8b5cf6",
    "cross": "#14b8a6",
    "rest": "#94a3b8",
}

WORKOUT_TYPE_QUERIES: list[dict[str, Any]] = [
    {
        "type_key": "easy_run",
        "display_name": "Easy Run",
        "zone": "easy",
        "query": (
            "Explain easy aerobic running — Zone 1 and Zone 2 effort — in the context of trail and mountain "
            "running training. What is the correct pace, heart rate, and feel? How should you execute an easy "
            "run session? What are the key physiological adaptations it develops? What are the most common "
            "mistakes athletes make (usually running too fast) and warnings to heed?"
        ),
    },
    {
        "type_key": "long_run",
        "display_name": "Long Run",
        "zone": "moderate",
        "query": (
            "Explain the long run for trail and mountain runners. How should it be paced (Zone 2), how long "
            "should it be, how should an athlete fuel during it, and how does it fit into the weekly training "
            "structure? What are the key physiological benefits and what mistakes do athletes typically make "
            "with long runs (going too hard, bonking, skipping fueling)?"
        ),
    },
    {
        "type_key": "tempo_run",
        "display_name": "Tempo Run",
        "zone": "tempo",
        "query": (
            "Explain tempo running and lactate threshold training for trail and mountain runners. What is the "
            "correct effort level (comfortably hard, Zone 3-4), how is a tempo session structured (warm-up, "
            "main set, cooldown), and what pace or HR defines tempo effort? What physiological adaptations "
            "does it build and what are the key warnings (going too fast, skipping warm-up)?"
        ),
    },
    {
        "type_key": "interval",
        "display_name": "Intervals",
        "zone": "hard",
        "query": (
            "Explain high-intensity interval training for trail and mountain runners — VO2max intervals, "
            "track repeats, or uphill intervals. How are they structured (reps, rest, intensity), what "
            "physiological adaptations do they produce, and what are the critical warnings around recovery, "
            "overtraining risk, and when intervals are appropriate in a training cycle?"
        ),
    },
    {
        "type_key": "hill_repeat",
        "display_name": "Hill Repeats",
        "zone": "hard",
        "query": (
            "Explain hill repeats for trail and mountain runners. How are they performed, what gradient and "
            "duration is appropriate, what heart rate or effort zone do they target, and how do they differ "
            "from hill sprints? What specific muscles and adaptations do they develop for uphill racing, "
            "and what are the key execution warnings?"
        ),
    },
    {
        "type_key": "hill_sprint",
        "display_name": "Hill Sprints",
        "zone": "hard",
        "query": (
            "Explain hill sprints (short 8-12 second maximal efforts) for trail and mountain runners. "
            "How are they executed (gradient, duration, full recovery between reps), what neuromuscular "
            "adaptations do they develop, and how do they differ from longer hill repeats? What are the "
            "key warnings around form, recovery, and frequency?"
        ),
    },
    {
        "type_key": "me_session",
        "display_name": "ME Session",
        "zone": "strength",
        "query": (
            "Explain Muscular Endurance (ME) training for trail and mountain runners — specifically the "
            "gym-based ME work described in Training for the Uphill Athlete: weighted step-ups, single-leg "
            "squats, box steps. How is an ME session structured, what load and rep range is used, what "
            "muscles does it target, and how does it translate to uphill running performance? What are "
            "the key warnings about scheduling and fatigue?"
        ),
    },
    {
        "type_key": "strength",
        "display_name": "Strength Training",
        "zone": "strength",
        "query": (
            "Explain general strength training for trail and mountain runners — compound lifts, injury "
            "prevention work, and running-specific strength. What exercises are most important, how should "
            "sessions be structured (sets, reps, weight), and what are the key benefits for running economy "
            "and injury prevention? What are the warnings about scheduling relative to key run sessions?"
        ),
    },
    {
        "type_key": "recovery_run",
        "display_name": "Recovery Run",
        "zone": "easy",
        "query": (
            "Explain recovery running for trail and mountain runners. How slow and short should a recovery "
            "run be, what heart rate or effort zone defines it (strictly Zone 1), how does it differ from "
            "an easy aerobic run, and what are its physiological benefits? What is the key warning about "
            "athletes accidentally turning recovery runs into aerobic work?"
        ),
    },
    {
        "type_key": "fartlek",
        "display_name": "Fartlek",
        "zone": "moderate",
        "query": (
            "Explain fartlek training for trail and mountain runners — unstructured speed play mixing easy "
            "running with surges of effort. How is it executed, how does it differ from formal intervals, "
            "what adaptations does it build, and when in a training block is it most useful? What are "
            "the key warnings?"
        ),
    },
    {
        "type_key": "cross_training",
        "display_name": "Cross-Training",
        "zone": "cross",
        "query": (
            "Explain cross-training (cycling, swimming, elliptical, hiking) for trail and mountain runners. "
            "When is it appropriate to use instead of running, how should intensity be matched to a run "
            "session it replaces, what aerobic adaptations carry over to running, and what are the "
            "limitations (it does not fully replace running's neural adaptations)?"
        ),
    },
    {
        "type_key": "rest",
        "display_name": "Rest Day",
        "zone": "rest",
        "query": (
            "Explain the importance of planned rest days in trail and mountain running training. Why are "
            "rest days essential for adaptation (not just recovery), what should an athlete actually do "
            "on a rest day (very gentle movement, sleep, nutrition), and what is the key warning about "
            "athletes adding bonus runs or cross-training on rest days?"
        ),
    },
]

GEMINI_STRUCTURE_PROMPT = """
You are structuring training knowledge into workout type descriptions for a trail running coaching app.

The source material is from "Training for the Uphill Athlete" podcasts and books by Scott Johnston and Kilian Jornet.

OUTPUT CONTRACT: Return ONLY a valid JSON object. NEVER include markdown fences or explanation.
The JSON MUST have exactly these fields:
- "type_key": "{type_key}" (use exactly this value)
- "display_name": "{display_name}" (use exactly this value)
- "zone": "{zone}" (use exactly this value — do not change)
- "color": "{color}" (use exactly this value — do not change)
- "overview": 2-3 sentences. What is this workout type at its core? Audience: experienced trail runners. Tone: expert, direct.
- "execution": 3-5 sentences describing exactly how to perform this workout. Include effort level, structure, duration guidance.
- "benefit": 2-3 sentences on the specific physiological adaptations this workout produces. Be precise (e.g. "raises lactate threshold", "builds mitochondrial density").
- "warning": 1-3 sentences on the most important mistake or risk with this workout type. Be direct.

NEVER add a fact, statistic, or claim that isn't grounded in the source content below — restructure it, don't extend it.

Convert the following NotebookLM response into the JSON object above for workout type: "{display_name}"

Source content:
{source_text}
"""

TRANSLATE_PROMPT = """
You are an expert sports translator. Translate the following workout type description into Vietnamese.

OUTPUT CONTRACT: Return ONLY a JSON object with the EXACT same keys as the input. NEVER wrap it in markdown code blocks.

Rules:
1. Technical terms MUST remain in English: Zone 1, Zone 2, Zone 3, Zone 4, Zone 5, RPE, HR, AeT, AnT, Pace, VO2max, ME, HIIT, GPS.
2. "type_key", "zone", and "color" MUST remain unchanged (English/hex).
3. "display_name" should be translated, or kept if it's a standard term (e.g. "Tempo Run" stays as "Tempo Run").
4. Translations MUST sound natural and professional for a Vietnamese trail running audience — NEVER a literal word-for-word translation.

Object to translate:
{source_json}
"""


async def extract_workout_types(
    notebook_id: str,
    auth_json: str,
    api_key: str,
    status_holder: dict[str, Any],
) -> int:
    """
    For each workout type:
      1. Query NotebookLM for grounded content
      2. Structure with Gemini into the required schema
      3. Save to DB (en + vi)
    Updates status_holder in place. Returns total types saved.
    """
    from db import save_workout_types
    from services.notebooklm_service import NotebookLmService

    try:
        import google.generativeai as genai
        from google.generativeai import client as genai_client
    except ImportError:
        status_holder.update({"status": "error", "message": "google-generativeai not installed"})
        return 0

    model = genai.GenerativeModel(model_name="gemini-2.5-flash")
    mgr = genai_client._ClientManager()
    mgr.configure(api_key=api_key)
    model._client = mgr.get_default_client("generative")

    total = len(WORKOUT_TYPE_QUERIES)
    total_saved = 0

    for idx, wtype in enumerate(WORKOUT_TYPE_QUERIES):
        status_holder.update(
            {
                "status": "extracting",
                "current_type": wtype["display_name"],
                "progress": idx,
                "total": total,
            }
        )
        print(f"[WorkoutTypeExtractor] Querying NLM for: {wtype['display_name']}")

        try:
            nlm_text = await NotebookLmService.query_notebook(
                notebook_id=notebook_id,
                auth_json=auth_json,
                query=wtype["query"],
                service="workout_type_extractor",
            )

            if not nlm_text or len(nlm_text.strip()) < 50:
                print(f"[WorkoutTypeExtractor] Empty response for {wtype['display_name']}, skipping.")
                continue

            color = ZONE_COLORS.get(wtype["zone"], "#6b7280")
            prompt = GEMINI_STRUCTURE_PROMPT.format(
                type_key=wtype["type_key"],
                display_name=wtype["display_name"],
                zone=wtype["zone"],
                color=color,
                source_text=nlm_text[:8000],
            )

            response = await asyncio.to_thread(
                model.generate_content,
                prompt,
                generation_config={"response_mime_type": "application/json"},
            )
            raw = response.text.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            raw = raw.strip()

            entry = json.loads(raw)
            # Enforce non-negotiables
            entry["type_key"] = wtype["type_key"]
            entry["display_name"] = wtype["display_name"]
            entry["zone"] = wtype["zone"]
            entry["color"] = color

            save_workout_types([entry], lang="en")
            total_saved += 1
            print(f"[WorkoutTypeExtractor] Saved EN entry for {wtype['display_name']}")

            # Translate to Vietnamese
            try:
                vi_entry = await _translate_to_vi(model, entry)
                save_workout_types([vi_entry], lang="vi")
                print(f"[WorkoutTypeExtractor] Saved VI entry for {wtype['display_name']}")
            except Exception as tr_err:
                print(f"[WorkoutTypeExtractor] VI translation failed for {wtype['display_name']}: {tr_err}")

            await asyncio.sleep(1.5)

        except json.JSONDecodeError as e:
            print(f"[WorkoutTypeExtractor] JSON parse error for {wtype['display_name']}: {e}")
        except Exception as e:
            print(f"[WorkoutTypeExtractor] Error for {wtype['display_name']}: {e}")

    from datetime import datetime

    status_holder.update(
        {
            "status": "done",
            "current_type": None,
            "type_count": total_saved,
            "last_extracted": datetime.utcnow().isoformat(),
            "progress": total,
            "total": total,
        }
    )
    print(f"[WorkoutTypeExtractor] Done. {total_saved} types saved.")
    return total_saved


async def _translate_to_vi(model: Any, entry: dict[str, Any]) -> dict[str, Any]:
    prompt = TRANSLATE_PROMPT.format(source_json=json.dumps(entry, ensure_ascii=False, indent=2))
    response = await asyncio.to_thread(model.generate_content, prompt)
    text = response.text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1])
    vi = json.loads(text.strip())
    # Enforce structural integrity
    vi["type_key"] = entry["type_key"]
    vi["zone"] = entry["zone"]
    vi["color"] = entry["color"]
    return vi
