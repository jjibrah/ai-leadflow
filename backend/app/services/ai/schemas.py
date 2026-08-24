from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AIProcessingOutput(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    category: Literal[
        "sales",
        "support",
        "partnership",
        "general",
        "spam",
    ]

    priority: Literal[
        "low",
        "medium",
        "high",
    ]

    intent: str = Field(min_length=1, max_length=200)

    company: str | None = Field(
        default=None,
        max_length=200,
    )

    summary: str = Field(
        min_length=1,
        max_length=500,
    )

    suggested_response: str = Field(
        min_length=1,
        max_length=2000,
    )

    @field_validator("company", mode="after")
    @classmethod
    def normalize_company(cls, value: str | None) -> str | None:
        return value or None
