import json
import os
import time

from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load env variables
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from config import settings  # noqa: E402 (must follow load_dotenv)

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY not found in .env")

client = genai.Client(api_key=api_key)
_generate_config = types.GenerateContentConfig(
    thinking_config=types.ThinkingConfig(thinking_level=settings.GEMINI_THINKING_LEVEL)
)


def translate_card(card):
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
        response = client.models.generate_content(model=settings.GEMINI_MODEL, contents=prompt, config=_generate_config)
        text = response.text.strip()
        # Clean potential markdown wrapping
        if text.startswith("```"):
            lines = text.split("\n")
            if lines[0].startswith("```json"):
                text = "\n".join(lines[1:-1])
            else:
                text = "\n".join(lines[1:-1])
        return json.loads(text.strip())
    except Exception as e:
        print(f"Error translating card '{card.get('chapter_title')}': {e}")
        # Retry once after 2 seconds
        time.sleep(2)
        try:
            response = client.models.generate_content(
                model=settings.GEMINI_MODEL, contents=prompt, config=_generate_config
            )
            text = response.text.strip()
            if text.startswith("```"):
                lines = text.split("\n")
                if lines[0].startswith("```json"):
                    text = "\n".join(lines[1:-1])
                else:
                    text = "\n".join(lines[1:-1])
            return json.loads(text.strip())
        except Exception as retry_err:
            print(f"Retry failed: {retry_err}")
            return None


def main():
    backup_path = os.path.join(os.path.dirname(__file__), "knowledge_cards_backup.json")
    output_path = os.path.join(os.path.dirname(__file__), "knowledge_cards_backup_vi.json")

    with open(backup_path, encoding="utf-8") as f:
        cards = json.load(f)

    print(f"Loaded {len(cards)} cards for translation.")
    translated_cards = []

    for idx, card in enumerate(cards, 1):
        print(f"[{idx}/{len(cards)}] Translating: {card['chapter_title']}...")
        translated = translate_card(card)
        if translated:
            translated_cards.append(translated)
        else:
            print(f"Skipping card: {card['chapter_title']}")
        # Brief sleep to avoid rate limiting
        time.sleep(0.5)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(translated_cards, f, indent=2, ensure_ascii=False)

    print(f"Saved {len(translated_cards)} translated cards to {output_path}")


if __name__ == "__main__":
    main()
