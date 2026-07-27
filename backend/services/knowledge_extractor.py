"""
Knowledge Extractor Service
────────────────────────────
Queries NotebookLM on 8 targeted topics, then uses Gemini to structure
each response into JSON knowledge cards, which are saved to the DB.
"""

import asyncio
import json
import re
from typing import Any

import google.generativeai as genai
from pydantic import BaseModel
from tavily import TavilyClient

from services.kb_distiller import _gemini_structured

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

OUTPUT CONTRACT: Return ONLY a valid JSON array. NEVER include markdown fences or explanation.
Each card MUST have exactly these fields:
- "chapter_title": Short, punchy title (max 8 words, no punctuation at end)
- "summary": 2–3 sentences explaining the concept clearly
- "key_points": Array of 3–5 specific, actionable bullet points (strings, start with a verb)
- "tags": Array of 2–4 lowercase keyword tags (e.g. "zone2", "heart-rate", "recovery", "fueling")
- "topic": Exactly one of: Training, Nutrition, Recovery, Pacing, Mindset, Gear
- "source_label": "Uphill Athlete Podcasts"

Convert the source summary below into 3–6 cards, one per distinct concept, principle, or piece of advice.
NEVER add a fact, statistic, or claim that isn't present in the source summary — restructure it, don't extend it.

Topic category for this batch: {topic}
Source summary:
{source_text}
"""


async def extract_knowledge_cards(
    notebook_id: str,
    auth_json: str,
    api_key: str,
    status_holder: dict[str, Any],
) -> int:
    """
    Full extraction pipeline:
      For each topic → query NotebookLM → structure with Gemini → save to DB.
    Updates status_holder in place so the API can stream progress.
    Returns total cards saved.
    """
    from db import clear_knowledge_cards, save_knowledge_cards
    from services.notebooklm_service import NotebookLmService

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
        status_holder.update(
            {
                "status": "extracting",
                "current_topic": topic_name,
                "progress": idx,
                "total": total_topics,
            }
        )
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
            print("[KnowledgeExtractor][Gemini] --- PROMPT START ---")
            print(prompt[:1000])
            print("[KnowledgeExtractor][Gemini] --- PROMPT END ---")
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

            saved_en = save_knowledge_cards(cards, lang="en")
            total_saved += saved_en
            print(f"[KnowledgeExtractor] Saved {saved_en} EN cards for {topic_name} (total EN so far: {total_saved})")

            # Translate to Vietnamese and save
            try:
                translated_cards = await translate_cards_to_vi_with_gemini(model, cards)
                saved_vi = save_knowledge_cards(translated_cards, lang="vi")
                print(f"[KnowledgeExtractor] Translated and saved {saved_vi} VI cards for {topic_name}")
            except Exception as tr_err:
                print(f"[KnowledgeExtractor] Failed to translate and save VI cards: {tr_err}")

            # Small delay between NLM queries to avoid rate limits
            await asyncio.sleep(1.5)

        except json.JSONDecodeError as e:
            print(f"[KnowledgeExtractor][Gemini] JSON parse error for {topic_name}: {e}")
            continue
        except Exception as e:
            print(f"[KnowledgeExtractor] Error processing {topic_name}: {e}")
            continue

    from datetime import datetime

    status_holder.update(
        {
            "status": "done",
            "current_topic": None,
            "card_count": total_saved,
            "last_extracted": datetime.utcnow().isoformat(),
            "progress": total_topics,
            "total": total_topics,
        }
    )
    print(f"[KnowledgeExtractor] Extraction complete. Total EN cards: {total_saved}")
    return total_saved


async def translate_cards_to_vi_with_gemini(model, cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    translated = []
    for card in cards:
        prompt = f"""
You are an expert sports translator. Translate the following running coaching knowledge card into Vietnamese.

OUTPUT CONTRACT: Return ONLY a JSON object with the exact same keys as the input — "chapter_title", "summary", "key_points", "tags", "topic", "source_label". NEVER wrap it in a markdown code block.

Rules:
1. Core physiological/running terms ("Zone 2", "AeT", "AnT", "Pace", "Resting HR", "Max HR") MUST remain in English.
2. Keep the "topic" and "source_label" fields exactly as they are in English.
3. Keep the "tags" list elements in English.
4. Start "key_points" bullet points with an active verb in Vietnamese.
5. Translations MUST sound natural, professional, and elite-coaching oriented — NEVER a literal word-for-word translation.

Card to translate:
{json.dumps(card, indent=2, ensure_ascii=False)}
"""
        try:
            # Wrap the blocking generate_content call in an async thread to prevent blocking the async loop
            response = await asyncio.to_thread(model.generate_content, prompt)
            text = response.text.strip()
            if text.startswith("```"):
                lines = text.split("\n")
                if lines[0].startswith("```json"):
                    text = "\n".join(lines[1:-1])
                else:
                    text = "\n".join(lines[1:-1])
            translated_card = json.loads(text.strip())
            # Maintain structural integrity
            translated_card["topic"] = card["topic"]
            translated_card["source_label"] = card["source_label"]
            translated_card["tags"] = card["tags"]
            translated.append(translated_card)
        except Exception as e:
            print(f"[KnowledgeExtractor] Error translating card: {e}")
            # Fallback to copy the card as-is so we don't drop it
            translated.append(
                {
                    "chapter_title": f"[VI] {card['chapter_title']}",
                    "summary": card["summary"],
                    "key_points": card["key_points"],
                    "tags": card["tags"],
                    "topic": card["topic"],
                    "source_label": card["source_label"],
                }
            )
    return translated


# ─── Podcast episode knowledge cards (live web discovery) ────────────────────
# Distinct from extract_knowledge_cards above (which sweeps a NotebookLM notebook
# on 8 fixed topics and does a full clear+rebuild): this finds NEW Evoke Endurance
# trail/ultrarunning podcast ("Evokecast") episodes directly from the web, fetches
# each episode's YouTube transcript, and structures it into cards with Gemini --
# incrementally appended, never clearing the existing library. An episode is
# tracked as "processed" via its YouTube URL used as source_label
# (db.get_knowledge_card_source_labels).
#
# Two-hop discovery, confirmed live (not just theoretical): the Evokecast listing
# page links to per-episode pages (evokeendurance.com/resources/<slug>/) whose
# plain <a> links survive Tavily's markdown extraction fine -- but each episode's
# embedded YouTube player is a lazy-loaded iframe (`data-src="https://www.youtube.com
# /embed/<id>?feature=oembed"`, real `src` is a placeholder image) that Tavily's
# extraction strips entirely, since it converts pages to readable text/markdown, not
# raw DOM. So: Tavily discovers episode page URLs (hop 1); a direct HTTP fetch of
# each episode page's raw HTML (hop 2, bypassing Tavily) finds the actual embedded
# video, since the iframe's `data-src` attribute is plain text in the raw markup.

EVOKE_PODCAST_URL = "https://evokeendurance.com/media-type/evokecast/?_sports=trail-ultrarunning"
ALLOWED_TOPICS = ("Training", "Nutrition", "Recovery", "Pacing", "Mindset", "Gear")
# Safety cap: a first run against a listing page with many linked episodes could
# otherwise fire dozens of transcript fetches + Gemini calls in one go.
_MAX_EPISODES_PER_RUN = 15
_EPISODE_PAGE_URL_RE = re.compile(r"https://evokeendurance\.com/resources/([\w-]+)/")
_YOUTUBE_URL_RE = re.compile(r"https?://(?:www\.)?(?:youtube\.com/(?:watch\?v=|embed/|shorts/)[\w-]+|youtu\.be/[\w-]+)")
_HTTP_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}
# Non-episode paths that match the /resources/<slug>/ shape but aren't episode
# pages (pagination, the listing/filter root itself).
_NON_EPISODE_SLUGS = ("page",)


class PodcastKnowledgeCard(BaseModel):
    chapter_title: str
    summary: str
    key_points: list[str]
    tags: list[str]
    topic: str


class PodcastKnowledgeCardList(BaseModel):
    cards: list[PodcastKnowledgeCard]


_PODCAST_CARD_ASK = (
    "You are structuring a podcast episode transcript into knowledge cards for a trail/mountain "
    "running training app. Each card must have exactly: chapter_title (short, punchy, max 8 words, "
    "no ending punctuation), summary (2-3 sentences explaining the concept clearly), key_points "
    "(3-5 specific actionable bullet points, each starting with a verb), tags (2-4 lowercase keyword "
    "tags), topic (exactly one of Training, Nutrition, Recovery, Pacing, Mindset, Gear). Extract 3-8 "
    "cards, one per distinct concept, principle, or piece of advice actually discussed. NEVER add a "
    "fact, statistic, or claim not present in the transcript -- restructure it, don't extend it. Write "
    "every field in clear English only -- never any other language.\n\nEpisode transcript:\n"
)


def _find_episode_page_urls(text: str) -> list[str]:
    """Distinct evokeendurance.com/resources/<slug>/ episode page URLs from the
    Evokecast listing page's content (excludes pagination/non-episode paths)."""
    seen: list[str] = []
    for match in _EPISODE_PAGE_URL_RE.finditer(text or ""):
        url, slug = match.group(0), match.group(1)
        if slug in _NON_EPISODE_SLUGS or url in seen:
            continue
        seen.append(url)
    return seen


def _find_youtube_links(text: str) -> list[str]:
    """Distinct YouTube video URLs found in arbitrary page content (matches inside
    an iframe's data-src attribute just as well as a plain link, since this only
    looks for the URL substring, not a specific surrounding tag)."""
    seen: list[str] = []
    for match in _YOUTUBE_URL_RE.finditer(text or ""):
        url = match.group(0)
        if url not in seen:
            seen.append(url)
    return seen


async def _fetch_raw_html(url: str) -> str:
    """Direct HTTP fetch of a page's raw HTML -- deliberately NOT via Tavily, since
    Tavily's markdown extraction strips iframe embeds that only carry a lazy-loaded
    `data-src` attribute in the raw markup (see module note above)."""
    import httpx

    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
        response = await client.get(url, headers=_HTTP_HEADERS)
        response.raise_for_status()
        return response.text


async def discover_podcast_knowledge_web(api_key: str, tavily_api_key: str, status_holder: dict) -> list[dict]:
    """Discover new Evokecast episode pages (via Tavily), find each one's embedded
    YouTube video (via a direct HTML fetch), skip episodes already processed, fetch
    each new episode's transcript, and structure it into knowledge cards with
    Gemini. Incremental -- an empty result (no new episodes this run) is a normal,
    valid outcome, same posture as the KB web-discovery sources."""
    import db
    from services.rag_service import RagService

    client = TavilyClient(api_key=tavily_api_key)
    known_source_labels = db.get_knowledge_card_source_labels()

    try:
        extraction = await asyncio.to_thread(client.extract, urls=[EVOKE_PODCAST_URL], extract_depth="advanced")
    except Exception as e:
        print(f"[KnowledgeExtractor][podcast-web] Failed to fetch Evokecast listing page, continuing: {e}")
        return []

    page_results = extraction.get("results", [])
    if not page_results:
        print("[KnowledgeExtractor][podcast-web] Evokecast listing page fetch returned no content.")
        return []

    episode_page_urls = _find_episode_page_urls(page_results[0].get("raw_content", ""))[:_MAX_EPISODES_PER_RUN]
    new_cards: list[dict] = []

    for i, episode_page_url in enumerate(episode_page_urls):
        status_holder.update(
            {"current_topic": f"podcast: {episode_page_url}", "progress": i, "total": len(episode_page_urls)}
        )
        try:
            html = await _fetch_raw_html(episode_page_url)
        except Exception as e:
            print(f"[KnowledgeExtractor][podcast-web] Failed to fetch episode page '{episode_page_url}': {e}")
            continue
        video_urls = _find_youtube_links(html)
        if not video_urls:
            continue  # this resource has no embedded video (e.g. a text-only article)
        video_url = video_urls[0]
        if video_url in known_source_labels:
            continue  # already processed this episode
        try:
            transcript = await asyncio.to_thread(RagService.get_youtube_transcript, video_url)
        except Exception as e:
            print(f"[KnowledgeExtractor][podcast-web] Transcript fetch failed for '{video_url}', continuing: {e}")
            continue
        content = transcript.get("content", "")
        if len(content.strip()) < 200:
            continue
        try:
            structured = await _gemini_structured(
                api_key, _PODCAST_CARD_ASK + content[:20000], PodcastKnowledgeCardList
            )
        except Exception as e:
            print(f"[KnowledgeExtractor][podcast-web] Structuring failed for '{video_url}', continuing: {e}")
            continue
        for card in structured.get("cards", []):
            topic = card.get("topic") if card.get("topic") in ALLOWED_TOPICS else "Training"
            new_cards.append(
                {
                    "chapter_title": card.get("chapter_title", ""),
                    "summary": card.get("summary", ""),
                    "key_points": card.get("key_points", []),
                    "tags": card.get("tags", []),
                    "topic": topic,
                    "source_label": video_url,
                }
            )
        known_source_labels.add(video_url)
        await asyncio.sleep(1.5)  # rate-limit courtesy, same pacing as the KB sweeps
    return new_cards


async def save_podcast_knowledge_cards(cards: list[dict], api_key: str) -> int:
    """Insert-only append of newly-discovered podcast knowledge cards -- never
    clears/replaces the existing library, unlike extract_knowledge_cards's full
    NotebookLM rebuild. Bilingual: also translates + saves the Vietnamese versions,
    matching this table's existing en/vi convention. Returns the EN count saved (VI
    translation failures are logged but don't fail the whole save -- the EN cards
    are still worth keeping)."""
    from db import save_knowledge_cards

    if not cards:
        return 0
    saved_en = save_knowledge_cards(cards, lang="en")
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")
        translated_cards = await translate_cards_to_vi_with_gemini(model, cards)
        save_knowledge_cards(translated_cards, lang="vi")
    except Exception as e:
        print(f"[KnowledgeExtractor][podcast-web] VI translation/save failed, EN cards still saved: {e}")
    return saved_en
