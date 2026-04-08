from unittest.mock import patch, MagicMock


def test_chat_happy_path(client, seed_user):
    mock_graph = MagicMock()
    mock_graph.invoke.return_value = {
        "messages": [{"role": "user", "content": "hello"}],
        "user_id": 1,
        "task_id": None,
        "context": {},
        "route": "chat",
        "final_response": "Hello from Jarvis!",
    }

    with patch("app.routers.chat.build_orchestrator", return_value=mock_graph):
        resp = client.post("/chat/message", json={"content": "hello", "user_id": 1})
        assert resp.status_code == 200
        data = resp.json()
        assert "response" in data
        assert data["response"] == "Hello from Jarvis!"
        assert "conversation_id" in data


def test_chat_creates_task_for_task_route(client, seed_user):
    mock_graph = MagicMock()
    mock_graph.invoke.return_value = {
        "messages": [{"role": "user", "content": "build me an app"}],
        "user_id": 1,
        "task_id": None,
        "context": {},
        "route": "task",
        "final_response": "Task recognized.",
    }

    with patch("app.routers.chat.build_orchestrator", return_value=mock_graph):
        resp = client.post("/chat/message", json={"content": "build me an app", "user_id": 1})
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("task_id") is not None
