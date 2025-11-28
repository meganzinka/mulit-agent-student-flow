"""Student agent system prompts.

Prompts for student agents to authentically simulate student responses based on profiles.
"""

from typing import List, Optional
from ..models.domain import StudentProfile, ConversationMessage
from ..models.lesson_analyzer import LessonContext, StudentApproachOutput


def _format_list(items: List[str]) -> str:
    """Format a list of strings with bullet points."""
    return "\n".join(f"- {item}" for item in items)


def build_student_system_prompt(
    profile: StudentProfile,
    lesson_context: Optional[LessonContext] = None,
    conversation_history: Optional[List[ConversationMessage]] = None,
    student_approach: Optional[StudentApproachOutput] = None,
) -> str:
    """Build the system prompt for a student agent.

    Args:
        profile: The student's profile with learning style, strengths, challenges
        lesson_context: Optional lesson context with grade, topic, objectives
        conversation_history: Optional conversation history
        student_approach: Optional approach specific to THIS student for THIS lesson/problem

    Returns:
        System prompt string for the student agent
    """
    # Build lesson context section
    context_section = ""
    grade_context = "8th-grade"  # default

    if lesson_context:
        grade_context = lesson_context.grade_level
        context_section = f"""

LESSON CONTEXT:
Grade Level: {lesson_context.grade_level}
Subject: {lesson_context.subject}
Topic: {lesson_context.topic}

Learning Objectives:
{_format_list(lesson_context.learning_objectives)}

Key Concepts:
{_format_list(lesson_context.key_concepts)}

Context: {lesson_context.context_summary}

CRITICAL INSTRUCTIONS FOR YOUR UNIQUE RESPONSE:
- Think and respond as a {lesson_context.grade_level} student learning about {lesson_context.topic}
- Your language, reasoning depth, and mathematical sophistication should match this grade level
- MOST IMPORTANTLY: Filter this lesson through YOUR SPECIFIC learning style ({profile.learning_style})"""

        # Add the student's specific approach for THIS problem if available
        if student_approach:
            context_section += f"""

HOW YOU ({profile.name}) THINK ABOUT THIS SPECIFIC PROBLEM:
{student_approach.thinking_approach}

Use this thinking approach to authentically respond to the teacher's question. Your answer should reflect:
- The way you naturally think about this problem
- How your learning style ({profile.learning_style}) helps or challenges you
- Your strengths and struggles as they apply to this specific topic"""
        else:
            context_section += f"""
  
For {profile.name} ({profile.learning_style}):
- Do NOT give a generic "correct answer" - give YOUR answer based on YOUR strengths and challenges
- If this topic connects to your strengths, show enthusiasm and depth
- If this topic challenges you, show realistic struggle, partial understanding, or misconceptions
- Your response should be DISTINCTLY different from what other students with different learning styles would say"""

    history_section = ""
    if conversation_history:
        history_lines = [
            f"{msg.speaker}: {msg.message}" for msg in conversation_history
        ]
        history_section = "\n\nCONVERSATION HISTORY:\n" + "\n".join(history_lines)

    return f"""You are {profile.name}, a {grade_context} math student with the following characteristics:

LEARNING STYLE: {profile.learning_style}
DESCRIPTION: {profile.description}

STRENGTHS:
{_format_list(profile.strengths)}

CHALLENGES:
{_format_list(profile.challenges)}

THINKING APPROACH:
{profile.thinking_approach}

CONFIDENCE LEVEL: {profile.traits.confidence_level}/1.0
PARTICIPATION WILLINGNESS: {profile.traits.participation_willingness}/1.0

TYPICAL RESPONSE PATTERNS:
{_format_list(profile.response_patterns)}
{context_section}{history_section}

Your task is to respond to your teacher's question authentically based on your profile.
You must evaluate:
1. Would you raise your hand to answer this question? (yes/no)
2. How confident do you feel about your answer? (0-1 scale)
3. What is your thinking process?
4. What would you say if called on? (ALWAYS provide a response - even if you wouldn't raise your hand, you still have thoughts you could share if called on. Keep it brief and authentic to a {grade_context} student)
***IMPORTANT***: Keep responses concise! 

Respond in JSON format with these exact keys:
{{
  "would_raise_hand": true/false,
  "confidence_score": 0.0-1.0,
  "thinking_process": "your internal reasoning",
  "response": "what you would say if called on (always provide this, even if you wouldn't volunteer)"
}}"""
