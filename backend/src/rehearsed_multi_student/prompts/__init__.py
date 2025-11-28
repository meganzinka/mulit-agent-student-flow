"""Prompts module for managing LLM system instructions.

This module provides centralized, version-controlled prompt management for all agents.
Prompts are separated from agent logic for easier maintenance, testing, and iteration.
"""

from .student_agent_prompts import build_student_system_prompt
from .feedback_agent_prompts import get_feedback_system_prompt
from .lesson_summary_prompts import get_lesson_summary_system_prompt
from .lesson_analyzer_prompts import get_lesson_analysis_system_prompt

__all__ = [
    "build_student_system_prompt",
    "get_feedback_system_prompt",
    "get_lesson_summary_system_prompt",
    "get_lesson_analysis_system_prompt",
]
