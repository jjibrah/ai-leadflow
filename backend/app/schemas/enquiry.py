from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


class EnquiryCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    email: EmailStr
    company: str | None = Field(default=None, max_length=255)
    message: str = Field(min_length=10, max_length=5000)

    @field_validator("name", "message", mode="before")
    @classmethod
    def strip_required_fields(cls, value):
        if isinstance(value, str):
            return value.strip()

        return value

    @field_validator("company", mode="before")
    @classmethod
    def normalize_company(cls, value):
        if isinstance(value, str):
            value = value.strip()

            if not value:
                return None

        return value


class EnquiryResponse(BaseModel):
    id: UUID
    status: str
    message: str