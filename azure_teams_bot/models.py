import time
import uuid
from datamodel import BaseModel, Field


class UserProfile(BaseModel):
    """User Profile for User State Management.
    """
    name: str
    email: str
    profile: dict = Field(required=False, default_factory=dict)


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


def created_at(*args, **kwargs) -> int:
    return int(time.time()) * 1000


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
