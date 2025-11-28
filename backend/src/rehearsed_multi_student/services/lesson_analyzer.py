"""Service for analyzing lesson plans and extracting structured context.

The LessonAnalyzer calls Gemini ONCE to generate:
1. Core lesson information
2. How each student profile would approach this problem
3. Subskills/success criteria for this problem

All of this is returned in a single LessonContext that is then passed to
student agents, feedback agents, and lesson summary agents.
"""

import json
import asyncio
from typing import List
from google import genai
from google.genai import types

from ..models.lesson_analyzer import LessonSetupRequest, LessonContext
from ..models.lesson_analyzer.outputs import LessonAnalysisOutput
from ..models.domain import StudentProfile
from ..prompts import get_lesson_analysis_system_prompt


class LessonAnalyzer:
    """Analyzes lesson plans and extracts context with student approaches."""

    def __init__(self):
        """Initialize with Gemini client."""
        self.client = genai.Client(
            vertexai=True, project="upbeat-lexicon-411217", location="us-central1"
        )
        self.model_id = "gemini-2.5-flash"

    async def analyze_lesson_plan(
        self,
        request: LessonSetupRequest,
        student_profiles: List[StudentProfile],
    ) -> LessonContext:
        """
        Analyze a lesson plan once and extract full context including student approaches.

        Calls Gemini once with:
        - The lesson plan
        - All student profiles

        Returns a LessonContext with:
        - Core lesson info
        - How each student would approach
        - Subskills for this problem

        Args:
            request: Lesson plan input (text and/or PDF)
            student_profiles: List of student profiles to include approaches for

        Returns:
            LessonContext with lesson info and student approaches indexed by ID
        """
        # Build content for Gemini
        content_parts = []

        # Add lesson plan text
        if request.lesson_plan_text:
            content_parts.append(
                types.Part(text=f"Lesson Plan:\n\n{request.lesson_plan_text}")
            )

        # Add PDF if provided
        if request.lesson_plan_pdf_base64:
            content_parts.append(
                types.Part(
                    inline_data=types.Blob(
                        mime_type="application/pdf",
                        data=request.lesson_plan_pdf_base64,
                    )
                )
            )

        if not content_parts:
            raise ValueError(
                "Must provide either lesson_plan_text or lesson_plan_pdf_base64"
            )

        # Build system prompt that includes all student profiles
        system_prompt = self._build_analysis_prompt(student_profiles)

        # Call Gemini once with structured output
        response = await asyncio.to_thread(
            self.client.models.generate_content,
            model=self.model_id,
            contents=content_parts,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.3,
                response_mime_type="application/json",
            ),
        )

        # Parse the response
        try:
            result = json.loads(response.text)
            analysis_output = LessonAnalysisOutput(**result)

            # Convert to LessonContext with student approaches indexed by ID
            student_approaches = {
                approach.student_id: approach
                for approach in analysis_output.student_approaches
            }

            return LessonContext(
                grade_level=analysis_output.grade_level,
                subject=analysis_output.subject,
                topic=analysis_output.topic,
                learning_objectives=analysis_output.learning_objectives,
                key_concepts=analysis_output.key_concepts,
                context_summary=analysis_output.context_summary,
                mathematical_problem=analysis_output.mathematical_problem,
                student_approaches=student_approaches,
            )
        except (json.JSONDecodeError, Exception) as e:
            # Fallback response
            print(f"Error parsing lesson analysis: {e}")
            return LessonContext(
                grade_level="Unknown",
                subject="Mathematics",
                topic="General Discussion",
                learning_objectives=["Practice mathematical reasoning"],
                key_concepts=["Problem solving"],
                context_summary=f"Lesson context could not be fully extracted: {str(e)}",
                student_approaches={},
            )

    def _build_analysis_prompt(self, student_profiles: List[StudentProfile]) -> str:
        """Build system prompt that includes all student profiles.

        Pulls the base prompt dynamically and appends student profile context.

        Args:
            student_profiles: List of student profiles to analyze approaches for

        Returns:
            System prompt string with base prompt + student profiles
        """
        base_prompt = get_lesson_analysis_system_prompt()
        profiles_text = self._format_student_profiles(student_profiles)

        return f"""{base_prompt}

STUDENT PROFILES TO ANALYZE:
{profiles_text}"""

    def _format_student_profiles(self, student_profiles: List[StudentProfile]) -> str:
        """Format student profiles into a readable text block for the prompt.

        Args:
            student_profiles: List of student profiles to format

        Returns:
            Formatted string with all student profile details
        """
        return "\n".join(
            [
                f"""STUDENT PROFILE: {profile.name}
- ID: {profile.id}
- Learning Style: {profile.learning_style}
- Description: {profile.description}
- Thinking Approach: {profile.thinking_approach}
- Strengths: {', '.join(profile.strengths)}
- Challenges: {', '.join(profile.challenges)}"""
                for profile in student_profiles
            ]
        )
