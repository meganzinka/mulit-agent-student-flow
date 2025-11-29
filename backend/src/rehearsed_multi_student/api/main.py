"""FastAPI application for the multi-student agent system."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pathlib import Path
import json
import asyncio
import os

from rehearsed_multi_student.models.student_agent import (
    TeacherPromptRequest,
    MultiStudentResponse,
)
from rehearsed_multi_student.models.lesson_analyzer import (
    LessonSetupRequest,
    LessonContext,
)
from rehearsed_multi_student.models.lesson_summary_agent import (
    EndLessonRequest,
    EndLessonResponse,
)
from rehearsed_multi_student.profiles.loader import ProfileLoader
from rehearsed_multi_student.agents.student_agent import ParallelStudentOrchestrator
from rehearsed_multi_student.agents.feedback_agent import FeedbackAgent
from rehearsed_multi_student.agents.lesson_summary_agent import LessonSummaryAgent
from rehearsed_multi_student.services.tts_service import TextToSpeechService
from rehearsed_multi_student.services.lesson_analyzer import LessonAnalyzer


app = FastAPI(
    title="Rehearsed Multi-Student API",
    description="Parallel student agent system for teacher training",
    version="0.1.0",
    root_path="/api"
)

def get_allowed_origins():
    """Get allowed CORS origins."""
    # Default allowed origins
    default_origins = ",".join([
        "https://multi-agent-frontend-847407960490.us-central1.run.app",  # Production frontend
        "https://builder.io",  # Builder.io editor
        "https://cdn.builder.io",  # Builder.io CDN
    ])
    
    origins_str = os.getenv("ALLOWED_ORIGINS", default_origins)
    return [origin. strip() for origin in origins_str.split(",")]

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
    max_age=600,
)

# Initialize profile loader
profiles_dir = Path(__file__).parent.parent / "profiles"
profile_loader = ProfileLoader(profiles_dir)

# Load all student profiles on startup
profiles = profile_loader.load_all_profiles()

# Initialize TTS service
tts_service = TextToSpeechService()

# Initialize feedback agent
feedback_agent = FeedbackAgent()

# Initialize lesson summary agent
lesson_summary_agent = LessonSummaryAgent()

# Initialize lesson analyzer
lesson_analyzer = LessonAnalyzer()

# Initialize orchestrator (uses ADC, no API key needed)
orchestrator = ParallelStudentOrchestrator(profiles, tts_service)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "ok",
        "message": "Rehearsed Multi-Student API is running",
        "students_loaded": len(profiles),
    }


@app.get("/students")
async def list_students():
    """List all available student profiles."""
    return {
        "students": [
            {
                "id": p.id,
                "name": p.name,
                "learning_style": p.learning_style,
                "description": p.description,
            }
            for p in profiles
        ]
    }


@app.post("/ask")
async def ask_students(request: TeacherPromptRequest, stream_feedback: bool = False):
    """
    Send a prompt to all student agents and get their TEXT responses.
    
    The agents process the prompt in parallel and determine:
    - Whether each student would raise their hand
    - Their confidence level
    - Their thinking process
    - What they would say (if anything)
    
    Args:
        request: Teacher prompt and conversation history
        stream_feedback: If True, streams teacher feedback via SSE after student responses
    
    Returns:
        - If stream_feedback=False: JSON with student responses
        - If stream_feedback=True: SSE stream with students first, then feedback
    """
    try:
        # Process prompt with all agents in parallel (text only)
        student_responses = await orchestrator.process_prompt_parallel(
            request, include_audio=False
        )
        
        # Generate summary
        num_raising_hands = sum(1 for r in student_responses if r.would_raise_hand)
        summary = (
            f"{num_raising_hands} out of {len(student_responses)} students "
            f"would raise their hand to answer this question."
        )
        
        students_data = MultiStudentResponse(
            students=student_responses,
            summary=summary,
        )
        
        # If not streaming feedback, return JSON immediately
        if not stream_feedback:
            return students_data
        
        # Stream feedback via SSE
        async def event_stream():
            # Send student responses immediately
            yield f"event: students_response\n"
            yield f"data: {students_data.model_dump_json()}\n\n"
            await asyncio.sleep(0.1)
            
            # Generate and stream feedback
            feedback = await feedback_agent.analyze_teacher_move(
                latest_teacher_statement=request.prompt,
                student_responses=student_responses,
                conversation_history=request.conversation_history,
                lesson_context=request.lesson_context,
            )
            
            # Send teacher feedback
            yield f"event: teacher_feedback\n"
            yield f"data: {feedback.model_dump_json()}\n\n"
            await asyncio.sleep(0.05)
            
            yield f"event: done\n"
            yield f"data: {{}}\n\n"
        
        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ask/with-audio")
async def ask_students_with_audio(request: TeacherPromptRequest, stream_feedback: bool = False):
    """
    Send a prompt to all student agents and get their responses WITH AUDIO.
    
    The agents process the prompt in parallel and determine:
    - Whether each student would raise their hand
    - Their confidence level
    - Their thinking process
    - What they would say (if anything)
    - Audio (base64-encoded MP3) of what they would say
    
    Args:
        request: Teacher prompt and conversation history
        stream_feedback: If True, streams teacher feedback via SSE after student responses
    
    Returns:
        - If stream_feedback=False: JSON with student responses and audio
        - If stream_feedback=True: SSE stream with students+audio first, then feedback
    """
    try:
        # Process prompt with all agents in parallel (with audio)
        student_responses = await orchestrator.process_prompt_parallel(
            request, include_audio=True
        )
        
        # Generate summary
        num_raising_hands = sum(1 for r in student_responses if r.would_raise_hand)
        num_with_audio = sum(1 for r in student_responses if r.audio_base64)
        summary = (
            f"{num_raising_hands} out of {len(student_responses)} students "
            f"would raise their hand. Audio generated for {num_with_audio} responses."
        )
        
        students_data = MultiStudentResponse(
            students=student_responses,
            summary=summary,
        )
        
        # If not streaming feedback, return JSON immediately
        if not stream_feedback:
            return students_data
        
        # Stream feedback via SSE
        async def event_stream():
            # Send student responses immediately
            yield f"event: students_response\n"
            yield f"data: {students_data.model_dump_json()}\n\n"
            await asyncio.sleep(0.1)
            
            # Generate and stream feedback
            feedback = await feedback_agent.analyze_teacher_move(
                latest_teacher_statement=request.prompt,
                student_responses=student_responses,
                conversation_history=request.conversation_history,
                lesson_context=request.lesson_context,
            )
            
            # Send teacher feedback
            yield f"event: teacher_feedback\n"
            yield f"data: {feedback.model_dump_json()}\n\n"
            await asyncio.sleep(0.05)
            
            yield f"event: done\n"
            yield f"data: {{}}\n\n"
        
        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ask/with-feedback")
async def ask_students_with_feedback(request: TeacherPromptRequest):
    """
    Send a prompt to all student agents and stream back:
    1. IMMEDIATE: Student responses (text + audio if requested)
    2. STREAMING: Real-time teacher feedback via SSE
    
    This endpoint uses Server-Sent Events to deliver feedback WITHOUT blocking
    the student response flow. The frontend receives student answers instantly,
    then gets coaching feedback as it's generated.
    
    SSE Format:
    - event: students_response
      data: {students: [...], summary: "..."}
    
    - event: feedback_chunk
      data: {insight: {...}, progress: "analyzing..."}
    
    - event: feedback_complete
      data: {overall_observation: "..."}
    
    - event: done
      data: {}
    """
    async def event_stream():
        try:
            # Step 1: Generate student responses immediately (non-blocking)
            student_responses = await orchestrator.process_prompt_parallel(
                request, include_audio=request.include_audio if hasattr(request, 'include_audio') else False
            )
            
            # Send student responses immediately
            num_raising_hands = sum(1 for r in student_responses if r.would_raise_hand)
            summary = (
                f"{num_raising_hands} out of {len(student_responses)} students "
                f"would raise their hand to answer."
            )
            
            students_data = MultiStudentResponse(
                students=student_responses,
                summary=summary,
            )
            
            yield f"event: students_response\n"
            yield f"data: {students_data.model_dump_json()}\n\n"
            
            # Small delay to ensure frontend receives student data first
            await asyncio.sleep(0.1)
            
            # Step 2: Generate feedback in background (streaming)
            # Analyze the teacher's move
            feedback = await feedback_agent.analyze_teacher_move(
                latest_teacher_statement=request.prompt,
                student_responses=student_responses,
                conversation_history=request.conversation_history,
                lesson_context=request.lesson_context,
            )
            
            # Send teacher feedback
            yield f"event: teacher_feedback\n"
            yield f"data: {feedback.model_dump_json()}\n\n"
            await asyncio.sleep(0.05)
            
            # Signal completion
            yield f"event: done\n"
            yield f"data: {{}}\n\n"
            
        except Exception as e:
            # Send error event
            yield f"event: error\n"
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
    )


@app.post("/lesson/setup", response_model=LessonContext)
async def setup_lesson(request: LessonSetupRequest):
    """
    Analyze a lesson plan and extract structured context.
    
    Takes a lesson plan (text or PDF) and uses AI to extract:
    - Grade level
    - Subject and topic
    - Learning objectives
    - Key concepts/vocabulary
    - Context summary for student agents
    
    The frontend should store this LessonContext and include it
    in subsequent /ask requests so student agents and feedback
    can adapt to the specific lesson.
    
    Example:
        POST /lesson/setup
        {
          "lesson_plan_text": "3rd Grade Math - Today we're learning..."
        }
        
        Returns:
        {
          "grade_level": "3rd grade",
          "subject": "Mathematics",
          "topic": "Fractions - Adding Unlike Denominators",
          "learning_objectives": [...],
          "key_concepts": [...],
          "context_summary": "..."
        }
    """
    try:
        student_profiles = profiles
        lesson_context = await lesson_analyzer.analyze_lesson_plan(request, student_profiles)
        return lesson_context
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/lesson/end", response_model=EndLessonResponse)
async def end_lesson(request: EndLessonRequest):
    """
    End a lesson and receive comprehensive feedback.
    
    Analyzes the complete lesson transcript and provides:
    - Summary of what happened (participation patterns, key moments)
    - Overall narrative feedback
    - Specific strengths with evidence from transcript
    - Areas for growth with evidence from transcript
    - Actionable next steps for improvement
    - Celebration message
    
    The frontend should call this when the teacher is ready to end
    the practice session and review their performance.
    
    Example:
        POST /lesson/end
        {
          "lesson_context": {
            "grade_level": "3rd grade",
            "subject": "Mathematics",
            "topic": "Fractions",
            "learning_objectives": [...],
            "key_concepts": [...],
            "context_summary": "..."
          },
          "conversation_transcript": [
            {"speaker": "Teacher", "message": "What is a fraction?"},
            {"speaker": "Chipper", "message": "A fraction is..."},
            ...
          ]
        }
        
        Returns:
        {
          "lesson_summary": {
            "total_exchanges": 8,
            "students_called_on": ["Chipper", "Vex"],
            "participation_pattern": "...",
            "key_moments": [...]
          },
          "overall_feedback": "...",
          "strengths_and_growth": {
            "strengths": [...],
            "areas_for_growth": [...]
          },
          "next_steps": {
            "immediate_actions": [...],
            "practice_focus": "...",
            "resources": [...]
          },
          "celebration": "..."
        }
    """
    try:
        summary = await lesson_summary_agent.generate_lesson_summary(
            lesson_context=request.lesson_context,
            conversation_transcript=request.conversation_transcript
        )
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
