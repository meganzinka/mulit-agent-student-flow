"""Lesson summary agent request models."""

from typing import List
from pydantic import BaseModel, Field
from ..domain import ConversationMessage
from ..lesson_analyzer import LessonContext


class EndLessonRequest(BaseModel):
    """Request to end a lesson and get comprehensive feedback."""
    
    lesson_context: LessonContext = Field(description="The lesson that was taught")
    conversation_transcript: List[ConversationMessage] = Field(
        description="Complete transcript of the lesson conversation"
    )
