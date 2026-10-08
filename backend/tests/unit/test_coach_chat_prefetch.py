import asyncio
import time

from services.coach_chat import _prefetch_retrieval


async def test_prefetch_returns_the_retrieval_result():
    retrieve = _prefetch_retrieval(lambda q: [{"title": q}], "taper")
    assert await retrieve("taper") == [{"title": "taper"}]


async def test_prefetch_overlaps_with_other_blocking_work():
    def slow_retrieve(_q):
        time.sleep(0.3)
        return []

    start = time.monotonic()
    retrieve = _prefetch_retrieval(slow_retrieve, "q")
    await asyncio.to_thread(time.sleep, 0.3)  # stands in for build_chat_context
    await retrieve("q")
    elapsed = time.monotonic() - start

    assert elapsed < 0.5  # sequential would be >= 0.6
