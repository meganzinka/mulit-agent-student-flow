"""Student agent response models."""

from typing import Optional, List
from pydantic import BaseModel, Field


class StudentResponse(BaseModel):
    """Response from a single student agent."""
    
    student_id: str
    student_name: str
    would_raise_hand: bool
    confidence_score: float = Field(
        ge=0.0,
        le=1.0,
        description="How confident the student feels about their answer"
    )
    thinking_process: str = Field(description="Student's internal reasoning")
    response: Optional[str] = Field(
        default=None,
        description="The actual response if student would speak"
    )
    audio_base64: Optional[str] = Field(
        default=None,
        description="Base64-encoded audio (MP3) of the student's response"
    )


class MultiStudentResponse(BaseModel):
    """Response containing all student reactions to teacher's prompt."""
    
    students: List[StudentResponse]
    summary: Optional[str] = Field(
        default=None,
        description="Optional summary of the classroom dynamics"
    )
