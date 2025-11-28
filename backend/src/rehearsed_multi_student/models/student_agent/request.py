"""Student agent request models."""

from typing import List, Optional
from pydantic import BaseModel, Field
from ..domain import ConversationMessage
from ..lesson_analyzer import LessonContext


class TeacherPromptRequest(BaseModel):
    """Request from teacher with prompt and lesson context."""
    
    prompt: str = Field(description="The question the teacher is asking")
    lesson_context: Optional[LessonContext] = Field(
        default=None,
        description="Context about the lesson (grade level, topic, objectives, student approaches)"
    )
    conversation_history: List[ConversationMessage] = Field(
        default_factory=list,
        description="Previous conversation messages for context"
    )
