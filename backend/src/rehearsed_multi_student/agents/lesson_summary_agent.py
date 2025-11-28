"""Agent for generating comprehensive end-of-lesson feedback."""
import json
from typing import List
from google import genai
from google.genai import types
from ..models.domain import ConversationMessage
from ..models.lesson_analyzer import LessonContext
from ..models.lesson_summary_agent import (
    EndLessonResponse,
    LessonSummary,
    StrengthsAndGrowth,
    NextSteps,
    LessonSummaryOutput,
)
from ..prompts import get_lesson_summary_system_prompt


class LessonSummaryAgent:
    """Agent that generates comprehensive end-of-lesson feedback."""
    
    def __init__(self):
        """Initialize lesson summary agent with Gemini."""
        self.client = genai.Client(
            vertexai=True,
            project="upbeat-lexicon-411217",
            location="us-central1"
        )
        self.model_id = "gemini-2.5-flash"
    
    async def generate_lesson_summary(
        self,
        lesson_context: LessonContext,
        conversation_transcript: List[ConversationMessage]
    ) -> EndLessonResponse:
        """
        Generate comprehensive end-of-lesson feedback.
        
        Args:
            lesson_context: Context about the lesson (grade, topic, objectives)
            conversation_transcript: Complete conversation history
            
        Returns:
            EndLessonResponse with summary, feedback, and next steps
        """
        # Build the complete context
        context_parts = [
            "**LESSON CONTEXT:**",
            f"Grade Level: {lesson_context.grade_level}",
            f"Subject: {lesson_context.subject}",
            f"Topic: {lesson_context.topic}",
            "",
            "**Learning Objectives:**",
            *[f"- {obj}" for obj in lesson_context.learning_objectives],
            "",
            "**Key Concepts:**",
            ", ".join(lesson_context.key_concepts),
            "",
            f"**Developmental Context:** {lesson_context.context_summary}",
            "",
            "---",
            "",
            "**COMPLETE LESSON TRANSCRIPT:**",
            ""
        ]
        
        # Add full transcript
        for i, msg in enumerate(conversation_transcript, 1):
            context_parts.append(f"{i}. **{msg.speaker}:** {msg.message}")
        
        context_parts.extend([
            "",
            "---",
            "",
            "Analyze this lesson and provide comprehensive feedback following the framework above."
        ])
        
        analysis_context = "\n".join(context_parts)
        
        # Generate comprehensive feedback
        response = await self.client.aio.models.generate_content(
            model=self.model_id,
            contents=analysis_context,
            config=types.GenerateContentConfig(
                system_instruction=get_lesson_summary_system_prompt(),
                temperature=0.5,  # Balanced creativity and consistency
                response_schema=LessonSummaryOutput
            )
        )
        
        # Parse structured output
        try:
            feedback_output = LessonSummaryOutput.model_validate_json(response.text)
            
            return EndLessonResponse(
                lesson_summary=LessonSummary(**feedback_output.lesson_summary.model_dump()),
                overall_feedback=feedback_output.overall_feedback,
                strengths_and_growth=StrengthsAndGrowth(**feedback_output.strengths_and_growth.model_dump()),
                next_steps=NextSteps(**feedback_output.next_steps.model_dump()),
                celebration=feedback_output.celebration
            )
        except (json.JSONDecodeError, KeyError, Exception) as e:
            # Fallback if parsing fails
            raise ValueError(f"Failed to parse lesson summary: {str(e)}\nResponse: {response.text}")
