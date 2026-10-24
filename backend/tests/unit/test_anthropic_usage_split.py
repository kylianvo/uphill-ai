from types import SimpleNamespace

from services.observability import Usage, _cost_details_usd


def _usage(out: int = 1000) -> SimpleNamespace:
    return SimpleNamespace(input_tokens=10, output_tokens=out, cache_read_input_tokens=0, cache_creation_input_tokens=0)


def block(kind: str, value: str) -> SimpleNamespace:
    return SimpleNamespace(type=kind, thinking=value) if kind == "thinking" else SimpleNamespace(type=kind, text=value)


def test_split_moves_non_answer_tokens_to_thinking():
    u = Usage.from_anthropic(_usage(1000), [block("thinking", ""), block("text", "x" * 300)])
    assert (u.output_tokens, u.thinking_tokens) == (100, 900)


def test_no_thinking_block_keeps_everything_as_output():
    u = Usage.from_anthropic(_usage(1000), [block("text", "x" * 300)])
    assert (u.output_tokens, u.thinking_tokens) == (1000, 0)


def test_estimate_is_clamped_to_output_tokens():
    u = Usage.from_anthropic(_usage(1000), [block("thinking", ""), block("text", "ạ" * 6000)])
    assert (u.output_tokens, u.thinking_tokens) == (1000, 0)


def test_refusal_with_empty_text_is_all_thinking():
    u = Usage.from_anthropic(_usage(500), [block("thinking", "")])
    assert (u.output_tokens, u.thinking_tokens) == (0, 500)


def test_split_does_not_change_cost():
    raw = Usage.from_anthropic(_usage(1000))
    split = Usage.from_anthropic(_usage(1000), [block("thinking", ""), block("text", "x" * 300)])
    assert _cost_details_usd("claude-haiku-5-5", split)["total"] == _cost_details_usd("claude-haiku-5-5", raw)["total"]
