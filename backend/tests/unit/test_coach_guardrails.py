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
