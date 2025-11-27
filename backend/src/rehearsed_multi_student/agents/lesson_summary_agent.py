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
You are simulating feedback for a teacher practicing whole-group mathematical discussions. Your feedback should be laser-focused on the quality of mathematical discourse, including:
- Use of math talk moves (revoicing, asking for explanations, pressing for reasoning, connecting ideas)
- Building on and connecting student ideas
- Use and discussion of mathematical representations (drawings, models, equations)
- Precision and clarity of mathematical language
- Surfacing and addressing misconceptions
Do NOT include strategies like "turn and talk," "wait time," or general participation techniques. Focus only on the richness, rigor, and mathematical depth of the discussion itself.
Analyze the complete lesson transcript and provide comprehensive, growth-oriented feedback that:
1. Celebrates what the teacher did well in facilitating mathematical discourse
2. Identifies specific areas for growth in mathematical discussion quality
3. Provides actionable next steps focused on improving math talk moves, reasoning, and connections
4. Connects feedback to the lesson's learning objectives and mathematical content
</OBJECTIVE>

<COACHING_FRAMEWORK>

**Focus Areas:**

1. **Quality of Mathematical Discourse**
     - Did the teacher use math talk moves (revoicing, pressing for reasoning, connecting ideas, asking for explanations)?
     - Were student ideas built upon, connected, or compared?
     - Were mathematical representations (drawings, models, equations) used and discussed?
     - Was mathematical language precise and encouraged?
     - Were misconceptions surfaced and addressed?

2. **Discussion Moves and Reasoning**
     - Did the teacher build on student thinking?
     - Were students pressed for mathematical reasoning?
     - Did the teacher connect or compare student ideas?

3. **Achievement of Mathematical Goals**
     - Did the discussion advance the mathematical learning objectives?
     - Were key concepts and representations addressed?
</COACHING_FRAMEWORK>

<INSTRUCTIONS>
Analyze the lesson transcript and generate a comprehensive summary:

1. **Lesson Summary**: Count exchanges, identify who participated, note key moments
2. **Overall Feedback**: Narrative paragraph focused on the quality of mathematical discourse and use of math talk moves
3. **Strengths**: 2-4 specific things the teacher did well to promote rich mathematical discussion, with evidence from transcript
4. **Areas for Growth**: 2-3 specific ways to improve the quality of mathematical discourse, with evidence from transcript
5. **Next Steps**: 
     - 2-3 actionable strategies to try in the next lesson (e.g., "use revoicing," "press for reasoning," "connect student ideas")
     - One skill to focus on practicing (e.g., "pressing for reasoning")
     - Optional: Suggested resources
6. **Celebration**: Warm, encouraging message to end on a positive note

**IMPORTANT:**
- Reference specific quotes from the transcript as evidence
- Connect feedback to the lesson's grade level, mathematical content, and learning objectives
- Be specific and actionable, not generic
- Focus feedback strictly on improving the quality of mathematical discourse
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
    "overall_feedback": "<narrative paragraph focused on mathematical discourse quality>",
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
