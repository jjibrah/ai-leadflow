from typing import Literal

from pydantic import BaseModel, Field


class AIProcessingOutput(BaseModel):
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