"""Lesson summary agent LLM output schema.

What Gemini returns when summarizing an end-of-lesson conversation.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class LessonSummaryDetail(BaseModel):
    """Details about what occurred during the lesson."""
    
    total_exchanges: int = Field(description="Total number of exchanges")
    students_called_on: List[str] = Field(description="Student names who participated")
    participation_pattern: str = Field(description="Summary of participation")
    key_moments: List[str] = Field(description="Notable moments")


class StrengthsAndGrowthOutput(BaseModel):
    """Teacher strengths and areas for growth."""
    
    strengths: List[str] = Field(description="Specific things teacher did well with evidence")
    areas_for_growth: List[str] = Field(description="Specific areas to improve with evidence")


class NextStepsOutput(BaseModel):
    """Actionable next steps for teacher development."""
    
    immediate_actions: List[str] = Field(description="Actions to try in the next lesson")
    practice_focus: str = Field(description="One skill to focus on practicing")
    resources: Optional[List[str]] = Field(default=None, description="Suggested resources")


class LessonSummaryOutput(BaseModel):
    """Output schema for comprehensive end-of-lesson feedback."""
    
    lesson_summary: LessonSummaryDetail = Field(description="Structured lesson statistics")
    overall_feedback: str = Field(description="Narrative paragraph on mathematical discourse quality")
    strengths_and_growth: StrengthsAndGrowthOutput = Field(description="Teacher strengths and growth areas")
    next_steps: NextStepsOutput = Field(description="Actionable strategies")
    celebration: str = Field(description="Warm, encouraging message")
