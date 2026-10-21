import asyncio

from config import settings
from services import vi_humanizer
from services.vi_humanizer import acceptable


def test_accepts_clean_rewrite():
    assert acceptable(
        "Tuần trước bạn hoàn thành 4/5 buổi. Giữ nhịp này nhé.", "Tuần trước bạn hoàn thành 4/5 buổi. Cứ giữ nhịp này."
    )


def test_rejects_swapped_protected_term():
    # Real sample output: "Plan" became "Kế hoạch".
    assert not acceptable(
        "Plan chưa đỡ hết mục tiêu nên thời gian mục tiêu đã lùi lại.",
        "Kế hoạch chưa đạt hết mục tiêu nên thời gian dự kiến đã bị dời lại.",
    )


def test_rejects_lost_ui_label():
    assert not acceptable("Giữ đều các buổi Zone 2 và xem mục Goal.", "Cứ giữ đều các buổi Zone 2 và xem mục tiêu nhé.")


def test_rejects_added_casual_particle_and_pace_gloss():
    assert not acceptable("Tuần trước bạn hoàn thành 4/5 buổi.", "Tuần trước bạn hoàn thành 4/5 buổi rồi nha.")
    assert not acceptable("Hỏi về pace hoặc fueling.", "Hỏi về tốc độ (pace) hay fueling.")
    assert not acceptable("Chạy Easy nhẹ nhàng.", "Chạy nhẹ nhàng.", english="Easy run")


def test_rejects_changed_number():
    assert not acceptable("Chạy nhẹ 45 phút.", "Chạy nhẹ 40 phút.")


def test_rejects_banned_word_and_runaway_length():
    assert not acceptable("Giảm khối lượng 15%.", "Giảm thể tích 15%.")
    assert not acceptable("Giữ nhịp nhé.", "Giữ nhịp nhé, " + "bạn cứ thong thả " * 5)


def test_off_without_url(monkeypatch):
    monkeypatch.setattr(settings, "VI_HUMANIZER_URL", "")
    assert asyncio.run(vi_humanizer.humanize("Giữ nhịp nhé.")) == "Giữ nhịp nhé."


def test_unreachable_server_keeps_original(monkeypatch):
    monkeypatch.setattr(settings, "VI_HUMANIZER_URL", "http://127.0.0.1:1")
    assert asyncio.run(vi_humanizer.humanize("Giữ nhịp nhé.")) == "Giữ nhịp nhé."


def test_static_copy_has_no_banned_words():
    # Guards the web app and iOS strings; run `python scripts/vi_copy_check.py` for the offending lines.
    import importlib.util
    from pathlib import Path

    spec = importlib.util.spec_from_file_location(
        "vi_copy_check", Path(__file__).parents[2] / "scripts/vi_copy_check.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert not list(mod.violations())
