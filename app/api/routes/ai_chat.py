from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.ai_chat import (
    AIChatConversationCreate,
    AIChatConversationDetail,
    AIChatConversationRead,
    AIChatMessageCreate,
    AIChatModelRead,
    AIChatTurnRead,
)
from app.services import ai_chat_service

router = APIRouter(prefix="/ai/chat", tags=["ai-chat"])


@router.get("/models", response_model=list[AIChatModelRead])
def get_chat_models() -> list[AIChatModelRead]:
    return ai_chat_service.list_models()


@router.get("/conversations", response_model=list[AIChatConversationRead])
def list_chat_conversations(db: Session = Depends(get_db)) -> list[AIChatConversationRead]:
    return ai_chat_service.list_conversations(db)


@router.post(
    "/conversations",
    response_model=AIChatConversationRead,
    status_code=status.HTTP_201_CREATED,
)
def create_chat_conversation(
    payload: AIChatConversationCreate,
    db: Session = Depends(get_db),
) -> AIChatConversationRead:
    return ai_chat_service.create_conversation(db, payload)


@router.get(
    "/conversations/{conversation_id}",
    response_model=AIChatConversationDetail,
)
def get_chat_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
) -> AIChatConversationDetail:
    conversation = ai_chat_service.get_conversation(db, conversation_id)
    return AIChatConversationDetail(
        **AIChatConversationRead.model_validate(conversation).model_dump(),
        messages=ai_chat_service.get_conversation_messages(db, conversation_id),
    )


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=AIChatTurnRead,
)
def send_chat_message(
    conversation_id: int,
    payload: AIChatMessageCreate,
    db: Session = Depends(get_db),
) -> AIChatTurnRead:
    return ai_chat_service.send_message(db, conversation_id, payload)


@router.delete(
    "/conversations/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_chat_conversation(conversation_id: int, db: Session = Depends(get_db)) -> Response:
    ai_chat_service.delete_conversation(db, conversation_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
