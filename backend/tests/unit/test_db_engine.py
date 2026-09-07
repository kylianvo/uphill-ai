"""Unit test for the db.py engine configuration -- no DB connection needed,
this only inspects how the Engine object itself was constructed."""

import db


def test_engine_hides_bound_parameters_in_error_messages():
    # StatementError.__str__ appends the SQL and its bound parameters --
    # for activities/daily_metrics that means real athlete health data
    # (start_time, distance_km, avg_hr, device_model, ...). coros_sync.py's
    # per-row handlers log that error via logger.exception, so the engine
    # must be configured to redact parameter values from it.
    assert db.engine.hide_parameters is True
