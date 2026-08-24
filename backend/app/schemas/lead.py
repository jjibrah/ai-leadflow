from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import LeadPriority, LeadStatus


class LeadCreate(BaseModel):
    enquiry_id: UUID

    name: str = Field(min_length=2, max_length=255)
    email: str = Field(min_length=3, max_length=255)
    company: str | None = Field(default=None, max_length=255)

    category: str = Field(min_length=1, max_length=100)
    priority: LeadPriority

    intent: str = Field(min_length=1, max_length=255)
    summary: str = Field(min_length=1)
    suggested_response: str = Field(min_length=1)

    status: LeadStatus = LeadStatus.NEW


class LeadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    enquiry_id: UUID

    name: str
    email: str
    company: str | None

    category: str
    priority: LeadPriority

    intent: str
    summary: str
    suggested_response: str

    status: LeadStatus
