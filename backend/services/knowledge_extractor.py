"""
Knowledge Extractor Service
────────────────────────────
Discovers new Evoke Endurance podcast episodes, fetches each episode's YouTube
transcript, and uses Gemini to structure it into bilingual knowledge cards saved
to the DB. Incremental and insert-only: it never clears the existing library.
"""

import asyncio
import json
import re
from typing import Any

from google import genai
from google.genai import types
from pydantic import BaseModel
from tavily import TavilyClient

from config import settings
from services.kb_distiller import _gemini_structured


async def translate_cards_to_vi_with_gemini(client, cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
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
            response = await asyncio.to_thread(
                client.models.generate_content,
                model=settings.GEMINI_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    thinking_config=types.ThinkingConfig(thinking_level=settings.GEMINI_THINKING_LEVEL)
                ),
            )
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
# Incremental discovery path (
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
    clears or replaces the existing library. Bilingual: also translates + saves the Vietnamese versions,
    matching this table's existing en/vi convention. Returns the EN count saved (VI
    translation failures are logged but don't fail the whole save -- the EN cards
    are still worth keeping)."""
    from db import save_knowledge_cards

    if not cards:
        return 0
    saved_en = save_knowledge_cards(cards, lang="en")
    try:
        client = genai.Client(api_key=api_key)
        translated_cards = await translate_cards_to_vi_with_gemini(client, cards)
        save_knowledge_cards(translated_cards, lang="vi")
    except Exception as e:
        print(f"[KnowledgeExtractor][podcast-web] VI translation/save failed, EN cards still saved: {e}")
    return saved_en
