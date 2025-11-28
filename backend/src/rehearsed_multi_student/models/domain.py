"""Shared domain models used across all components.

These are core models that multiple components depend on:
- StudentProfile and related traits
- ConversationMessage for conversation history
- VoiceSettings for TTS
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class ConversationMessage(BaseModel):
    """A single message in the conversation history."""
    
    speaker: str = Field(description="The speaker (e.g., 'teacher', student name)")
    message: str = Field(description="The message content")


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


class HandRaisingCriteria(BaseModel):
    """Criteria that determine whether a student raises their hand."""
    
    requires_clear_procedure: bool
    comfort_with_ambiguity: float = Field(ge=0.0, le=1.0)
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
