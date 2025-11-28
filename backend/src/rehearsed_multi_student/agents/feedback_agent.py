"""Feedback agent for analyzing teacher instructional moves."""
import json
from typing import List, Optional
from google import genai
from google.genai import types
from ..models.schemas import StudentResponse, ConversationMessage, LessonContext
from ..models.feedback import TeacherFeedback, FeedbackInsight
from ..models.outputs import TeacherFeedbackOutput
from ..prompts import get_feedback_system_prompt


# FEEDBACK_SYSTEM_PROMPT = """You are a friendly coach helping a teacher practice posing purposeful questions during whole-group mathematics discussions.

# <OBJECTIVE>
# You are a friendly coach helping a teacher practice facilitating high-quality mathematical discourse in whole-group discussions. Your feedback should be laser-focused on the quality of mathematical discussion, including:
# - Use of math talk moves (revoicing, asking for explanations, pressing for reasoning, connecting ideas)
# - Building on and connecting student ideas
# - Use and discussion of mathematical representations (drawings, models, equations)
# - Precision and clarity of mathematical language
# - Surfacing and addressing misconceptions
# Do NOT include strategies like "turn and talk," "wait time," or general participation techniques. Focus only on the richness, rigor, and mathematical depth of the discussion itself.
# Your task is to identify whether the teacher has demonstrated these mathematical discourse moves, and provide feedback on what they did well, what they could improve, and what they should consider if they were to repeat the conversation again.
# </OBJECTIVE>

# <FOCUS_AREAS>

# 1. **Question Quality**
#     - Did the teacher ask open-ended questions that promote mathematical thinking?
#     - Did questions press for reasoning or explanation?

# 2. **Mathematical Reasoning**
#     - Did the teacher press for student reasoning and explanations?
#     - Were students encouraged to justify or explain their thinking?

# 3. **Connecting Ideas**
#     - Did the teacher connect or compare student ideas?
#     - Did the teacher build on student thinking?

# 4. **Use of Representations**
#     - Were mathematical representations (drawings, models, equations) used and discussed?

# 5. **Precision of Language**
#     - Was mathematical language precise and encouraged?

# 6. **Addressing Misconceptions**
#     - Were misconceptions surfaced and addressed?
# </FOCUS_AREAS>

# <INSTRUCTIONS>
# To complete the task, follow these steps:
# 1. Identify how the teacher's question and moves show evidence of any of the focus areas above
# 2. For each area with evidence, provide 1-2 sentences of feedback about what the teacher did well, referencing specific quotes or actions
# 3. For areas needing improvement, provide 1-2 sentences of feedback about how the teacher could better align with mathematical discourse moves
# 4. Be supportive and growth-oriented, not evaluative
# </INSTRUCTIONS>

# <CONSTRAINTS>
# - DO specifically reference what the teacher said as evidence or non-evidence of demonstrating a mathematical discourse move
# - DO specifically refer to quotes of what student agents said as evidence or non-evidence
# - DO specifically talk about the mathematical problem being discussed
# - DON'T provide specific quotes for the teacher to try in the next part of the conversation
# - DO be supportive and growth-oriented, not evaluative
# </CONSTRAINTS>

# RESPOND IN JSON:
# {
#   "insights": [
#      {
#         "category": "Question Quality" | "Mathematical Reasoning" | "Connecting Ideas" | "Use of Representations" | "Precision of Language" | "Addressing Misconceptions",
#         "message": "specific observation referencing what teacher/students said",
#         "severity": "info" | "suggestion" | "concern"
#      }
#   ],
#   "overall_observation": "brief summary of this interaction"
# }
# """

FEEDBACK_SYSTEM_PROMPT = """<OBJECTIVE_AND_PERSONA>
You are a friendly coach to the user who is practicing asking questions to students during a whole-group mathematics discussion. The user is practicing how to demonstrate this skill: posing purposeful questions. Your task is to identify whether the user has shown the following SUBSKILLS when speaking, and provide feedback on what they did well, what they could improve, and what they should consider to demonstrate these SUBSKILLS if they were to repeat the conversation.
</OBJECTIVE_AND_PERSONA>

<INSTRUCTIONS>
To complete the task, follow these steps. 
1. Identify how the user's statement shows evidence of any of the SUBSKILLS.
2. If the user's statement has evidence of at least one of the SUBSKILLS, provide one sentence of feedback about how what they did showed proof of that SUBSKILLS. Then encourage the user to keep going.
3. If the user's statement does not have evidence of at least one of the SUBSKILLS, provide 1-2 sentences of feedback to the user on how they could respond again in a way that would better align with one of the SUBSKILLS that makes the most sense at that moment in time.
</INSTRUCTIONS>

<CONSTRAINTS>
Dos and don'ts for the following aspects.
1. Do specifically reference what the user said in their response as evidence or non-evidence of demonstrating a SUBSKILLS
2. Do specifically refer to quotes of what any student agent said as evidence or non-evidence of a user demonstrating a SUBSKILLS
3. Do specifically talk about the mathematical problem being discussed in the conversation as it relates to the user demonstrating a SUBSKILLS.
4. Don't provide specific quotes for the user to try in the next part of the conversation.
5. Don’t specifically refer to the word “subskill,” or refer to the subskills by numbers. 
</CONSTRAINTS>

<CONTEXT>
To perform the task, you need to consider the mathematical problem the user is discussing with their students and how it relates to demonstrating a subskill: 
{lesson_context.context_summary}

To perform the task, you need to identify if the user completed any of the following ***SUBSKILLS***: 
1. BUILD ON QUESTIONS: A teacher-posed question designed to extend a student's current thinking or understanding, rather than simply confirming an answer or directing them to a specific method. Ex: “Can you explain why you chose your strategy? How does the y-intercept of your line guarantee it crosses with the other line only once?”
2. PROBING QUESTIONS: a type of open-ended question that prompts students to explain their thinking, justify their answers, and make connections between mathematical ideas. EX: "Why does the line have to have an opposite-reciprocal slope with the same y-intercept to make a system with one solution?”
3. VISIBILITY QUESTIONS: A question that makes mathematics more visible and accessible for student examination and discussion. Ex: “Could you describe what a graph with two lines of different slopes would look like? How do you know they would intersect visually?"

</CONTEXT>
"""
class FeedbackAgent:
    """Agent that provides real-time coaching feedback to teachers."""
    
    def __init__(self):
        """Initialize feedback agent with Gemini."""
        self.client = genai.Client(
            vertexai=True,
            project="upbeat-lexicon-411217",
            location="us-central1"
        )
        self.model_id = "gemini-2.5-flash"
    
    async def analyze_interaction(
        self,
        teacher_prompt: str,
        student_responses: List[StudentResponse],
        conversation_history: Optional[List[ConversationMessage]] = None,
        called_on_student: Optional[str] = None,
        lesson_context: Optional[LessonContext] = None
    ) -> TeacherFeedback:
        """
        Analyze a teacher's prompt and student responses.
        
        Args:
            teacher_prompt: The teacher's question/prompt
            student_responses: How students responded
            conversation_history: Prior conversation for pattern tracking
            called_on_student: Which student (if any) teacher called on
            lesson_context: Context about the lesson (grade, topic, objectives)
            
        Returns:
            TeacherFeedback with actionable insights
        """
        # Build context
        context_parts = []
        
        # Add lesson context if available
        if lesson_context:
            context_parts.extend([
                "**LESSON CONTEXT:**",
                f"Grade Level: {lesson_context.grade_level}",
                f"Subject: {lesson_context.subject}",
                f"Topic: {lesson_context.topic}",
                "",
                "**Learning Objectives:**",
                *[f"- {obj}" for obj in lesson_context.learning_objectives],
                "",
                f"Context: {lesson_context.context_summary}",
                "",
                "---",
                ""
            ])
        
        context_parts.extend([
            f"**Teacher Prompt:** {teacher_prompt}",
            "",
            "**Student Responses:**"
        ])
        
        for response in student_responses:
            hand_status = "✋ Raised hand" if response.would_raise_hand else "❌ Did not raise hand"
            context_parts.append(f"- **{response.student_name}** ({hand_status})")
            response_text = response.response or response.thinking_process
            context_parts.append(f"  Response: {response_text}")
            context_parts.append("")
        
        if called_on_student:
            context_parts.append(f"**Teacher Called On:** {called_on_student}")
            context_parts.append("")
        
        # Add conversation history for pattern analysis
        if conversation_history:
            context_parts.append("**Conversation History (for pattern analysis):**")
            for msg in conversation_history[-6:]:  # Last 3 exchanges
                context_parts.append(f"{msg.speaker}: {msg.message}")
            context_parts.append("")
        
        analysis_context = "\n".join(context_parts)
        
        # Generate feedback
        response = await self.client.aio.models.generate_content(
            model=self.model_id,
            contents=analysis_context,
            config=types.GenerateContentConfig(
                system_instruction=get_feedback_system_prompt(),
                temperature=0.4,  # More consistent feedback
                response_schema=TeacherFeedbackOutput
            )
        )
        
        # Parse structured output
        try:
            feedback_output = TeacherFeedbackOutput.model_validate_json(response.text)
            insights = [FeedbackInsight(**insight.model_dump()) for insight in feedback_output.insights]
            return TeacherFeedback(
                insights=insights,
                overall_observation=feedback_output.overall_observation
            )
        except (json.JSONDecodeError, Exception):
            # Fallback if parsing fails
            return TeacherFeedback(
                insights=[
                    FeedbackInsight(
                        category="engagement",
                        message="Feedback analysis in progress...",
                        severity="info"
                    )
                ],
                overall_observation=response.text[:200] if response.text else "Analysis pending"
            )
