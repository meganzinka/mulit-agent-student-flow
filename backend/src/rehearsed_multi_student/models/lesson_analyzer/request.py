"""Lesson analyzer request models."""

from typing import Optional
from pydantic import BaseModel, Field


class LessonSetupRequest(BaseModel):
    """Request to set up a lesson from a lesson plan."""
    
    lesson_plan_text: str = Field(description="The lesson plan text")
    lesson_plan_pdf_base64: Optional[str] = Field(
        default=None,
        description="Optional base64-encoded PDF of the lesson plan"
    )
