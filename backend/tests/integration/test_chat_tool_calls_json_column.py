"""Integration tests for tool_calls_json column in chat_messages."""

import json

import db


def test_tool_calls_json_round_trips(auth_headers):
    user_id = auth_headers["user_id"]
    thread = db.get_or_create_chat_thread(user_id)
    msg_id = db.append_chat_message(thread["id"], "assistant", "Here's your week.")

    tool_calls = [
        {
            "tool_call_id": "call_1",
            "name": "get_week",
            "status": "success",
            "card_type": "week_schedule",
            "card_data": {"week_number": 3},
        }
    ]
    db.update_chat_message(msg_id, tool_calls_json=tool_calls)

    stored = db.get_chat_message(msg_id)
    raw = stored["tool_calls_json"]
    parsed = json.loads(raw) if isinstance(raw, str) else raw
    assert parsed == tool_calls
