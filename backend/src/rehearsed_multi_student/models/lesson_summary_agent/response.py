"""Lesson summary agent response models."""

from typing import List, Optional
from pydantic import BaseModel, Field


class LessonSummary(BaseModel):
    """Summary of what happened during the lesson."""
    
    total_exchanges: int = Field(description="Total number of teacher-student exchanges")
    students_called_on: List[str] = Field(description="Which students were called on")
    participation_pattern: str = Field(description="Summary of participation patterns")
    key_moments: List[str] = Field(description="Notable moments in the lesson")


class StrengthsAndGrowth(BaseModel):
    """Identified strengths and areas for growth."""
    
    strengths: List[str] = Field(description="What the teacher did well")
    areas_for_growth: List[str] = Field(description="Areas to improve")


class NextSteps(BaseModel):
    """Actionable next steps for the teacher."""
    
    immediate_actions: List[str] = Field(description="Things to try in the next lesson")
    practice_focus: str = Field(description="What skill to focus on practicing")
    resources: Optional[List[str]] = Field(
        default=None,
        description="Suggested resources or readings"
    )


class EndLessonResponse(BaseModel):
    """Comprehensive feedback at the end of a lesson."""
    
    lesson_summary: LessonSummary = Field(description="What happened during the lesson")
    overall_feedback: str = Field(description="Overall narrative feedback")
    strengths_and_growth: StrengthsAndGrowth = Field(description="Strengths and areas for growth")
    next_steps: NextSteps = Field(description="Actionable next steps")
    celebration: str = Field(description="Positive reinforcement message")
