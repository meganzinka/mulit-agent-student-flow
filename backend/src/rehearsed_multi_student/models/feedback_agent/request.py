"""Feedback agent request models."""

from typing import List
from pydantic import BaseModel, Field
from ..domain import ConversationMessage
from ..lesson_analyzer import LessonContext


class FeedbackContext(BaseModel):
    """Context provided to feedback agents for coaching.
    
    Combines:
    - LessonContext (the mathematical problem, subskills, and all student approaches)
    - Conversation history (what's been said so far)
    - Specific teacher move to evaluate
    - Recent student responses for context
    
    Feedback agents use subskills and student approaches to provide targeted
    coaching on mathematical discourse quality.
    """
    
    lesson_context: LessonContext = Field(
        description="The lesson being taught (problem, subskills, and student approaches)"
    )
    
    conversation_history: List[ConversationMessage] = Field(
        default_factory=list,
        description="Transcript of teacher-student exchanges so far"
    )
    
    latest_teacher_statement: str = Field(
        description="The most recent teacher statement to evaluate"
    )
    
    latest_student_responses: List[dict] = Field(
        default_factory=list,
        description="Recent student responses for context (thinking, confidence, etc.)"
    )
