"""Feedback agent response models."""

from typing import List, Optional
from pydantic import BaseModel, Field


class FeedbackInsight(BaseModel):
    """A single feedback insight for the teacher."""
    
    category: str = Field(..., description="Category: equity, wait_time, question_quality, follow_up, engagement")
    message: str = Field(..., description="Specific, actionable feedback")
    severity: str = Field(..., description="info, suggestion, or concern")


class TeacherFeedback(BaseModel):
    """Comprehensive feedback on teacher's instructional moves."""
    
    insights: List[FeedbackInsight] = Field(default_factory=list)
    overall_observation: Optional[str] = Field(None, description="High-level summary of this interaction")
