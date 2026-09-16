from fastapi.testclient import TestClient

from agent.app import app
from agent.schemas import parse_action


def home_snapshot() -> dict[str, object]:
    return {
        "v": 1,
        "url": "http://localhost:4000/",
        "title": "المتجر التجريبي",
        "lang": "ar",
        "viewport": {"w": 390, "h": 844, "scrollY": 0},
        "truncated": False,
        "elements": [
            {
                "id": 1,
                "role": "link",
                "name": "الأحذية",
                "href": "/c/shoes",
                "visible": True,
            }
        ],
    }


def test_step_turns_arabic_running_shoes_request_into_one_filter_action() -> None:
    response = TestClient(app).post(
        "/step",
        json={
            "message": "عاوز كوتشي للجري بأقل من ٢٠٠٠",
            "snapshot": home_snapshot(),
        },
    )

    assert response.status_code == 200
    action = parse_action(response.json())
    assert action.type == "navigate"
    assert action.url == "/c/shoes?type=running&max_price=2000"
    assert action.task_id
    assert action.action_id
    assert action.sequence_number == 1
    assert action.narration == "هفلتر لك أحذية الجري بحد أقصى ٢٠٠٠ جنيه."


def test_step_turns_english_running_shoes_request_into_one_filter_action() -> None:
    response = TestClient(app).post(
        "/step",
        json={
            "message": "Show me running shoes under 2000 EGP",
            "snapshot": home_snapshot(),
        },
    )

    assert response.status_code == 200
    action = parse_action(response.json())
    assert action.type == "navigate"
    assert action.url == "/c/shoes?type=running&max_price=2000"
    assert action.narration == "I'll filter running shoes to a maximum of EGP 2000."
