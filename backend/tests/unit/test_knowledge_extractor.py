import asyncio
from unittest.mock import AsyncMock, patch

from services import knowledge_extractor as ke


def test_find_episode_page_urls_extracts_distinct_slugs_and_skips_pagination():
    text = (
        "See https://evokeendurance.com/resources/kilian-jornet-on-training/ and "
        "https://evokeendurance.com/resources/paul-booth-nutrition/ and a duplicate "
        "https://evokeendurance.com/resources/kilian-jornet-on-training/ and "
        "pagination https://evokeendurance.com/resources/page/2/?_sports=trail-ultrarunning"
    )
    urls = ke._find_episode_page_urls(text)
    assert urls == [
        "https://evokeendurance.com/resources/kilian-jornet-on-training/",
        "https://evokeendurance.com/resources/paul-booth-nutrition/",
    ]


def test_find_episode_page_urls_returns_empty_for_no_links():
    assert ke._find_episode_page_urls("no episode links here") == []


def test_find_youtube_links_matches_inside_an_iframe_data_src_attribute():
    # Reproduces the real embed shape: a lazy-loaded iframe's data-src, not a plain link.
    html = (
        '<iframe data-src="https://www.youtube.com/embed/ms58TCaZ7po?feature=oembed" '
        'src="data:image/svg+xml;base64,abc"></iframe>'
    )
    assert ke._find_youtube_links(html) == ["https://www.youtube.com/embed/ms58TCaZ7po"]


def test_find_youtube_links_extracts_distinct_watch_and_short_urls():
    text = (
        "Check out https://www.youtube.com/watch?v=abc123 and also "
        "https://youtu.be/def456 plus a duplicate https://www.youtube.com/watch?v=abc123 "
        "and a shorts link https://youtube.com/shorts/ghi789"
    )
    links = ke._find_youtube_links(text)
    assert links == [
        "https://www.youtube.com/watch?v=abc123",
        "https://youtu.be/def456",
        "https://youtube.com/shorts/ghi789",
    ]


def test_find_youtube_links_returns_empty_for_no_links():
    assert ke._find_youtube_links("no links here at all") == []


def test_discover_podcast_knowledge_web_skips_already_processed_episode(monkeypatch):
    monkeypatch.setattr(ke, "_MAX_EPISODES_PER_RUN", 15)
    extraction = {
        "results": [
            {
                "raw_content": (
                    "https://evokeendurance.com/resources/known-episode/ and "
                    "https://evokeendurance.com/resources/new-episode/"
                ),
            }
        ]
    }
    html_by_url = {
        "https://evokeendurance.com/resources/known-episode/": (
            '<iframe data-src="https://www.youtube.com/embed/known111?feature=oembed"></iframe>'
        ),
        "https://evokeendurance.com/resources/new-episode/": (
            '<iframe data-src="https://www.youtube.com/embed/new222?feature=oembed"></iframe>'
        ),
    }
    transcript = {"title": "New Episode", "content": "x" * 500, "url_path": "https://www.youtube.com/embed/new222"}
    structured = {
        "cards": [
            {
                "chapter_title": "Fuel Early",
                "summary": "Start fueling in the first 30 minutes.",
                "key_points": ["Start eating early", "Don't wait for hunger"],
                "tags": ["fueling", "nutrition"],
                "topic": "Nutrition",
            }
        ]
    }

    async def fake_fetch_raw_html(url):
        return html_by_url[url]

    with (
        patch("db.get_knowledge_card_source_labels", return_value={"https://www.youtube.com/embed/known111"}),
        patch.object(ke, "TavilyClient") as tavily_cls,
        patch.object(ke, "_fetch_raw_html", side_effect=fake_fetch_raw_html),
        patch("services.rag_service.RagService.get_youtube_transcript", return_value=transcript),
        patch.object(ke, "_gemini_structured", new_callable=AsyncMock, return_value=structured),
        patch("asyncio.sleep", new_callable=AsyncMock),
    ):
        tavily_cls.return_value.extract.return_value = extraction
        cards = asyncio.run(ke.discover_podcast_knowledge_web("test-key", "tvly-test", {}))

    assert len(cards) == 1  # known111's episode skipped, only new222's episode processed
    assert cards[0]["chapter_title"] == "Fuel Early"
    assert cards[0]["source_label"] == "https://www.youtube.com/embed/new222"
    assert cards[0]["topic"] == "Nutrition"


def test_discover_podcast_knowledge_web_skips_episode_pages_with_no_embedded_video():
    extraction = {"results": [{"raw_content": "https://evokeendurance.com/resources/text-only-article/"}]}

    async def fake_fetch_raw_html(url):
        return "<p>Just a text article, no video embed here.</p>"

    with (
        patch("db.get_knowledge_card_source_labels", return_value=set()),
        patch.object(ke, "TavilyClient") as tavily_cls,
        patch.object(ke, "_fetch_raw_html", side_effect=fake_fetch_raw_html),
    ):
        tavily_cls.return_value.extract.return_value = extraction
        cards = asyncio.run(ke.discover_podcast_knowledge_web("test-key", "tvly-test", {}))
    assert cards == []


def test_discover_podcast_knowledge_web_coerces_unknown_topic_to_training(monkeypatch):
    extraction = {"results": [{"raw_content": "https://evokeendurance.com/resources/some-episode/"}]}
    html = '<iframe data-src="https://www.youtube.com/embed/vid333?feature=oembed"></iframe>'
    transcript = {"title": "Ep", "content": "x" * 500, "url_path": "https://www.youtube.com/embed/vid333"}
    structured = {
        "cards": [
            {
                "chapter_title": "Some Concept",
                "summary": "Summary.",
                "key_points": ["Do this", "Do that"],
                "tags": ["misc"],
                "topic": "NotARealTopic",
            }
        ]
    }
    with (
        patch("db.get_knowledge_card_source_labels", return_value=set()),
        patch.object(ke, "TavilyClient") as tavily_cls,
        patch.object(ke, "_fetch_raw_html", new_callable=AsyncMock, return_value=html),
        patch("services.rag_service.RagService.get_youtube_transcript", return_value=transcript),
        patch.object(ke, "_gemini_structured", new_callable=AsyncMock, return_value=structured),
        patch("asyncio.sleep", new_callable=AsyncMock),
    ):
        tavily_cls.return_value.extract.return_value = extraction
        cards = asyncio.run(ke.discover_podcast_knowledge_web("test-key", "tvly-test", {}))
    assert cards[0]["topic"] == "Training"


def test_discover_podcast_knowledge_web_returns_empty_when_no_episodes_found():
    with (
        patch.object(ke, "TavilyClient") as tavily_cls,
        patch("db.get_knowledge_card_source_labels", return_value=set()),
    ):
        tavily_cls.return_value.extract.return_value = {"results": [{"raw_content": "no episodes here"}]}
        cards = asyncio.run(ke.discover_podcast_knowledge_web("test-key", "tvly-test", {}))
    assert cards == []


def test_discover_podcast_knowledge_web_skips_transcripts_that_are_too_short():
    extraction = {"results": [{"raw_content": "https://evokeendurance.com/resources/short-episode/"}]}
    html = '<iframe data-src="https://www.youtube.com/embed/short111?feature=oembed"></iframe>'
    transcript = {"title": "Short", "content": "too short", "url_path": "https://www.youtube.com/embed/short111"}
    with (
        patch.object(ke, "TavilyClient") as tavily_cls,
        patch("db.get_knowledge_card_source_labels", return_value=set()),
        patch.object(ke, "_fetch_raw_html", new_callable=AsyncMock, return_value=html),
        patch("services.rag_service.RagService.get_youtube_transcript", return_value=transcript),
        patch("asyncio.sleep", new_callable=AsyncMock),
    ):
        tavily_cls.return_value.extract.return_value = extraction
        cards = asyncio.run(ke.discover_podcast_knowledge_web("test-key", "tvly-test", {}))
    assert cards == []


def test_save_podcast_knowledge_cards_saves_en_and_vi():
    cards = [
        {
            "chapter_title": "Fuel Early",
            "summary": "Start fueling early.",
            "key_points": ["Start early"],
            "tags": ["fueling"],
            "topic": "Nutrition",
            "source_label": "https://www.youtube.com/embed/new222",
        }
    ]
    vi_cards = [{**cards[0], "chapter_title": "[VI] Fuel Early"}]
    with (
        patch("db.save_knowledge_cards", side_effect=[1, 1]) as save_mock,
        patch.object(ke, "translate_cards_to_vi_with_gemini", new_callable=AsyncMock, return_value=vi_cards),
        patch.object(ke.genai, "configure"),
        patch.object(ke.genai, "GenerativeModel"),
    ):
        saved = asyncio.run(ke.save_podcast_knowledge_cards(cards, "test-key"))
    assert saved == 1
    assert save_mock.call_count == 2
    assert save_mock.call_args_list[0].kwargs.get("lang") == "en" or save_mock.call_args_list[0][1].get("lang") == "en"


def test_save_podcast_knowledge_cards_returns_zero_for_empty_input():
    saved = asyncio.run(ke.save_podcast_knowledge_cards([], "test-key"))
    assert saved == 0
