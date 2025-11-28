"""Feedback agent for analyzing teacher mathematical discourse."""
import json
from typing import List, Optional
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from ..models.student_agent import StudentResponse
from ..models.domain import ConversationMessage
from ..models.lesson_analyzer import LessonContext
from ..models.feedback_agent import TeacherFeedback
from ..prompts import get_feedback_system_prompt


class FeedbackAnalysisOutput(BaseModel):
    """Structured output from Gemini feedback analysis."""
    
    question_type: Optional[str] = Field(
        None,
        description="Type of question demonstrated: 'build_on', 'probing', 'visibility', or null"
    )
    
    feedback: str = Field(
        ...,
        description="Analysis of the teacher's statement"
    )
    
    suggestion: str = Field(
        ...,
        description="Actionable coaching suggestion"
    )


class FeedbackAgent:
    """Agent that provides real-time coaching feedback to teachers on mathematical discourse."""
    
    def __init__(self):
        """Initialize feedback agent with Gemini."""
        self.client = genai.Client(
            vertexai=True,
            project="upbeat-lexicon-411217",
            location="us-central1"
        )
        self.model_id = "gemini-2.5-flash"
    
    async def analyze_teacher_move(
        self,
        latest_teacher_statement: str,
        student_responses: List[StudentResponse],
        conversation_history: Optional[List[ConversationMessage]] = None,
        lesson_context: Optional[LessonContext] = None
    ) -> TeacherFeedback:
        """
        Analyze a teacher's most recent statement for mathematical discourse quality.
        
        Provides:
        - question_type: Classification of the question type (build_on, probing, visibility, or None)
        - feedback: What the teacher did well or could improve (second person, grounded)
        - suggestion: Actionable coaching tip (second person, specific)
        
        Args:
            latest_teacher_statement: The teacher's most recent statement to evaluate
            student_responses: How students responded to that statement
            conversation_history: Prior conversation for context
            lesson_context: The lesson being taught (problem, student approaches)
            
        Returns:
            TeacherFeedback with question classification, feedback, and suggestion
        """
        
        # Build the prompt context with all necessary information
        prompt_parts = []
        
        # Mathematical problem
        if lesson_context:
            prompt_parts.append(f"**Mathematical Problem:** {lesson_context.mathematical_problem}\n")
            prompt_parts.append(f"**Problem Context:** {lesson_context.context_summary}\n")
        
        # Student approaches
        if lesson_context and lesson_context.student_approaches:
            prompt_parts.append("**Student Approaches to This Problem:**")
            for student_id, approach in lesson_context.student_approaches.items():
                prompt_parts.append(f"\n- **{approach.student_name}** ({approach.learning_style} learner):")
                prompt_parts.append(f"  How they think about this problem: {approach.thinking_approach}")
            prompt_parts.append("")
        
        # Conversation history
        if conversation_history:
            prompt_parts.append("**Recent Conversation:**")
            for msg in conversation_history[-8:]:  # Last 4 exchanges
                prompt_parts.append(f"  {msg.speaker}: {msg.message}")
            prompt_parts.append("")
        
        # Latest teacher statement
        prompt_parts.append(f"**Teacher's Most Recent Statement:**\n{latest_teacher_statement}\n")
        
        # Student responses
        prompt_parts.append("**How Students Responded:**")
        for response in student_responses:
            if response.would_raise_hand and response.response:
                prompt_parts.append(f"\n- {response.student_name}: \"{response.response}\"")
                prompt_parts.append(f"  Thinking: {response.thinking_process[:80]}...")
            else:
                prompt_parts.append(f"\n- {response.student_name}: (did not raise hand)")
        
        analysis_prompt = "\n".join(prompt_parts)
        
        # Generate feedback with schema validation
        response = await self.client.aio.models.generate_content(
            model=self.model_id,
            contents=analysis_prompt,
            config=types.GenerateContentConfig(
                system_instruction=get_feedback_system_prompt(),
                temperature=0.7,  # Allow some variation in wording
                response_mime_type="application/json",
                response_schema=FeedbackAnalysisOutput,
            )
        )
        
        # Parse structured output
        try:
            feedback_output = FeedbackAnalysisOutput.model_validate_json(response.text)
            return TeacherFeedback(
                question_type=feedback_output.question_type,
                feedback=feedback_output.feedback,
                suggestion=feedback_output.suggestion
            )
        except (json.JSONDecodeError, Exception):
            # Fallback if parsing fails
            return TeacherFeedback(
                question_type=None,
                feedback="Feedback analysis in progress. Please try again.",
                suggestion="Consider asking a follow-up question to deepen student thinking."
            )
