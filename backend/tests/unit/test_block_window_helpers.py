"""Unit tests for db.py's week_range_for_block/block_number_for_week -- the
single source of truth for the block-window formula that plan generation,
get_block_completion, and block_evaluator.evaluate_block_performance all
call instead of inlining `(block_number - 1) * weeks_per_block + 1`. No DB
connection needed: these are pure functions of two integers.
"""

import db


def test_week_range_for_block_uses_configured_weeks_per_block_by_default():
    # settings.WEEKS_PER_BLOCK is 1: block N should be the single week N.
    assert db.week_range_for_block(1) == (1, 1)
    assert db.week_range_for_block(3) == (3, 3)


def test_week_range_for_block_honors_an_explicit_weeks_per_block():
    assert db.week_range_for_block(1, weeks_per_block=2) == (1, 2)
    assert db.week_range_for_block(2, weeks_per_block=2) == (3, 4)
    assert db.week_range_for_block(3, weeks_per_block=3) == (7, 9)


def test_block_number_for_week_uses_configured_weeks_per_block_by_default():
    assert db.block_number_for_week(1) == 1
    assert db.block_number_for_week(5) == 5


def test_block_number_for_week_honors_an_explicit_weeks_per_block():
    assert db.block_number_for_week(1, weeks_per_block=2) == 1
    assert db.block_number_for_week(2, weeks_per_block=2) == 1
    assert db.block_number_for_week(3, weeks_per_block=2) == 2


def test_week_range_and_block_number_agree_with_each_other():
    """Regression cover for the training-block-size change: generating block N
    (via week_range_for_block, as PlanGenerator.generate_plan_workouts does)
    and asking which block a week belongs to (via block_number_for_week, as
    get_block_completion's callers and adapt-week's block_num do) must
    compute the same week window -- every week in block N's range must map
    back to block N, for any weeks_per_block."""
    for weeks_per_block in (1, 2, 3, 4):
        for block_number in range(1, 6):
            week_start, week_end = db.week_range_for_block(block_number, weeks_per_block)
            for week in range(week_start, week_end + 1):
                assert db.block_number_for_week(week, weeks_per_block) == block_number
