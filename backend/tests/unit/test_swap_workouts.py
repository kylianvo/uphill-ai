"""Unit tests for swap_workouts function in db.py."""

from unittest.mock import MagicMock, patch

from db import swap_workouts


def test_swap_workouts_same_day_returns_true():
    assert swap_workouts(plan_id=1, week_number=1, day_1="Monday", day_2="Monday") is True


def test_swap_workouts_both_empty_returns_false():
    mock_conn = MagicMock()
    mock_conn.execute.return_value.scalar.return_value = 0
    with patch("db.engine.connect") as mock_connect:
        mock_connect.return_value.__enter__.return_value = mock_conn
        result = swap_workouts(plan_id=1, week_number=1, day_1="Monday", day_2="Tuesday")
        assert result is False
        mock_conn.commit.assert_not_called()


def test_move_workout_when_day2_is_empty():
    mock_conn = MagicMock()
    # count1 = 1, count2 = 0
    mock_conn.execute.return_value.scalar.side_effect = [1, 0]
    with patch("db.engine.connect") as mock_connect:
        mock_connect.return_value.__enter__.return_value = mock_conn
        result = swap_workouts(plan_id=1, week_number=1, day_1="Monday", day_2="Tuesday")
        assert result is True
        mock_conn.commit.assert_called_once()
        # Verify single UPDATE executed (moving Monday -> Tuesday)
        calls = mock_conn.execute.call_args_list
        # calls[0] is count1, calls[1] is count2, calls[2] is the UPDATE
        assert len(calls) == 3
        sql_text = str(calls[2][0][0])
        params = calls[2][0][1]
        assert "UPDATE workouts SET day_of_week=:day2" in sql_text
        assert params["day1"] == "Monday"
        assert params["day2"] == "Tuesday"


def test_move_workout_when_day1_is_empty():
    mock_conn = MagicMock()
    # count1 = 0, count2 = 1
    mock_conn.execute.return_value.scalar.side_effect = [0, 1]
    with patch("db.engine.connect") as mock_connect:
        mock_connect.return_value.__enter__.return_value = mock_conn
        result = swap_workouts(plan_id=1, week_number=1, day_1="Monday", day_2="Wednesday")
        assert result is True
        mock_conn.commit.assert_called_once()
        calls = mock_conn.execute.call_args_list
        assert len(calls) == 3
        sql_text = str(calls[2][0][0])
        params = calls[2][0][1]
        assert "UPDATE workouts SET day_of_week=:day1" in sql_text
        assert params["day1"] == "Monday"
        assert params["day2"] == "Wednesday"


def test_swap_workouts_when_both_days_have_workouts():
    mock_conn = MagicMock()
    # count1 = 1, count2 = 1
    mock_conn.execute.return_value.scalar.side_effect = [1, 1]
    with patch("db.engine.connect") as mock_connect:
        mock_connect.return_value.__enter__.return_value = mock_conn
        result = swap_workouts(plan_id=1, week_number=1, day_1="Monday", day_2="Wednesday")
        assert result is True
        mock_conn.commit.assert_called_once()
        calls = mock_conn.execute.call_args_list
        # count1, count2, plus 3-step placeholder swap = 5 execute calls
        assert len(calls) == 5
