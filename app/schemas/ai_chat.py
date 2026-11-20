from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AIChatModelRead(BaseModel):
    provider: str
    model_id: str
    name: str
    configured: bool


class AIChatConversationCreate(BaseModel):
    model_id: str = Field(min_length=1, max_length=100)


class AIChatMessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=8000)
    model_id: str | None = Field(default=None, max_length=100)


class AIChatConversationRead(BaseModel):
    id: int
    title: str
    provider: str
    model_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AIChatMessageRead(BaseModel):
    id: int
    conversation_id: int
    role: str
    content: str
    model_id: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AIChatConversationDetail(AIChatConversationRead):
    messages: list[AIChatMessageRead]


class AIChatTurnRead(BaseModel):
    conversation: AIChatConversationRead
    user_message: AIChatMessageRead
    assistant_message: AIChatMessageRead
