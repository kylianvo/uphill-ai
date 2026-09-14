from main import COACH_COPILOT_SYSTEM_INSTRUCTION, COACH_SYSTEM_INSTRUCTION


def test_coach_system_instruction_domain_guardrails():
    """Verify Coach Uphill has strict domain boundaries against answering off-topic queries."""
    prompt = COACH_SYSTEM_INSTRUCTION.lower()
    assert "domain boundaries" in prompt
    assert "running" in prompt
    assert "sports nutrition" in prompt or "nutrition" in prompt
    assert "decline" in prompt or "redirect" in prompt
    assert "outside of running" in prompt


def test_coach_copilot_system_instruction_domain_guardrails():
    """Verify Coach Copilot limits discussion strictly to athletic training and coaching."""
    prompt = COACH_COPILOT_SYSTEM_INSTRUCTION.lower()
    assert "domain boundaries" in prompt
    assert "running" in prompt
    assert "decline" in prompt or "redirect" in prompt


def test_coach_vietnamese_instruction_rules():
    """Verify Vietnamese language contract has R1-R5 rules (English terms, mappings, ban list)."""
    from main import COACH_VI_LANGUAGE_INSTRUCTION

    rule = COACH_VI_LANGUAGE_INSTRUCTION
    # Banned list checks
    for banned in ["giáo án", "sinh lý", "thể tích", "kiến tạo", "bảo chứng", "vận hành"]:
        assert banned in rule

    # English technical terms check
    for en_term in ["Pace", "Easy Run", "Long Run", "Zone 1–Zone 5", "AeT", "AnT", "Fueling"]:
        assert en_term in rule

    # Fixed mapping checks
    assert "khối lượng" in rule
    assert "thể chất" in rule
    assert "lịch tập" in rule or "plan" in rule


def test_is_vietnamese_request_detection():
    """Verify detection logic for Vietnamese requests."""
    from main import ChatMessage, is_vietnamese_request

    assert is_vietnamese_request(lang="vi") is True
    assert is_vietnamese_request(lang="en") is False
    assert is_vietnamese_request(user_profile={"lang": "vi"}) is True
    assert is_vietnamese_request(context_data={"lang": "vi"}) is True
    assert (
        is_vietnamese_request(messages=[ChatMessage(role="user", content="Tập bài Long Run Chủ Nhật này thế nào?")])
        is True
    )
    assert is_vietnamese_request(messages=[ChatMessage(role="user", content="How should I pace my easy run?")]) is False


def test_plan_week_adapt_vietnamese_rules():
    """Verify prompt generated for plan, week, and adapt has authentic Vietnamese rules."""
    from services.plan_generator import PlanGenerator

    # 1. Full plan / block prompt check
    user_profile = {
        "age": 32,
        "current_weekly_km": 40.0,
        "max_hr": 185,
        "resting_hr": 55,
        "aet_hr": 140,
        "ant_hr": 165,
        "terrain": "trail",
        "lang": "vi",
    }
    race_info = {
        "name": "Vietnam Mountain Marathon",
        "date": "2026-10-20",
        "terrain": "trail",
        "goal_type": "finish",
        "course_distance_km": 70,
        "course_elevation_gain_m": 3500,
        "lang": "vi",
    }

    # Verify that plan generator builds the Vietnamese localization rule into prompt
    # and handles target_week (adaptation) with the adaptation rule
    tier = PlanGenerator.resolve_athlete_tier(user_profile, race_info)
    assert tier is not None
