import json

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.ai_prediction import AIPrediction
from app.models.campaign import Campaign
from app.models.call import Call
from app.models.customer import Customer
from app.models.decision_recommendation import DecisionRecommendation
from app.models.engagement_event import EngagementEvent
from app.models.lead import Lead
from app.models.product import Product
from app.models.website_event import WebsiteEvent
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


def test_chat_context_includes_database_analytics_and_requested_lead(
    db_session: Session,
) -> None:
    customer = Customer(
        external_customer_id="CUST_TEST_42",
        crm_age_band="30-39",
        crm_income_band="middle",
    )
    campaign = Campaign(code="CMP-TEST-42", name="Spring campaign", channel="email")
    product = Product(code="PRD-TEST-42", name="Test plan")
    db_session.add_all([customer, campaign, product])
    db_session.flush()
    lead = Lead(
        customer_id=customer.id,
        campaign_id=campaign.id,
        source_channel="email",
        status="converted",
        current_stage="closed",
        current_section="sales",
        current_handler="Agent 1",
        priority="high",
        lead_score=87,
        recommended_action="follow_up",
        excel_fields={"CRM_Product_Code": product.code},
    )
    db_session.add(lead)
    db_session.flush()
    db_session.add_all(
        [
            Call(lead_id=lead.id, customer_id=customer.id, status="completed", duration_seconds=90),
            EngagementEvent(
                lead_id=lead.id,
                customer_id=customer.id,
                channel="email",
                metric_type="click",
                metric_value=3,
            ),
            WebsiteEvent(
                lead_id=lead.id,
                customer_id=customer.id,
                event_name="plan_view",
            ),
            AIPrediction(
                lead_id=lead.id,
                customer_id=customer.id,
                prediction_type="conversion",
                model_name="baseline",
                score=0.8,
                label="likely",
            ),
            DecisionRecommendation(
                lead_id=lead.id,
                customer_id=customer.id,
                decision_type="next_best_action",
                recommended_action="follow_up",
                confidence=0.75,
                rationale="Recent engagement",
            ),
        ]
    )
    db_session.commit()

    snapshot = json.loads(ai_chat_service._database_context(db_session, f"Lead #{lead.id}"))
    assert snapshot["counts"]["leads"] == 1
    assert snapshot["conversion_summary"]["conversion_rate"] == 1
    assert snapshot["call_metrics"]["average_duration_seconds"] == 90
    assert snapshot["product_lead_counts"] == [{"product": "Test plan", "leads": 1}]
    assert snapshot["prediction_counts_by_type_and_label"][0]["type"] == "conversion"
    assert snapshot["recommendations_by_type_action_and_priority"][0]["action"] == "follow_up"
    assert snapshot["requested_lead_records"][0]["lead_id"] == lead.id
    assert snapshot["requested_lead_records"][0]["latest_predictions"][0]["label"] == "likely"
    customer_snapshot = json.loads(
        ai_chat_service._database_context(db_session, f"Customer {customer.external_customer_id}")
    )
    assert customer_snapshot["requested_lead_records"][0]["customer_id"] == "CUST_TEST_42"

    chart = ai_chat_service._chart_for_question(db_session, "Graph campaign conversion rates")
    assert chart is not None
    assert chart["metric"] == "Conversion rate (%)"
    assert chart["data"] == [{"label": "Spring campaign", "value": 100}]


def test_chat_returns_a_chart_payload_for_graph_requests(
    client: TestClient,
    db_session: Session,
    monkeypatch,
) -> None:
    customer = Customer(external_customer_id="CUST_CHART_1")
    campaign = Campaign(code="CMP-CHART-1", name="Chart campaign", channel="web")
    db_session.add_all([customer, campaign])
    db_session.flush()
    db_session.add(
        Lead(
            customer_id=customer.id,
            campaign_id=campaign.id,
            status="converted",
            current_stage="closed",
            priority="high",
        )
    )
    db_session.commit()
    monkeypatch.setattr(ai_chat_service.settings, "groq_api_key", "test-groq-key")
    monkeypatch.setattr(
        ai_chat_service,
        "generate_reply",
        lambda model, messages: "Here is the conversion chart.",
    )

    conversation = client.post(
        "/api/ai/chat/conversations",
        json={"model_id": "openai/gpt-oss-20b"},
    ).json()
    response = client.post(
        f"/api/ai/chat/conversations/{conversation['id']}/messages",
        json={"content": "Graph campaign conversion rates"},
    )

    assert response.status_code == 200
    content = response.json()["assistant_message"]["content"]
    assert content.startswith("Here is the conversion chart.")
    chart_json = content.split("```salesboard-chart\n", 1)[1].split("\n```", 1)[0]
    chart = json.loads(chart_json)
    assert chart["title"] == "Conversion rate by campaign"
    assert chart["data"] == [{"label": "Chart campaign", "value": 100.0}]
