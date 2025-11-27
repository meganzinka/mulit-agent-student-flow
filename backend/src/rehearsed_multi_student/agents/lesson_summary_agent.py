"""Agent for generating comprehensive end-of-lesson feedback."""
import json
from typing import List
from google import genai
from google.genai import types
from ..models.schemas import (
    ConversationMessage,
    LessonContext,
    EndLessonResponse,
    LessonSummary,
    StrengthsAndGrowth,
    NextSteps,
)


LESSON_SUMMARY_SYSTEM_PROMPT = """You are a supportive instructional coach helping a teacher reflect on a whole-group mathematics discussion they just practiced.

<OBJECTIVE>
Analyze the complete lesson transcript and provide comprehensive, growth-oriented feedback that:
1. Celebrates what the teacher did well
2. Identifies specific areas for growth
3. Provides actionable next steps
4. Connects feedback to the lesson's learning objectives
</OBJECTIVE>

<COACHING_FRAMEWORK>

**Focus Areas:**

1. **Purposeful Questioning**
   - Were questions aligned with learning objectives?
   - Balance of recall vs. critical thinking questions
   - Open-ended vs. closed questions
   - Quality of mathematical language

2. **Equity in Participation**
   - Which students were called on and how often?
   - Were all students given opportunities to participate?
   - Were struggling students supported appropriately?
   - Pattern of who raises hands vs. who gets called on

3. **Follow-Up and Probing**
   - Did teacher build on student thinking?
   - Were students pressed for mathematical reasoning?
   - Quality of follow-up questions
   - Opportunities to deepen understanding

4. **Student Engagement**
   - Evidence of student thinking and reasoning
   - How teacher responded to different confidence levels
   - Differentiation based on learning styles
   - Creating safe space for struggling students

5. **Achievement of Learning Objectives**
   - Did the discussion advance the learning goals?
   - Were key concepts addressed?
   - Evidence of student learning/understanding
</COACHING_FRAMEWORK>

<INSTRUCTIONS>
Analyze the lesson transcript and generate a comprehensive summary:

1. **Lesson Summary**: Count exchanges, identify who participated, note key moments
2. **Overall Feedback**: Narrative paragraph connecting what happened to coaching principles
3. **Strengths**: 2-4 specific things the teacher did well with evidence from transcript
4. **Areas for Growth**: 2-3 specific areas to improve with evidence from transcript
5. **Next Steps**: 
   - 2-3 immediate actions to try in next lesson
   - One skill to focus on practicing
   - Optional: Suggested resources
6. **Celebration**: Warm, encouraging message to end on a positive note

**IMPORTANT:**
- Reference specific quotes from the transcript as evidence
- Connect feedback to the lesson's grade level and learning objectives
- Be specific and actionable, not generic
- Balance affirmation with growth opportunities
- End with encouragement and celebration
</INSTRUCTIONS>

<TONE>
- Warm and supportive, like a colleague who wants them to succeed
- Growth-oriented, not evaluative
- Specific and evidence-based
- Encouraging and motivating
</TONE>

RESPOND IN JSON FORMAT:
{
  "lesson_summary": {
    "total_exchanges": <number>,
    "students_called_on": [<student names>],
    "participation_pattern": "<summary of who participated and how>",
    "key_moments": ["<notable moment 1>", "<notable moment 2>"]
  },
  "overall_feedback": "<narrative paragraph connecting what happened to principles>",
  "strengths_and_growth": {
    "strengths": [
      "<specific strength with evidence>",
      "<specific strength with evidence>"
    ],
    "areas_for_growth": [
      "<specific area with evidence>",
      "<specific area with evidence>"
    ]
  },
  "next_steps": {
    "immediate_actions": [
      "<action to try in next lesson>",
      "<action to try in next lesson>"
    ],
    "practice_focus": "<one skill to focus on>",
    "resources": ["<optional resource>"]
  },
  "celebration": "<warm, encouraging final message>"
}
"""


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
                system_instruction=LESSON_SUMMARY_SYSTEM_PROMPT,
                temperature=0.5,  # Balanced creativity and consistency
                response_mime_type="application/json"
            )
        )
        
        # Parse JSON response
        try:
            feedback_data = json.loads(response.text)
            
            return EndLessonResponse(
                lesson_summary=LessonSummary(**feedback_data["lesson_summary"]),
                overall_feedback=feedback_data["overall_feedback"],
                strengths_and_growth=StrengthsAndGrowth(**feedback_data["strengths_and_growth"]),
                next_steps=NextSteps(**feedback_data["next_steps"]),
                celebration=feedback_data["celebration"]
            )
        except (json.JSONDecodeError, KeyError, Exception) as e:
            # Fallback if parsing fails
            raise ValueError(f"Failed to parse lesson summary: {str(e)}\nResponse: {response.text}")
