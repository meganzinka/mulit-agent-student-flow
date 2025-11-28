"""Output schemas for LLM responses.

These models define the structured output that LLMs will return and are used
as output_schema in Gemini API calls for guaranteed structured data.
"""

from pydantic import BaseModel, Field
from typing import List, Optional


class LessonAnalysisOutput(BaseModel):
    """Output schema for lesson plan analysis."""
    
    grade_level: str = Field(description="Grade level (e.g., '3rd grade', '9th grade', 'High School')")
    subject: str = Field(description="Subject area (e.g., 'Mathematics', 'Algebra II')")
    topic: str = Field(description="Specific topic being taught")
    learning_objectives: List[str] = Field(description="What students should learn")
    key_concepts: List[str] = Field(description="Key vocabulary and concepts")
    context_summary: str = Field(description="Brief paragraph on how students at this grade level approach this topic")


class LessonSummaryOutput(BaseModel):
    """Output schema for comprehensive end-of-lesson feedback."""
    
    lesson_summary: "LessonSummaryDetail" = Field(description="Structured lesson statistics")
    overall_feedback: str = Field(description="Narrative paragraph on mathematical discourse quality")
    strengths_and_growth: "StrengthsAndGrowthOutput" = Field(description="Teacher strengths and growth areas")
    next_steps: "NextStepsOutput" = Field(description="Actionable strategies")
    celebration: str = Field(description="Warm, encouraging message")


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


class FeedbackInsightOutput(BaseModel):
    """Output schema for a single feedback insight."""
    
    category: str = Field(description="Feedback category")
    message: str = Field(description="Specific, actionable feedback")
    severity: str = Field(description="info, suggestion, or concern")


class TeacherFeedbackOutput(BaseModel):
    """Output schema for real-time coaching feedback."""
    
    insights: List[FeedbackInsightOutput] = Field(description="List of coaching insights")
    overall_observation: Optional[str] = Field(default=None, description="Summary of this interaction")


# Update forward references for Pydantic
LessonSummaryOutput.model_rebuild()
