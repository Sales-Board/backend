import json

import httpx

from app.services import ai_chat_service


def test_provider_adapters_send_authenticated_requests(monkeypatch) -> None:
    expected_models = {
        "groq": "openai/gpt-oss-20b",
        "google": "gemini-3.8-flash",
    }
    monkeypatch.setattr(ai_chat_service.settings, "groq_api_key", "groq-test-key")
    monkeypatch.setattr(ai_chat_service.settings, "google_api_key", "google-test-key")

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        if request.url.host == "api.groq.com":
            assert request.headers["authorization"] == "Bearer groq-test-key"
            assert body["model"] == expected_models["groq"]
            return httpx.Response(
                200,
                json={"choices": [{"message": {"content": "Groq reply"}}]},
            )

        assert request.url.host == "generativelanguage.googleapis.com"
        assert request.headers["x-goog-api-key"] == "google-test-key"
        assert request.url.path.endswith(f"{expected_models['google']}:generateContent")
        return httpx.Response(
            200,
            json={"candidates": [{"content": {"parts": [{"text": "Gemini reply"}]}}]},
        )

    real_client = httpx.Client
    monkeypatch.setattr(
        ai_chat_service.httpx,
        "Client",
        lambda **kwargs: real_client(transport=httpx.MockTransport(handler), **kwargs),
    )
    messages = [
        {"role": "system", "content": "Use the database snapshot."},
        {"role": "user", "content": "Hello"},
    ]

    assert ai_chat_service.generate_reply(
        ai_chat_service.MODEL_BY_ID[expected_models["groq"]],
        messages,
    ) == "Groq reply"
    assert ai_chat_service.generate_reply(
        ai_chat_service.MODEL_BY_ID[expected_models["google"]],
        messages,
    ) == "Gemini reply"
