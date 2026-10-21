"""Polish Vietnamese text with the vi-humanizer model (llama.cpp, OpenAI-compatible API).

The model reads more naturally than Gemini's Vietnamese but, in sample runs, also swapped glossary terms
("plan" -> "kế hoạch", "mục Goal" -> "mục tiêu") and shifted meaning. So its output is only used when it keeps
every number, every protected term and none of the banned words; otherwise the original text is returned.
Off unless VI_HUMANIZER_URL is set. Never raises.
"""

import re

import httpx

from config import settings
from log_utils import get_logger

_logger = get_logger(__name__)

# Natural tone prompt from the vi-humanizer web app (web/js/i18n.js): keeps xưng hô and register.
_PROMPT = (
    "Viết lại văn bản trong ngoặc kép cho tự nhiên, như người Việt thật viết. Giữ nguyên thông tin, cách xưng hô "
    "và mức trang trọng của bản gốc. Chỉ trả về văn bản đã viết lại, không thêm lời dẫn.\n\n"
    '"""\n{t}\n"""'
)
# Same list as the glossary rules in plan_generator.py's Vietnamese prompts.
BANNED = (
    "kiến tạo", "bảo chứng", "bứt phá", "nâng tầm", "vượt trội", "tối ưu hóa", "chuyên sâu", "đột phá",
    "giáo án", "sinh lý", "thể tích", "chinh phục đỉnh cao", "tiếp nhiên liệu",
    # Rest of R3 in .claude/skills/uphill-ai-vietnamese-copy; "hành trình" and "vận hành" are only banned in
    # some senses, so a word match can't police them.
    "toàn diện", "độc quyền", "mạnh mẽ", "tuyệt vời", "uy tín hàng đầu", "chuẩn mực thế giới", "đắm chìm",
    "giải pháp", "thấu hiểu", "đồng hành cùng bạn", "kiểm toán", "tri thức", "hệ sinh thái",
)  # fmt: skip
# Terms we keep in English or as UI labels; if the draft has one, the rewrite must too.
PROTECTED = (
    "zone", "goal", "plan", "long run", "tempo", "hrv", "bpm", "aerobic", "fueling",
    # Rest of R1 (keep in English): training vocabulary and race/nutrition terms.
    "pace", "easy run", "threshold", "interval", "fartlek", "surges", "recovery run", "hill repeat", "strength",
    "aet", "ant", "rpe", "cadence", "deload", "taper", "block", "split", "checkpoint", "cutoff", "dnf",
    "elevation gain", "gpx", "race", "ultra", "trail", "road", "treadmill", "gel", "chews", "carbs", "sodium",
    "electrolytes", "gut training", "stack height", "drop", "carbon plate", "foam rolling", "warm-up",
    "cool-down", "strides", "coach", "anaerobic", "resting hr", "max hr",
)  # fmt: skip
# Chatty particles. UI/coach copy is plain and direct (R5); the model adds them, so a rewrite may not
# contain one the draft did not.
# R2 forbids glossing pace/fueling; reject a rewrite that adds one the draft did not have.
NEW_FORBIDDEN = ("tốc độ", "dinh dưỡng (fueling)", "nhật ký chạy")
CASUAL = ("nha", "nhé", "nhỉ", "nè", "nhen", "đó", "đấy", "vậy", "mình", "ạ", "thôi", "rồi", "đi", "xem sao")
MAX_GROWTH = 1.4  # a rewrite much longer than the draft has added content


def _numbers(text: str) -> list[str]:
    return sorted(re.findall(r"\d+", text))


# printf (%@ %lld %d), {name} / {{term:KEY}} and ${expr} placeholders must come back untouched.
_PLACEHOLDER = re.compile(r"%(?:\d+\$)?(?:lld|ld|d|@|f|s)|\{\{[^}]*\}\}|\$\{[^}]*\}|\{[^}\s]+\}")


def _placeholders(text: str) -> list[str]:
    return sorted(_PLACEHOLDER.findall(text))


def _words(text: str, terms) -> set[str]:
    return {t for t in terms if re.search(rf"(?<![\w-]){re.escape(t)}(?![\w-])", text.lower())}


def acceptable(original: str, rewrite: str, english: str | None = None) -> bool:
    low, orig = rewrite.lower(), original.lower()
    if not rewrite or len(rewrite) > len(original) * MAX_GROWTH:
        return False
    if _numbers(original) != _numbers(rewrite) or _placeholders(original) != _placeholders(rewrite):
        return False
    if any(w in low for w in BANNED):
        return False
    if any(w in low and w not in orig for w in NEW_FORBIDDEN):
        return False
    if _words(low, CASUAL) - _words(orig, CASUAL) or rewrite.count("!") > original.count("!"):
        return False
    # Terms kept in English must survive, whether the draft or its English source carries them.
    need = _words(orig, PROTECTED) | (_words(english, PROTECTED) if english else set())
    return need <= _words(low, PROTECTED)


async def humanize(text: str, english: str | None = None) -> str:
    if not settings.VI_HUMANIZER_URL or not text.strip():
        return text
    body = {
        "model": "vi-humanizer",
        "temperature": settings.VI_HUMANIZER_TEMPERATURE,
        "messages": [{"role": "user", "content": _PROMPT.replace("{t}", text)}],
    }
    try:
        async with httpx.AsyncClient(timeout=settings.VI_HUMANIZER_TIMEOUT) as client:
            r = await client.post(f"{settings.VI_HUMANIZER_URL.rstrip('/')}/v1/chat/completions", json=body)
            r.raise_for_status()
            rewrite = r.json()["choices"][0]["message"]["content"].strip()
    except Exception as ex:  # noqa: BLE001
        _logger.warning(f"[ViHumanizer] call failed, keeping original: {type(ex).__name__}: {ex}")
        return text
    if acceptable(text, rewrite, english):
        return rewrite
    _logger.info("[ViHumanizer] rewrite rejected by guards, keeping original")
    return text
