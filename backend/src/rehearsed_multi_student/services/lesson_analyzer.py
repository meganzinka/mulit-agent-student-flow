"""Service for analyzing lesson plans and extracting structured context."""
import json
from google import genai
from google.genai import types
from ..models.schemas import LessonContext, LessonSetupRequest
from ..models.outputs import LessonAnalysisOutput
from ..prompts import get_lesson_analysis_system_prompt


class LessonAnalyzer:
    """Analyzes lesson plans and extracts context for student agents."""
    
    def __init__(self):
        """Initialize with Gemini client."""
        self.client = genai.Client(
            vertexai=True,
            project="upbeat-lexicon-411217",
            location="us-central1"
        )
        self.model_id = "gemini-2.5-flash"
    
    async def analyze_lesson_plan(self, request: LessonSetupRequest) -> LessonContext:
        """
        Analyze a lesson plan and extract structured context.
        
        Supports both text and PDF inputs. PDFs are sent directly to Gemini
        via the Part class (no disk I/O, cloud-ready).
        
        Args:
            request: Lesson plan text and/or base64-encoded PDF
            
        Returns:
            LessonContext with grade level, objectives, key concepts, etc.
        """
        # Build content for Gemini
        content_parts = []
        
        # Add text if provided
        if request.lesson_plan_text:
            content_parts.append(types.Part(text=f"Lesson Plan:\n\n{request.lesson_plan_text}"))
        
        # Add PDF if provided (as inline data - no file I/O!)
        if request.lesson_plan_pdf_base64:
            content_parts.append(
                types.Part(
                    inline_data=types.Blob(
                        mime_type="application/pdf",
                        data=request.lesson_plan_pdf_base64  # Base64 string from frontend
                    )
                )
            )
        
        if not content_parts:
            raise ValueError("Must provide either lesson_plan_text or lesson_plan_pdf_base64")
        
        # Generate structured analysis
        response = await self.client.aio.models.generate_content(
            model=self.model_id,
            contents=content_parts,
            config=types.GenerateContentConfig(
                system_instruction=get_lesson_analysis_system_prompt(),
                temperature=0.3,  # Consistent extraction
                response_schema=LessonAnalysisOutput
            )
        )
        
        # Parse structured output
        try:
            lesson_output = LessonAnalysisOutput.model_validate_json(response.text)
            return LessonContext(**lesson_output.model_dump())
        except (json.JSONDecodeError, Exception) as e:
            # Fallback if parsing fails
            return LessonContext(
                grade_level="Unknown",
                subject="Mathematics",
                topic="General Discussion",
                learning_objectives=["Practice mathematical reasoning"],
                key_concepts=["Problem solving"],
                context_summary=f"Lesson context could not be fully extracted: {str(e)}"
            )
