"""
Knowledge Extractor Service
────────────────────────────
Queries NotebookLM on 8 targeted topics, then uses Gemini to structure
each response into JSON knowledge cards, which are saved to the DB.
"""
import json
import asyncio
from typing import List, Dict, Any

# Topic queries sent to NotebookLM — each focuses on a distinct area
TOPIC_QUERIES = [
    {
        "topic": "Training",
        "label": "Aerobic Base & Zone 2 Training",
        "query": (
            "Summarize everything discussed about aerobic base building and Zone 2 training. "
            "Include: what Zone 2 is, how to identify it (HR, pace, talk test), why it matters, "
            "how much weekly volume should be Zone 2, common mistakes, and any specific protocols mentioned."
        ),
    },
    {
        "topic": "Training",
        "label": "Muscular Endurance & Strength Training",
        "query": (
            "Summarize everything about muscular endurance training and strength work for mountain/trail runners. "
            "Include: box step-ups, weighted carries, hill repeats, gym exercises, periodization of strength, "
            "and how it complements aerobic training."
        ),
    },
    {
        "topic": "Training",
        "label": "Periodization & Training Planning",
        "query": (
            "Summarize the training periodization concepts discussed — Base, Build, Peak, Taper phases. "
            "Include: how long each phase should be, how to structure a training week, "
            "how to decide weekly volume, and the 80/20 intensity principle."
        ),
    },
    {
        "topic": "Pacing",
        "label": "Race Strategy & Pacing",
        "query": (
            "Summarize all race strategy and pacing advice from these podcasts. "
            "Include: how to set a target pace, uphill vs downhill pacing strategy, "
            "positive/negative split debate, how to handle aid stations, late-race fatigue management."
        ),
    },
    {
        "topic": "Nutrition",
        "label": "Nutrition & In-Race Fueling",
        "query": (
            "Summarize all nutrition and fueling advice — both training nutrition and race-day fueling. "
            "Include: carbohydrate intake targets (g/hr), sodium/electrolyte guidelines, "
            "fluid intake, gut training, real food vs gels, and pre-race nutrition."
        ),
    },
    {
        "topic": "Recovery",
        "label": "Recovery & Regeneration",
        "query": (
            "Summarize all recovery advice discussed in these podcasts. "
            "Include: sleep importance, active vs passive recovery, recovery nutrition, "
            "how to know when you're recovered, deload weeks, and signs of overtraining."
        ),
    },
    {
        "topic": "Mindset",
        "label": "Mental Training & Race Mindset",
        "query": (
            "Summarize the mental and psychological aspects of training and racing discussed. "
            "Include: how to deal with suffering, goal-setting, self-talk strategies, "
            "fear of failure, pre-race anxiety, and staying motivated during long training blocks."
        ),
    },
    {
        "topic": "Gear",
        "label": "Gear & Equipment for Mountain Running",
        "query": (
            "Summarize all gear and equipment recommendations discussed. "
            "Include: shoe selection (trail vs road, drop, cushioning), poles, packs/vests, "
            "clothing for weather, trekking poles use in races, and any specific product recommendations."
        ),
    },
]

GEMINI_STRUCTURE_PROMPT = """
You are structuring podcast transcript summaries into knowledge cards for a training app.

Convert the following topic summary into a JSON array of knowledge cards.
Each card represents one distinct concept, principle, or piece of advice.
Aim for 3–6 cards from this topic.

Each card MUST have exactly these fields:
- "chapter_title": Short, punchy title (max 8 words, no punctuation at end)
- "summary": 2–3 sentences explaining the concept clearly
- "key_points": Array of 3–5 specific, actionable bullet points (strings, start with a verb)
- "tags": Array of 2–4 lowercase keyword tags (e.g. "zone2", "heart-rate", "recovery", "fueling")
- "topic": Exactly one of: Training, Nutrition, Recovery, Pacing, Mindset, Gear
- "source_label": "Uphill Athlete Podcasts"

Topic category for this batch: {topic}
Source summary:
{source_text}

Output ONLY a valid JSON array. No markdown, no explanation, no code fences.
"""

async def extract_knowledge_cards(
    notebook_id: str,
    auth_json: str,
    api_key: str,
    status_holder: Dict[str, Any],
) -> int:
    """
    Full extraction pipeline:
      For each topic → query NotebookLM → structure with Gemini → save to DB.
    Updates status_holder in place so the API can stream progress.
    Returns total cards saved.
    """
    from services.notebooklm_service import NotebookLmService
    from db import clear_knowledge_cards, save_knowledge_cards

    try:
        import google.generativeai as genai
        from google.generativeai import client as genai_client
    except ImportError:
        status_holder.update({"status": "error", "message": "google-generativeai not installed"})
        return 0

    # Configure Gemini
    model = genai.GenerativeModel(model_name="gemini-2.5-flash")
    mgr = genai_client._ClientManager()
    mgr.configure(api_key=api_key)
    model._client = mgr.get_default_client("generative")

    # Clear existing cards before fresh extraction
    clear_knowledge_cards()
    total_saved = 0
    total_topics = len(TOPIC_QUERIES)

    for idx, topic_def in enumerate(TOPIC_QUERIES):
        topic_name = topic_def["label"]
        status_holder.update({
            "status": "extracting",
            "current_topic": topic_name,
            "progress": idx,
            "total": total_topics,
        })
        print(f"[KnowledgeExtractor] Querying NLM for: {topic_name}")

        try:
            # Step 1: Query NotebookLM
            print(f"[KnowledgeExtractor][NotebookLM] Querying notebook {notebook_id[:8]}... Topic: {topic_name}")
            print(f"[KnowledgeExtractor][NotebookLM] Query: {topic_def['query'][:200]}...")
            nlm_text = await NotebookLmService.query_notebook(
                notebook_id=notebook_id,
                auth_json=auth_json,
                query=topic_def["query"],
            )
            print(f"[KnowledgeExtractor][NotebookLM] Response received ({len(nlm_text)} chars) for {topic_name}")

            if not nlm_text or len(nlm_text.strip()) < 50:
                print(f"[KnowledgeExtractor][NotebookLM] Empty/short response for {topic_name}, skipping.")
                continue

            # Step 2: Structure with Gemini
            prompt = GEMINI_STRUCTURE_PROMPT.format(
                topic=topic_def["topic"],
                source_text=nlm_text[:8000],  # Trim to avoid token limits
            )
            print(f"[KnowledgeExtractor][Gemini] Sending structure prompt ({len(prompt)} chars) for {topic_name}")
            print(f"[KnowledgeExtractor][Gemini] --- PROMPT START ---")
            print(prompt[:1000])
            print(f"[KnowledgeExtractor][Gemini] --- PROMPT END ---")
            import asyncio
            response = await asyncio.to_thread(
                model.generate_content,
                prompt,
                generation_config={"response_mime_type": "application/json"},
            )
            raw = response.text.strip()
            print(f"[KnowledgeExtractor][Gemini] Response received ({len(raw)} chars) for {topic_name}")

            # Clean up any accidental markdown fences
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            raw = raw.strip()

            cards = json.loads(raw)
            if not isinstance(cards, list):
                print(f"[KnowledgeExtractor] Gemini returned non-list for {topic_name}")
                continue

            # Force the correct topic field (don't trust the model)
            for card in cards:
                card["topic"] = topic_def["topic"]
                card["source_label"] = "Uphill Athlete Podcasts"

            saved = save_knowledge_cards(cards)
            total_saved += saved
            print(f"[KnowledgeExtractor] Saved {saved} cards for {topic_name} (total so far: {total_saved})")

            # Small delay between NLM queries to avoid rate limits
            await asyncio.sleep(1.5)

        except json.JSONDecodeError as e:
            print(f"[KnowledgeExtractor][Gemini] JSON parse error for {topic_name}: {e}")
            continue
        except Exception as e:
            print(f"[KnowledgeExtractor] Error processing {topic_name}: {e}")
            continue

    from datetime import datetime
    status_holder.update({
        "status": "done",
        "current_topic": None,
        "card_count": total_saved,
        "last_extracted": datetime.utcnow().isoformat(),
        "progress": total_topics,
        "total": total_topics,
    })
    print(f"[KnowledgeExtractor] Extraction complete. Total cards: {total_saved}")
    return total_saved
