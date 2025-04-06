import time
from typing import Any, Dict
import uuid
from datetime import datetime, timedelta, timezone
from datamodel import BaseModel, Field


def created_at(*args, **kwargs) -> int:
    """Get the current time in milliseconds since epoch.
    """
    return int(datetime.now(timezone.utc).timestamp() * 1000)

def default_consent():
    return {
        "location": False,
        "profile": False,
        "graph": False
    }

class UserProfile(BaseModel):
    """User Profile for User State Management.
    """
    id: str
    name: str
    email: str
    upn: str
    profile: Dict[str, Any] = Field(required=False, default_factory=dict)
    location: Dict[str, Any] = Field(required=False, default_factory=dict)
    tenant_id: str
    graph_data: Dict[str, Any] = Field(required=False, default_factory=dict)
    sid: uuid.UUID = Field(primary_key=True, required=False, default=uuid.uuid4)
    at: int = Field(default=created_at)
    preferences: Dict[str, Any] = Field(required=False, default_factory=dict)
    last_interaction: datetime
    ip_address: str
    device_info: Dict[str, Any] = Field(required=False, default_factory=dict)
    consents: Dict[str, bool] = Field(required=False, default=default_consent)


class ConversationData(BaseModel):
    """Conversation Data for Conversation State Management.
    """
    conversation_id: str
    timestamp: str
    channel_id: str
    user_id: str
    bot_id: str
    service_url: str
    locale: str
    prompted_for_user_name: bool = Field(required=False, default=False)
    entities: dict = Field(required=False, default_factory=dict)


class ChatResponse(BaseModel):
    """ChatResponse.
    dict_keys(
        ['question', 'chat_history', 'answer', 'source_documents', 'generated_question']
    )

    Response from Chatbots.
    """
    query: str = Field(required=False)
    result: str = Field(required=False)
    question: str = Field(required=False)
    generated_question: str = Field(required=False)
    answer: str = Field(required=False)
    response: str = Field(required=False)
    chat_history: list = Field(repr=True, default_factory=list)
    source_documents: list = Field(required=False, default_factory=list)
    documents: dict = Field(required=False, default_factory=dict)
    sid: uuid.UUID = Field(primary_key=True, required=False, default=uuid.uuid4)
    at: int = Field(default=created_at)

    def __post_init__(self) -> None:
        if self.result and not self.answer:
            self.answer = self.result
        if self.question and not self.generated_question:
            self.generated_question = self.question
        return super().__post_init__()
