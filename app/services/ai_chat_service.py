import json
from collections.abc import Sequence

import httpx
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.ai_prediction import AIPrediction
from app.models.ai_chat import AIChatConversation, AIChatMessage
from app.models.campaign import Campaign
from app.models.call import Call
from app.models.customer import Customer
from app.models.data_import_job import DataImportJob
from app.models.decision_recommendation import DecisionRecommendation
from app.models.engagement_event import EngagementEvent
from app.models.followup import Followup
from app.models.lead import Lead
from app.models.lead_assignment import LeadAssignment
from app.models.lead_outcome import LeadOutcome
from app.models.lead_timeline_event import LeadTimelineEvent
from app.models.ml_training_job import MLTrainingJob
from app.models.product import Product
from app.models.task import Task
from app.models.website_event import WebsiteEvent
from app.schemas.ai_chat import (
    AIChatConversationCreate,
    AIChatMessageCreate,
    AIChatModelRead,
    AIChatTurnRead,
)

CHAT_MODELS = (
    {
        "provider": "groq",
        "model_id": "openai/gpt-oss-120b",
        "name": "GPT OSS 120B",
    },
    {
        "provider": "groq",
        "model_id": "qwen/qwen3.8-27b",
        "name": "Qwen 3.8 27B",
    },
    {
        "provider": "groq",
        "model_id": "openai/gpt-oss-20b",
        "name": "GPT OSS 20B",
    },
    {
        "provider": "google",
        "model_id": "gemini-3.8-flash",
        "name": "Gemini 3.8 Flash",
    },
    {
        "provider": "google",
        "model_id": "gemini-3.6-flash",
        "name": "Gemini 3.6 Flash",
    },
    {
        "provider": "google",
        "model_id": "gemini-3.5-flash-lite",
        "name": "Gemini 3.5 Flash-Lite",
    },
)
MODEL_BY_ID = {model["model_id"]: model for model in CHAT_MODELS}
SYSTEM_PROMPT = """You are the AI Agent for a sales and lead intelligence application.
Answer clearly and helpfully using the supplied application database snapshot and
conversation. Treat the snapshot as the only source of business facts: do not
invent records, metrics, customer details, or actions. The product and campaign
lists and lead details are bounded samples; do not infer that an unlisted record
does not exist. If the snapshot does not contain enough information, say what is
missing. The data is anonymized; never attempt to identify a person. You can
explain or recommend actions, but you cannot claim to have changed records or
contacted anyone."""


def list_models() -> list[AIChatModelRead]:
    return [
        AIChatModelRead(
            **model,
            configured=bool(
                settings.groq_api_key.strip()
                if model["provider"] == "groq"
                else settings.google_api_key.strip()
            ),
        )
        for model in CHAT_MODELS
    ]


def create_conversation(db: Session, payload: AIChatConversationCreate) -> AIChatConversation:
    model = _get_model(payload.model_id)
    conversation = AIChatConversation(
        title="New chat",
        provider=model["provider"],
        model_id=model["model_id"],
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


def list_conversations(db: Session) -> list[AIChatConversation]:
    return list(
        db.scalars(
            select(AIChatConversation).order_by(
                AIChatConversation.updated_at.desc(),
                AIChatConversation.id.desc(),
            )
        )
    )


def get_conversation(db: Session, conversation_id: int) -> AIChatConversation:
    conversation = db.get(AIChatConversation, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    return conversation


def get_conversation_messages(db: Session, conversation_id: int) -> list[AIChatMessage]:
    get_conversation(db, conversation_id)
    return list(
        db.scalars(
            select(AIChatMessage)
            .where(AIChatMessage.conversation_id == conversation_id)
            .order_by(AIChatMessage.id.asc())
        )
    )


def delete_conversation(db: Session, conversation_id: int) -> None:
    conversation = get_conversation(db, conversation_id)
    db.execute(
        AIChatMessage.__table__.delete().where(
            AIChatMessage.conversation_id == conversation_id,
        )
    )
    db.delete(conversation)
    db.commit()


def send_message(
    db: Session,
    conversation_id: int,
    payload: AIChatMessageCreate,
) -> AIChatTurnRead:
    conversation = get_conversation(db, conversation_id)
    model_id = payload.model_id or conversation.model_id
    model = _get_model(model_id)
    _require_api_key(model["provider"])

    user_message = AIChatMessage(
        conversation_id=conversation_id,
        role="user",
        content=payload.content.strip(),
    )
    if not user_message.content:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Message cannot be blank")

    db.add(user_message)
    db.flush()
    history = list(
        db.scalars(
            select(AIChatMessage)
            .where(AIChatMessage.conversation_id == conversation_id)
            .order_by(AIChatMessage.id.desc())
            .limit(30)
        )
    )
    history.reverse()
    reply = generate_reply(
        model,
        _build_messages(db, history),
    )
    assistant_message = AIChatMessage(
        conversation_id=conversation_id,
        role="assistant",
        content=reply,
        model_id=model_id,
    )
    db.add(assistant_message)
    conversation.provider = model["provider"]
    conversation.model_id = model_id
    if conversation.title == "New chat":
        conversation.title = _conversation_title(payload.content)
    db.commit()
    db.refresh(conversation)
    db.refresh(user_message)
    db.refresh(assistant_message)

    return AIChatTurnRead(
        conversation=conversation,
        user_message=user_message,
        assistant_message=assistant_message,
    )


def _get_model(model_id: str) -> dict[str, str]:
    model = MODEL_BY_ID.get(model_id)
    if model is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unsupported chat model")
    return model


def _require_api_key(provider: str) -> str:
    api_key = settings.groq_api_key if provider == "groq" else settings.google_api_key
    if not api_key.strip():
        env_name = "GROQ_API_KEY" if provider == "groq" else "GOOGLE_API_KEY"
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"{env_name} is not configured on the backend.",
        )
    return api_key.strip()


def _build_messages(
    db: Session,
    history: Sequence[AIChatMessage],
) -> list[dict[str, str]]:
    context = _database_context(db)
    messages = [
        {
            "role": "system",
            "content": f"{SYSTEM_PROMPT}\n\nApplication database snapshot:\n{context}",
        }
    ]
    messages.extend(
        {"role": message.role, "content": message.content}
        for message in history
        if message.role in {"user", "assistant"}
    )
    return messages


def _database_context(db: Session) -> str:
    counts = {
        "leads": db.scalar(select(func.count()).select_from(Lead)) or 0,
        "customers": db.scalar(select(func.count()).select_from(Customer)) or 0,
        "products": db.scalar(select(func.count()).select_from(Product)) or 0,
        "campaigns": db.scalar(select(func.count()).select_from(Campaign)) or 0,
        "calls": db.scalar(select(func.count()).select_from(Call)) or 0,
        "tasks": db.scalar(select(func.count()).select_from(Task)) or 0,
        "followups": db.scalar(select(func.count()).select_from(Followup)) or 0,
        "engagement_events": db.scalar(select(func.count()).select_from(EngagementEvent)) or 0,
        "website_events": db.scalar(select(func.count()).select_from(WebsiteEvent)) or 0,
        "lead_outcomes": db.scalar(select(func.count()).select_from(LeadOutcome)) or 0,
        "lead_assignments": db.scalar(select(func.count()).select_from(LeadAssignment)) or 0,
        "lead_timeline_events": db.scalar(select(func.count()).select_from(LeadTimelineEvent)) or 0,
        "ai_predictions": db.scalar(select(func.count()).select_from(AIPrediction)) or 0,
        "decision_recommendations": db.scalar(
            select(func.count()).select_from(DecisionRecommendation)
        )
        or 0,
        "data_import_jobs": db.scalar(select(func.count()).select_from(DataImportJob)) or 0,
        "ml_training_jobs": db.scalar(select(func.count()).select_from(MLTrainingJob)) or 0,
    }
    statuses = db.execute(
        select(Lead.status, func.count(Lead.id)).group_by(Lead.status).order_by(Lead.status)
    ).all()
    call_statuses = db.execute(
        select(Call.status, func.count(Call.id)).group_by(Call.status).order_by(Call.status)
    ).all()
    task_statuses = db.execute(
        select(Task.status, func.count(Task.id)).group_by(Task.status).order_by(Task.status)
    ).all()
    followup_statuses = db.execute(
        select(Followup.status, func.count(Followup.id))
        .group_by(Followup.status)
        .order_by(Followup.status)
    ).all()
    channels = db.execute(
        select(Lead.source_channel, func.count(Lead.id))
        .group_by(Lead.source_channel)
        .order_by(Lead.source_channel)
    ).all()
    stages = db.execute(
        select(Lead.current_stage, func.count(Lead.id))
        .group_by(Lead.current_stage)
        .order_by(Lead.current_stage)
    ).all()
    average_score = db.scalar(select(func.avg(Lead.lead_score)))
    leads = db.execute(
        select(Lead.id, Lead.status, Lead.current_stage, Lead.priority, Lead.lead_score)
        .order_by(Lead.lead_score.desc(), Lead.id.asc())
        .limit(15)
    ).all()
    products = db.execute(select(Product.code, Product.name).order_by(Product.name).limit(25)).all()
    campaigns = db.execute(
        select(Campaign.code, Campaign.name, Campaign.channel, Campaign.status)
        .order_by(Campaign.name)
        .limit(25)
    ).all()

    return json.dumps(
        {
            "counts": counts,
            "lead_counts_by_status": {status: count for status, count in statuses},
            "lead_counts_by_source_channel": {channel: count for channel, count in channels},
            "lead_counts_by_stage": {stage: count for stage, count in stages},
            "call_counts_by_status": {status: count for status, count in call_statuses},
            "task_counts_by_status": {status: count for status, count in task_statuses},
            "followup_counts_by_status": {status: count for status, count in followup_statuses},
            "average_lead_score": average_score,
            "listed_record_limits": {
                "lead_details": 15,
                "products": 25,
                "campaigns": 25,
            },
            "highest_scored_leads": [
                {
                    "lead_id": lead_id,
                    "status": status,
                    "stage": stage,
                    "priority": priority,
                    "score": score,
                }
                for lead_id, status, stage, priority, score in leads
            ],
            "products": [{"code": code, "name": name} for code, name in products],
            "campaigns": [
                {"code": code, "name": name, "channel": channel, "status": status}
                for code, name, channel, status in campaigns
            ],
        },
        ensure_ascii=True,
        default=str,
    )


def generate_reply(model: dict[str, str], messages: list[dict[str, str]]) -> str:
    api_key = _require_api_key(model["provider"])
    try:
        with httpx.Client(timeout=90.0) as client:
            if model["provider"] == "groq":
                response = client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {api_key}"},
                    json={
                        "model": model["model_id"],
                        "messages": messages,
                        "temperature": 0.4,
                        "max_tokens": 1200,
                    },
                )
                response.raise_for_status()
                content = response.json()["choices"][0]["message"]["content"]
            else:
                google_messages = [
                    {
                        "role": "model" if message["role"] == "assistant" else "user",
                        "parts": [{"text": message["content"]}],
                    }
                    for message in messages
                    if message["role"] != "system"
                ]
                system_instruction = messages[0]["content"] if messages else SYSTEM_PROMPT
                response = client.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/{model['model_id']}:generateContent",
                    headers={"x-goog-api-key": api_key},
                    json={
                        "systemInstruction": {"parts": [{"text": system_instruction}]},
                        "contents": google_messages,
                        "generationConfig": {"temperature": 0.4, "maxOutputTokens": 1200},
                    },
                )
                response.raise_for_status()
                content = "".join(
                    part.get("text", "")
                    for part in response.json()["candidates"][0]["content"]["parts"]
                )
    except httpx.TimeoutException as error:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=f"{model['provider'].title()} did not respond in time.",
        ) from error
    except httpx.HTTPStatusError as error:
        provider_status = error.response.status_code
        http_status = (
            status.HTTP_429_TOO_MANY_REQUESTS
            if provider_status == 429
            else status.HTTP_502_BAD_GATEWAY
        )
        raise HTTPException(
            status_code=http_status,
            detail=(
                f"{model['provider'].title()} API rejected the request (HTTP {provider_status}). "
                "Check the API key, model availability, and provider limits."
            ),
        ) from error
    except httpx.RequestError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Could not reach the {model['provider'].title()} API.",
        ) from error
    except (KeyError, IndexError, TypeError, ValueError) as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"{model['provider'].title()} returned an invalid response.",
        ) from error

    if not isinstance(content, str) or not content.strip():
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"{model['provider'].title()} returned an empty response.",
        )
    return content.strip()


def _conversation_title(content: str) -> str:
    normalized = " ".join(content.split())
    return normalized if len(normalized) <= 80 else f"{normalized[:77].rstrip()}..."
