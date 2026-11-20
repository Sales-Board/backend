from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.product import Product
from app.services import ai_chat_service


def test_chat_models_expose_three_options_per_provider(client: TestClient) -> None:
    response = client.get("/api/ai/chat/models")

    assert response.status_code == 200
    models = response.json()
    assert len(models) == 6
    assert sum(model["provider"] == "groq" for model in models) == 3
    assert sum(model["provider"] == "google" for model in models) == 3
    assert {
        model["model_id"] for model in models
    } == {
        "openai/gpt-oss-20b",
        "openai/gpt-oss-120b",
        "qwen/qwen3.8-27b",
        "gemini-3.8-flash",
        "gemini-3.6-flash",
        "gemini-3.5-flash-lite",
    }
    assert all(isinstance(model["configured"], bool) for model in models)


def test_chat_persists_conversation_and_answers_from_database(
    client: TestClient,
    db_session: Session,
    monkeypatch,
) -> None:
    db_session.add(Product(code="SAVER", name="Saver Plan"))
    db_session.commit()
    monkeypatch.setattr(ai_chat_service.settings, "groq_api_key", "test-groq-key")

    def fake_reply(model: dict[str, str], messages: list[dict[str, str]]) -> str:
        assert model["provider"] == "groq"
        assert "Saver Plan" in messages[0]["content"]
        return "The database contains a Saver Plan product."

    monkeypatch.setattr(ai_chat_service, "generate_reply", fake_reply)

    created = client.post(
        "/api/ai/chat/conversations",
        json={"model_id": "openai/gpt-oss-20b"},
    )
    assert created.status_code == 201
    conversation_id = created.json()["id"]

    turn = client.post(
        f"/api/ai/chat/conversations/{conversation_id}/messages",
        json={"content": "Which products do we have?"},
    )
    assert turn.status_code == 200
    assert turn.json()["assistant_message"]["content"] == (
        "The database contains a Saver Plan product."
    )
    assert turn.json()["conversation"]["title"] == "Which products do we have?"

    history = client.get(f"/api/ai/chat/conversations/{conversation_id}")
    assert history.status_code == 200
    assert [message["role"] for message in history.json()["messages"]] == [
        "user",
        "assistant",
    ]

    deleted = client.delete(f"/api/ai/chat/conversations/{conversation_id}")
    assert deleted.status_code == 204
    assert client.get(f"/api/ai/chat/conversations/{conversation_id}").status_code == 404


def test_chat_requires_a_provider_api_key(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(ai_chat_service.settings, "groq_api_key", "")
    created = client.post(
        "/api/ai/chat/conversations",
        json={"model_id": "openai/gpt-oss-20b"},
    )
    conversation_id = created.json()["id"]

    response = client.post(
        f"/api/ai/chat/conversations/{conversation_id}/messages",
        json={"content": "Hello"},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "GROQ_API_KEY is not configured on the backend."
