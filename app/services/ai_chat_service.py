import json
import re
from collections.abc import Sequence
from datetime import UTC, datetime

import httpx
from fastapi import HTTPException, status
from sqlalchemy import String, case, cast, func, or_, select
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
Answer clearly and helpfully using the supplied live application database analytics
and conversation. It includes exact whole-database totals, grouped metrics, and
bounded record examples. Treat it as the only source of business facts: do not
invent records, metrics, customer details, or actions. Grouped metrics cover all
matching records; record examples are only samples and cannot establish that an
unlisted record does not exist. Show calculations and state their denominators
when giving rates or comparisons. Distinguish recorded facts from recommendations
and forecasts. Existing baseline predictions are rule-based indicators, not
calibrated probabilities or guarantees. The data is anonymized; never attempt to
identify a person. You can explain or recommend actions, but you cannot claim to
have changed records or contacted anyone."""


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
    chart = _chart_for_question(db, payload.content)
    if chart is not None:
        reply = f"{reply}\n\n```salesboard-chart\n{json.dumps(chart, ensure_ascii=True)}\n```"
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
    question = history[-1].content if history else ""
    context = _database_context(db, question)
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


def _database_context(db: Session, question: str = "") -> str:
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
    converted_leads = db.scalar(
        select(func.count(Lead.id)).where(Lead.status == "converted")
    ) or 0
    campaign_performance = db.execute(
        select(
            Campaign.name,
            Campaign.channel,
            func.count(Lead.id).label("lead_count"),
            func.sum(case((Lead.status == "converted", 1), else_=0)).label("converted_count"),
        )
        .join(Lead, Lead.campaign_id == Campaign.id)
        .group_by(Campaign.id, Campaign.name, Campaign.channel)
        .order_by(func.count(Lead.id).desc(), Campaign.name.asc())
        .limit(20)
    ).all()
    lead_months = db.execute(
        select(
            func.substr(cast(Lead.created_at, String), 1, 7).label("month"),
            func.count(Lead.id),
        )
        .where(Lead.created_at.is_not(None))
        .group_by(func.substr(cast(Lead.created_at, String), 1, 7))
        .order_by(func.substr(cast(Lead.created_at, String), 1, 7).desc())
        .limit(24)
    ).all()
    lead_months.reverse()
    call_metrics = db.execute(
        select(
            func.count(Call.id),
            func.sum(case((Call.status == "completed", 1), else_=0)),
            func.avg(Call.duration_seconds),
            func.sum(Call.duration_seconds),
        )
    ).one()
    engagement = db.execute(
        select(
            EngagementEvent.channel,
            EngagementEvent.metric_type,
            func.count(EngagementEvent.id),
            func.sum(EngagementEvent.metric_value),
        )
        .group_by(EngagementEvent.channel, EngagementEvent.metric_type)
        .order_by(func.count(EngagementEvent.id).desc())
        .limit(30)
    ).all()
    website_events = db.execute(
        select(WebsiteEvent.event_name, func.count(WebsiteEvent.id))
        .group_by(WebsiteEvent.event_name)
        .order_by(func.count(WebsiteEvent.id).desc())
        .limit(30)
    ).all()
    prediction_summary = db.execute(
        select(
            AIPrediction.prediction_type,
            AIPrediction.label,
            func.count(AIPrediction.id),
            func.avg(AIPrediction.score),
        )
        .group_by(AIPrediction.prediction_type, AIPrediction.label)
        .order_by(AIPrediction.prediction_type, func.count(AIPrediction.id).desc())
        .limit(40)
    ).all()
    decision_summary = db.execute(
        select(
            DecisionRecommendation.decision_type,
            DecisionRecommendation.recommended_action,
            DecisionRecommendation.priority,
            func.count(DecisionRecommendation.id),
            func.avg(DecisionRecommendation.confidence),
        )
        .group_by(
            DecisionRecommendation.decision_type,
            DecisionRecommendation.recommended_action,
            DecisionRecommendation.priority,
        )
        .order_by(func.count(DecisionRecommendation.id).desc())
        .limit(30)
    ).all()
    outcome_summary = db.execute(
        select(
            LeadOutcome.outcome_code,
            LeadOutcome.action_type,
            func.count(LeadOutcome.id),
            func.sum(case((LeadOutcome.followup_required.is_(True), 1), else_=0)),
        )
        .group_by(LeadOutcome.outcome_code, LeadOutcome.action_type)
        .order_by(func.count(LeadOutcome.id).desc())
        .limit(30)
    ).all()
    import_summary = db.execute(
        select(
            DataImportJob.dataset_name,
            DataImportJob.status,
            func.count(DataImportJob.id),
            func.sum(DataImportJob.row_count),
            func.sum(DataImportJob.invalid_row_count),
        )
        .group_by(DataImportJob.dataset_name, DataImportJob.status)
        .order_by(func.count(DataImportJob.id).desc())
        .limit(30)
    ).all()
    training_summary = db.execute(
        select(
            MLTrainingJob.model_name,
            MLTrainingJob.status,
            func.count(MLTrainingJob.id),
            func.max(MLTrainingJob.training_rows),
        )
        .group_by(MLTrainingJob.model_name, MLTrainingJob.status)
        .order_by(func.count(MLTrainingJob.id).desc())
        .limit(20)
    ).all()
    overdue_tasks = db.scalar(
        select(func.count(Task.id)).where(
            Task.due_at < datetime.now(UTC),
            Task.status.notin_(("completed", "cancelled", "done")),
        )
    ) or 0
    customer_profile = {
        "gender": _grouped_counts(db, Customer.crm_gender, Customer.id),
        "age_band": _grouped_counts(db, Customer.crm_age_band, Customer.id),
        "income_band": _grouped_counts(db, Customer.crm_income_band, Customer.id),
        "occupation": _grouped_counts(db, Customer.crm_occupation, Customer.id, limit=15),
        "education": _grouped_counts(db, Customer.crm_education, Customer.id, limit=15),
        "tobacco_user": _grouped_counts(db, Customer.crm_tobacco_user, Customer.id),
        "nonresident": _grouped_counts(db, Customer.crm_nonresident_flag, Customer.id),
        "existing_plan": _grouped_counts(db, Customer.crm_existing_plan_flag, Customer.id),
    }
    product_leads = db.execute(
        select(Product.name, func.count(Lead.id))
        .join(Product, Product.code == Lead.excel_fields["CRM_Product_Code"].as_string())
        .group_by(Product.name)
        .order_by(func.count(Lead.id).desc())
        .limit(20)
    ).all()
    matched_leads = _matched_lead_records(db, question)
    leads = db.execute(
        select(
            Lead.id,
            Customer.external_customer_id,
            Lead.status,
            Lead.current_stage,
            Lead.current_section,
            Lead.current_handler,
            Lead.priority,
            Lead.lead_score,
            Lead.recommended_action,
        )
        .join(Customer, Customer.id == Lead.customer_id)
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
            "conversion_summary": {
                "total_leads": counts["leads"],
                "converted_leads": converted_leads,
                "conversion_rate": (
                    round(converted_leads / counts["leads"], 4) if counts["leads"] else 0
                ),
                "rate_definition": "converted leads divided by all leads",
            },
            "lead_counts_by_status": {status: count for status, count in statuses},
            "lead_counts_by_source_channel": {channel: count for channel, count in channels},
            "lead_counts_by_source_medium": _grouped_counts(db, Lead.source_medium, Lead.id),
            "lead_counts_by_stage": {stage: count for stage, count in stages},
            "lead_counts_by_priority": _grouped_counts(db, Lead.priority, Lead.id),
            "lead_counts_by_section": _grouped_counts(db, Lead.current_section, Lead.id),
            "lead_counts_by_handler": _grouped_counts(db, Lead.current_handler, Lead.id, limit=30),
            "call_counts_by_status": {status: count for status, count in call_statuses},
            "call_metrics": {
                "total_calls": call_metrics[0] or 0,
                "completed_calls": call_metrics[1] or 0,
                "average_duration_seconds": _round_or_none(call_metrics[2]),
                "total_duration_seconds": call_metrics[3] or 0,
            },
            "task_counts_by_status": {status: count for status, count in task_statuses},
            "task_counts_by_priority": _grouped_counts(db, Task.priority, Task.id),
            "overdue_open_tasks": overdue_tasks,
            "followup_counts_by_status": {status: count for status, count in followup_statuses},
            "followup_counts_by_channel": _grouped_counts(db, Followup.channel, Followup.id),
            "customer_profile_counts": customer_profile,
            "campaign_performance": [
                {
                    "campaign": name,
                    "channel": channel,
                    "leads": lead_count,
                    "converted": converted_count or 0,
                    "conversion_rate": (
                        round((converted_count or 0) / lead_count, 4) if lead_count else 0
                    ),
                }
                for name, channel, lead_count, converted_count in campaign_performance
            ],
            "product_lead_counts": [
                {"product": name, "leads": count} for name, count in product_leads
            ],
            "lead_creation_by_month": [
                {"month": month, "leads": count} for month, count in lead_months
            ],
            "engagement_by_channel_and_metric": [
                {"channel": channel, "metric": metric, "events": count, "value_sum": total or 0}
                for channel, metric, count, total in engagement
            ],
            "website_events_by_name": {
                name: count for name, count in website_events
            },
            "prediction_counts_by_type_and_label": [
                {
                    "type": prediction_type,
                    "label": label,
                    "count": count,
                    "average_score": _round_or_none(score),
                }
                for prediction_type, label, count, score in prediction_summary
            ],
            "recommendations_by_type_action_and_priority": [
                {
                    "type": decision_type,
                    "action": action,
                    "priority": priority,
                    "count": count,
                    "average_confidence": _round_or_none(confidence),
                }
                for decision_type, action, priority, count, confidence in decision_summary
            ],
            "lead_outcomes_by_code_and_action": [
                {
                    "outcome": outcome_code,
                    "action": action_type,
                    "count": count,
                    "followup_required": followup_count or 0,
                }
                for outcome_code, action_type, count, followup_count in outcome_summary
            ],
            "data_imports_by_dataset_and_status": [
                {
                    "dataset": dataset,
                    "status": import_status,
                    "jobs": jobs,
                    "rows": row_count or 0,
                    "invalid_rows": invalid_rows or 0,
                }
                for dataset, import_status, jobs, row_count, invalid_rows in import_summary
            ],
            "model_training_by_name_and_status": [
                {
                    "model": model_name,
                    "status": training_status,
                    "jobs": jobs,
                    "latest_training_rows": training_rows or 0,
                }
                for model_name, training_status, jobs, training_rows in training_summary
            ],
            "lead_assignments_by_handler": _grouped_counts(
                db,
                LeadAssignment.to_handler,
                LeadAssignment.id,
                limit=30,
            ),
            "lead_timeline_events_by_type": _grouped_counts(
                db,
                LeadTimelineEvent.event_type,
                LeadTimelineEvent.id,
                limit=30,
            ),
            "average_lead_score": average_score,
            "data_snapshot_generated_at": datetime.now(UTC).isoformat(),
            "listed_record_limits": {
                "highest_scored_leads": 15,
                "products": 25,
                "campaigns": 25,
                "campaign_performance": 20,
            },
            "highest_scored_leads": [
                {
                    "lead_id": lead_id,
                    "customer_id": customer_id,
                    "status": status,
                    "stage": stage,
                    "section": section,
                    "handler": handler,
                    "priority": priority,
                    "score": score,
                    "recommended_action": action,
                }
                for (
                    lead_id,
                    customer_id,
                    status,
                    stage,
                    section,
                    handler,
                    priority,
                    score,
                    action,
                ) in leads
            ],
            "requested_lead_records": matched_leads,
            "products": [{"code": code, "name": name} for code, name in products],
            "campaigns": [
                {"code": code, "name": name, "channel": channel, "status": status}
                for code, name, channel, status in campaigns
            ],
        },
        ensure_ascii=True,
        default=str,
    )


def _grouped_counts(
    db: Session,
    field,
    record_id,
    *,
    limit: int = 20,
) -> dict[str, int]:
    rows = db.execute(
        select(field, func.count(record_id))
        .group_by(field)
        .order_by(func.count(record_id).desc(), field.asc())
        .limit(limit)
    ).all()
    return {str(value) if value is not None else "unknown": count for value, count in rows}


def _round_or_none(value) -> float | None:
    return round(float(value), 4) if value is not None else None


def _chart_for_question(db: Session, question: str) -> dict[str, object] | None:
    lowered = question.lower()
    if not any(term in lowered for term in ("chart", "graph", "plot", "visual", "trend")):
        return None

    chart_type = (
        "line"
        if any(term in lowered for term in ("trend", "over time", "month"))
        else "bar"
    )
    if "conversion" in lowered and chart_type == "line":
        rows = db.execute(
            select(
                func.substr(cast(Lead.created_at, String), 1, 7),
                func.count(Lead.id),
            )
            .where(Lead.status == "converted", Lead.created_at.is_not(None))
            .group_by(func.substr(cast(Lead.created_at, String), 1, 7))
            .order_by(func.substr(cast(Lead.created_at, String), 1, 7).desc())
            .limit(24)
        ).all()
        rows.reverse()
        title, metric = "Monthly converted leads", "Converted leads"
    elif "conversion" in lowered:
        converted_count = func.sum(case((Lead.status == "converted", 1), else_=0))
        rows = db.execute(
            select(Campaign.name, converted_count * 100.0 / func.count(Lead.id))
            .join(Lead, Lead.campaign_id == Campaign.id)
            .group_by(Campaign.name)
            .order_by((converted_count * 100.0 / func.count(Lead.id)).desc())
            .limit(12)
        ).all()
        title, metric = "Conversion rate by campaign", "Conversion rate (%)"
    elif "converted" in lowered or "sales" in lowered:
        rows = db.execute(
            select(Campaign.name, func.count(Lead.id))
            .join(Lead, Lead.campaign_id == Campaign.id)
            .where(Lead.status == "converted")
            .group_by(Campaign.name)
            .order_by(func.count(Lead.id).desc(), Campaign.name.asc())
            .limit(12)
        ).all()
        title, metric = "Converted leads by campaign", "Converted leads"
    elif any(term in lowered for term in ("campaign", "campaigns")):
        rows = db.execute(
            select(Campaign.name, func.count(Lead.id))
            .join(Lead, Lead.campaign_id == Campaign.id)
            .group_by(Campaign.name)
            .order_by(func.count(Lead.id).desc(), Campaign.name.asc())
            .limit(12)
        ).all()
        title, metric = "Leads by campaign", "Leads"
    elif any(term in lowered for term in ("channel", "source")):
        rows = db.execute(
            select(Lead.source_channel, func.count(Lead.id))
            .group_by(Lead.source_channel)
            .order_by(func.count(Lead.id).desc(), Lead.source_channel.asc())
            .limit(12)
        ).all()
        title, metric = "Leads by source channel", "Leads"
    elif any(term in lowered for term in ("product", "products")):
        rows = db.execute(
            select(Product.name, func.count(Lead.id))
            .join(Lead, Product.code == Lead.excel_fields["CRM_Product_Code"].as_string())
            .group_by(Product.name)
            .order_by(func.count(Lead.id).desc(), Product.name.asc())
            .limit(12)
        ).all()
        title, metric = "Leads by product", "Leads"
    elif any(term in lowered for term in ("income", "age", "gender", "occupation")):
        if "income" in lowered:
            field, title = Customer.crm_income_band, "Leads by customer income band"
        elif "age" in lowered:
            field, title = Customer.crm_age_band, "Leads by customer age band"
        elif "gender" in lowered:
            field, title = Customer.crm_gender, "Leads by customer gender"
        else:
            field, title = Customer.crm_occupation, "Leads by customer occupation"
        rows = db.execute(
            select(field, func.count(Lead.id))
            .join(Customer, Customer.id == Lead.customer_id)
            .group_by(field)
            .order_by(func.count(Lead.id).desc(), field.asc())
            .limit(12)
        ).all()
        metric = "Leads"
    elif any(term in lowered for term in ("call", "calls")):
        rows = db.execute(
            select(Call.status, func.count(Call.id))
            .group_by(Call.status)
            .order_by(func.count(Call.id).desc(), Call.status.asc())
            .limit(12)
        ).all()
        title, metric = "Calls by status", "Calls"
    elif "task" in lowered:
        rows = db.execute(
            select(Task.status, func.count(Task.id))
            .group_by(Task.status)
            .order_by(func.count(Task.id).desc(), Task.status.asc())
            .limit(12)
        ).all()
        title, metric = "Tasks by status", "Tasks"
    elif "followup" in lowered or "follow-up" in lowered:
        rows = db.execute(
            select(Followup.status, func.count(Followup.id))
            .group_by(Followup.status)
            .order_by(func.count(Followup.id).desc(), Followup.status.asc())
            .limit(12)
        ).all()
        title, metric = "Follow-ups by status", "Follow-ups"
    elif "prediction" in lowered:
        rows = db.execute(
            select(AIPrediction.label, func.count(AIPrediction.id))
            .group_by(AIPrediction.label)
            .order_by(func.count(AIPrediction.id).desc(), AIPrediction.label.asc())
            .limit(12)
        ).all()
        title, metric = "Predictions by label", "Predictions"
    elif "recommendation" in lowered:
        rows = db.execute(
            select(DecisionRecommendation.priority, func.count(DecisionRecommendation.id))
            .group_by(DecisionRecommendation.priority)
            .order_by(
                func.count(DecisionRecommendation.id).desc(),
                DecisionRecommendation.priority.asc(),
            )
            .limit(12)
        ).all()
        title, metric = "Recommendations by priority", "Recommendations"
    elif chart_type == "line":
        rows = db.execute(
            select(
                func.substr(cast(Lead.created_at, String), 1, 7),
                func.count(Lead.id),
            )
            .where(Lead.created_at.is_not(None))
            .group_by(func.substr(cast(Lead.created_at, String), 1, 7))
            .order_by(func.substr(cast(Lead.created_at, String), 1, 7).desc())
            .limit(24)
        ).all()
        rows.reverse()
        title, metric = "Lead creation trend", "Leads"
    else:
        rows = db.execute(
            select(Lead.status, func.count(Lead.id))
            .group_by(Lead.status)
            .order_by(func.count(Lead.id).desc(), Lead.status.asc())
            .limit(12)
        ).all()
        title, metric = "Leads by status", "Leads"

    data = [
        {"label": str(label) if label is not None else "unknown", "value": float(value or 0)}
        for label, value in rows
    ]
    if not data:
        return None
    return {
        "type": chart_type,
        "title": title,
        "metric": metric,
        "data": data,
    }


def _matched_lead_records(db: Session, question: str) -> list[dict[str, object]]:
    conditions = []
    lead_ids = {
        int(value)
        for value in re.findall(r"\blead(?:\s+id)?\s*#?\s*(\d+)\b", question, re.IGNORECASE)
    }
    if lead_ids:
        conditions.append(Lead.id.in_(lead_ids))

    customer_ids = set(re.findall(r"\bCUST[_-][A-Z0-9_-]+\b", question, re.IGNORECASE))
    customer_refs = {
        value
        for value in re.findall(
            r"\bcustomer\s+(?:id\s*)?[:#]?\s*([A-Z][A-Z0-9_-]*\d[A-Z0-9_-]*)\b",
            question,
            re.IGNORECASE,
        )
    }
    external_ids = customer_ids | customer_refs
    if external_ids:
        conditions.append(Customer.external_customer_id.in_(external_ids))
    if not conditions:
        return []

    rows = db.execute(
        select(
            Lead.id,
            Customer.external_customer_id,
            Lead.status,
            Lead.current_stage,
            Lead.current_section,
            Lead.current_handler,
            Lead.priority,
            Lead.lead_score,
            Lead.recommended_action,
            Lead.source_channel,
            Campaign.name,
            Product.name,
        )
        .join(Customer, Customer.id == Lead.customer_id)
        .outerjoin(Campaign, Campaign.id == Lead.campaign_id)
        .outerjoin(Product, Product.code == Lead.excel_fields["CRM_Product_Code"].as_string())
        .where(or_(*conditions))
        .order_by(Lead.id.asc())
        .limit(10)
    ).all()
    predictions_by_lead: dict[int, list[dict[str, object]]] = {}
    prediction_rows = db.execute(
        select(
            AIPrediction.lead_id,
            AIPrediction.prediction_type,
            AIPrediction.model_name,
            AIPrediction.score,
            AIPrediction.label,
        )
        .where(AIPrediction.lead_id.in_([row[0] for row in rows]))
        .order_by(AIPrediction.created_at.desc(), AIPrediction.id.desc())
        .limit(50)
    ).all()
    for lead_id, prediction_type, model_name, score, label in prediction_rows:
        predictions = predictions_by_lead.setdefault(lead_id, [])
        if not any(item["type"] == prediction_type for item in predictions):
            predictions.append(
                {
                    "type": prediction_type,
                    "model": model_name,
                    "score": score,
                    "label": label,
                }
            )
    return [
        {
            "lead_id": lead_id,
            "customer_id": customer_id,
            "status": status,
            "stage": stage,
            "section": section,
            "handler": handler,
            "priority": priority,
            "score": score,
            "recommended_action": action,
            "source_channel": channel,
            "campaign": campaign,
            "product": product,
            "latest_predictions": predictions_by_lead.get(lead_id, []),
        }
        for (
            lead_id,
            customer_id,
            status,
            stage,
            section,
            handler,
            priority,
            score,
            action,
            channel,
            campaign,
            product,
        ) in rows
    ]


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
