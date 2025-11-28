"""Student agent implementation using Google GenAI."""

import asyncio
import os
from typing import List, Optional
from google import genai
from google.genai import types

from rehearsed_multi_student.models.schemas import (
    StudentProfile,
    StudentResponse,
    TeacherPromptRequest,
    ConversationMessage,
    LessonContext,
)
from ..prompts import build_student_system_prompt


class StudentAgent:
    """An AI agent representing a single student with a specific profile."""

    def __init__(
        self, profile: StudentProfile, model_name: str = "gemini-2.5-flash-lite"
    ):
        """Initialize a student agent.

        Args:
            profile: The student's profile
            model_name: The Gemini model to use (default: gemini-2.5-flash-lite)
        """
        self.profile = profile
        # Use Vertex AI with Application Default Credentials
        project = os.getenv("GOOGLE_CLOUD_PROJECT", "upbeat-lexicon-411217")
        self.client = genai.Client(
            vertexai=True, project=project, location="us-central1"
        )
        self.model_name = model_name

    def _build_system_prompt(
        self,
        lesson_context: Optional[LessonContext] = None,
        conversation_history: Optional[List[ConversationMessage]] = None,
    ) -> str:
        """Build the system prompt for this student agent.

        Args:
            lesson_context: Optional lesson context with grade, topic, objectives
            conversation_history: Optional conversation history

        Returns:
            System prompt string
        """
        return build_student_system_prompt(
            self.profile, lesson_context, conversation_history
        )

    async def process_prompt(self, request: TeacherPromptRequest) -> StudentResponse:
        """Process a teacher's prompt and generate student response.

        Args:
            request: The teacher's prompt request

        Returns:
            StudentResponse with decision and potential answer
        """
        system_prompt = self._build_system_prompt(
            request.lesson_context, request.conversation_history
        )

        try:
            # Call Gemini API
            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model=self.model_name,
                contents=request.prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.7,
                    response_mime_type="application/json",
                ),
            )

            # Parse response
            import json

            result = json.loads(response.text)

            return StudentResponse(
                student_id=self.profile.id,
                student_name=self.profile.name,
                would_raise_hand=result.get("would_raise_hand", False),
                confidence_score=result.get("confidence_score", 0.0),
                thinking_process=result.get("thinking_process", ""),
                response=result.get("response"),
            )

        except Exception as e:
            # Fallback response in case of error
            print(f"Error processing prompt for {self.profile.name}: {e}")
            return StudentResponse(
                student_id=self.profile.id,
                student_name=self.profile.name,
                would_raise_hand=False,
                confidence_score=0.0,
                thinking_process=f"Error occurred: {str(e)}",
                response=None,
            )


class ParallelStudentOrchestrator:
    """Orchestrates multiple student agents processing prompts in parallel."""

    def __init__(self, profiles: List[StudentProfile], tts_service=None):
        """Initialize the orchestrator with student profiles.

        Args:
            profiles: List of student profiles
            tts_service: Optional TextToSpeechService for audio generation
        """
        self.agents = [StudentAgent(profile) for profile in profiles]
        self.profiles = {profile.id: profile for profile in profiles}
        self.tts_service = tts_service

    async def process_prompt_parallel(
        self, request: TeacherPromptRequest, include_audio: bool = False
    ) -> List[StudentResponse]:
        """Process a prompt with all student agents in parallel.

        Args:
            request: The teacher's prompt request
            include_audio: Whether to generate audio for responses

        Returns:
            List of student responses (with audio if include_audio=True)
        """
        # Get text responses in parallel
        tasks = [agent.process_prompt(request) for agent in self.agents]
        responses = await asyncio.gather(*tasks)

        # Generate audio in parallel if requested
        if include_audio and self.tts_service:
            audio_tasks = []
            for response in responses:
                if response.response:  # Only generate audio if there's text
                    profile = self.profiles[response.student_id]
                    audio_tasks.append(
                        self.tts_service.synthesize_speech(
                            response.response, profile.voice_settings
                        )
                    )
                else:
                    audio_tasks.append(asyncio.sleep(0, result=None))

            audio_results = await asyncio.gather(*audio_tasks)

            # Attach audio to responses
            for response, audio_base64 in zip(responses, audio_results):
                response.audio_base64 = audio_base64

        return list(responses)
