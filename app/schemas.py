from pydantic import BaseModel, Field


class RelatedService(BaseModel):
    name: str
    reason: str


class LLMStructuredResponse(BaseModel):
    answer: str
    booking_link: str = ""
    related_services: list[RelatedService] = Field(default_factory=list)
    escalate_to_human: bool = False
    escalation_reason: str | None = None


class RetrievedPassage(BaseModel):
    text: str
    source: str
    page: int | None = None
    distance: float | None = None


class ChatMessage(BaseModel):
    role: str  # user | assistant
    content: str


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


class ChatResponse(BaseModel):
    session_id: str
    answer: str
    booking_link: str | None = None
    related_services: list[RelatedService] = Field(default_factory=list)
    escalated: bool = False
    escalation_reason: str | None = None
    support_url: str | None = None
    sources: list[RetrievedPassage] = Field(default_factory=list)
    retrieval_confidence: float | None = None
