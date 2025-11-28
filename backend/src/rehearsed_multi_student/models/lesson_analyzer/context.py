"""Lesson analyzer context returned to agents.

This is what the lesson analyzer service returns and passes to all other components.
"""

from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from .outputs import StudentApproachOutput


class LessonContext(BaseModel):
    """Extracted lesson context from a lesson plan.
    
    This is what the lesson analyzer returns. It contains:
    - Core lesson info (grade, subject, topic)
    - Learning objectives and key concepts
    - A summary describing how students at this grade think about this topic
    - The actual mathematical problem being discussed
    - Student approaches indexed by student_id (so each student agent knows their approach)
    
    This is passed to:
    - Student agents (with their specific approach included)
    - Feedback agents (so they can evaluate against subskills)
    - Lesson summary agents (context for overall feedback)
    """
    
    grade_level: str = Field(description="Grade level (e.g., '3rd grade', '11th grade', 'K-2')")
    subject: str = Field(description="Subject area (e.g., 'Mathematics', 'Algebra')")
    topic: str = Field(description="Specific topic (e.g., 'Linear Equations', 'Fractions')")
    learning_objectives: List[str] = Field(description="What students should learn")
    key_concepts: List[str] = Field(description="Important concepts/vocabulary")
    context_summary: str = Field(
        description="Summary of how students at this grade level typically approach this topic"
    )
    
    # The actual mathematical problem being discussed
    mathematical_problem: Optional[str] = Field(
        default=None,
        description="The specific mathematical problem or scenario (e.g., the fish/tanks problem)"
    )
    
    # Student approaches indexed by ID
    # Each student agent will use their own approach from this dict
    student_approaches: Dict[str, StudentApproachOutput] = Field(
        default_factory=dict,
        description="Map of student_id -> StudentApproachOutput, generated for each profile to inform how they think about this problem"
    )
