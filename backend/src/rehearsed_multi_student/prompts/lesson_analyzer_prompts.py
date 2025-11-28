"""Lesson analyzer system prompts.

Prompts for analyzing lesson plans and extracting structured context.
"""


def get_lesson_analysis_system_prompt() -> str:
    """Get the lesson plan analysis system prompt.

    This prompt guides the lesson analyzer to extract structured information from lesson plans:
    - Grade level identification
    - Subject and topic extraction
    - Learning objectives and key concepts
    - Context summary for AI agents

    Returns:
        System prompt string for lesson plan analysis
    """
    return """You are an educational content analyzer. Extract structured information from the lesson plan.

Your task:
1. Identify the grade level (if not explicit, infer from content complexity)
2. Identify the subject and specific topic
3. Extract learning objectives (what students should learn)
4. List key concepts and vocabulary
5. Write a brief context summary that will help AI agents understand how students at THIS grade level would think about THIS topic

Be specific about grade level - this determines how students will respond!"""
