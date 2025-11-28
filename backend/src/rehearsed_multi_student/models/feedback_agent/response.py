"""Feedback agent response models."""

from typing import Optional
from pydantic import BaseModel, Field


class FeedbackInsight(BaseModel):
    """Legacy feedback insight structure (kept for backward compatibility with frontend)."""
    
    category: str = Field(..., description="Category of insight")
    message: str = Field(..., description="Feedback message")
    severity: str = Field(..., description="Severity level: info, suggestion, or concern")


class TeacherFeedback(BaseModel):
    """Real-time coaching feedback for the teacher on mathematical discourse.
    
    Provides:
    - feedback: Analysis of what the teacher just said (what they did well, what could improve)
    - suggestion: Actionable coaching prompt (what to consider next)
    - question_type: Classification of the question type demonstrated (if any)
    
    All feedback is framed in second person (you/your) and references the specific
    mathematical problem and student responses to ground the coaching.
    """
    
    question_type: Optional[str] = Field(
        None,
        description="Type of question demonstrated: 'build_on', 'probing', 'visibility', or None if not present"
    )
    
    feedback: str = Field(
        ...,
        description="Analysis of the teacher's last statement. What they did well, what could improve. Second person (you/your). References specific quotes from what was said and student responses."
    )
    
    suggestion: str = Field(
        ...,
        description="Actionable coaching suggestion. Framed as something to consider or try next. Second person. Displayed as popup to teacher. Focuses on one specific move they could make to strengthen mathematical discourse."
    )
