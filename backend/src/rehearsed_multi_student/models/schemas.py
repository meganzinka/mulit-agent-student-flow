"""Pydantic models for student profiles and API requests/responses."""

from typing import List, Optional
from pydantic import BaseModel, Field


class ConversationMessage(BaseModel):
    """A single message in the conversation history."""
    
    speaker: str = Field(description="The speaker (e.g., 'teacher', student name)")
    message: str = Field(description="The message content")


class LessonContext(BaseModel):
    """Structured context about the lesson being taught."""
    
    grade_level: str = Field(description="Grade level (e.g., '3rd grade', '11th grade', 'K-2')")
    subject: str = Field(description="Subject area (e.g., 'Mathematics', 'Algebra')")
    topic: str = Field(description="Specific topic (e.g., 'Linear Equations', 'Fractions')")
    learning_objectives: List[str] = Field(description="What students should learn")
    key_concepts: List[str] = Field(description="Important concepts/vocabulary")
    context_summary: str = Field(description="Brief summary of the lesson for agent context")


class LessonSetupRequest(BaseModel):
    """Request to set up a lesson from a lesson plan."""
    
    lesson_plan_text: str = Field(description="The lesson plan text")
    lesson_plan_pdf_base64: Optional[str] = Field(
        default=None,
        description="Optional base64-encoded PDF of the lesson plan"
    )


class VoiceSettings(BaseModel):
    """Voice configuration for text-to-speech."""
    
    language_code: str = Field(default="en-US", description="Language code for TTS")
    voice_name: str = Field(description="Google Cloud TTS voice name")
    pitch: float = Field(default=0.0, ge=-20.0, le=20.0, description="Voice pitch adjustment")
    speaking_rate: float = Field(default=1.0, ge=0.25, le=4.0, description="Speaking rate multiplier")


class StudentTraits(BaseModel):
    """Personality and behavioral traits of a student."""
    
    confidence_level: float = Field(ge=0.0, le=1.0, description="Student's confidence level (0-1)")
    participation_willingness: float = Field(ge=0.0, le=1.0, description="Likelihood to participate (0-1)")
    processing_speed: str = Field(description="How quickly student processes information")


class HandRaisingCriteria(BaseModel):
    """Criteria that determine whether a student raises their hand."""
    
    requires_clear_procedure: bool
    comfort_with_ambiguity: float = Field(ge=0.0, le=1.0)
    needs_preparation_time: bool
    prefers_structured_questions: bool
    needs_high_confidence: Optional[bool] = None
    can_visualize_problem: Optional[bool] = None
    recognizes_familiar_pattern: Optional[bool] = None


class StudentProfile(BaseModel):
    """Complete profile of a student including personality and learning style."""
    
    id: str
    name: str
    learning_style: str
    description: str
    traits: StudentTraits
    strengths: List[str]
    challenges: List[str]
    hand_raising_criteria: HandRaisingCriteria
    response_patterns: List[str]
    thinking_approach: str
    voice_settings: VoiceSettings


class TeacherPromptRequest(BaseModel):
    """Request from teacher with prompt and lesson context."""
    
    prompt: str = Field(description="The question the teacher is asking")
    lesson_context: Optional[LessonContext] = Field(
        default=None,
        description="Context about the lesson (grade level, topic, objectives)"
    )
    conversation_history: List[ConversationMessage] = Field(
        default_factory=list,
        description="Previous conversation messages for context"
    )


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
