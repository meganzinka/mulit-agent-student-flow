"""FastAPI application for the multi-student agent system."""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pathlib import Path
import json
import asyncio
import os
import logging
import sys
from datetime import datetime
import time

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


# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

def setup_logging():
    """Configure structured logging for the application."""
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    
    # Create formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(console_handler)
    
    # Application logger
    app_logger = logging.getLogger("rehearsed_multi_student")
    app_logger.setLevel(log_level)
    
    return app_logger

logger = setup_logging()


# ============================================================================
# FASTAPI APP INITIALIZATION
# ============================================================================

app = FastAPI(
    title="Rehearsed Multi-Student API",
    description="Parallel student agent system for teacher training",
    version="0.1.0",
    root_path="/api"
)


# ============================================================================
# CORS CONFIGURATION
# ============================================================================

def get_cors_config():
    """
    Get CORS configuration supporting both static and dynamic origins.
    
    Supports Fly.dev dynamic preview URLs with regex pattern matching.
    """
    # Use regex pattern to match Fly.dev preview URLs and other allowed domains
    cors_regex = os.getenv(
        "CORS_ORIGIN_REGEX",
        r"https://([a-f0-9]+-[a-f0-9]+\.fly\.dev|"
        r"multi-agent-frontend-847407960490\.us-central1\.run\.app|"
        r"builder\.io|cdn\.builder\.io)"
    )
    
    logger.info(f"CORS configuration - Origin regex: {cors_regex}")
    
    return {
        "allow_origin_regex": cors_regex,
        "allow_credentials": True,
        "allow_methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"],
        "expose_headers": ["Content-Length", "X-Request-ID"],
        "max_age": 600,
    }

# Add CORS middleware
app.add_middleware(CORSMiddleware, **get_cors_config())


# ============================================================================
# REQUEST LOGGING MIDDLEWARE
# ============================================================================

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests and responses with timing."""
    request_id = f"{int(time.time() * 1000)}"
    start_time = time.time()
    
    # Log incoming request
    logger.info(
        f"[{request_id}] {request.method} {request.url.path} "
        f"- Origin: {request.headers.get('origin', 'N/A')}"
    )
    
    try:
        response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Log response
        logger.info(
            f"[{request_id}] {request.method} {request.url.path} "
            f"- Status: {response.status_code} - Duration: {duration:.3f}s"
        )
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        return response
        
    except Exception as e:
        duration = time.time() - start_time
        logger.error(
            f"[{request_id}] {request.method} {request.url.path} "
            f"- Error: {str(e)} - Duration: {duration:.3f}s",
            exc_info=True
        )
        raise


# ============================================================================
# SERVICE INITIALIZATION
# ============================================================================

# Initialize profile loader
profiles_dir = Path(__file__).parent.parent / "profiles"
profile_loader = ProfileLoader(profiles_dir)

# Load all student profiles on startup
logger.info("Loading student profiles...")
profiles = profile_loader.load_all_profiles()
logger.info(f"Loaded {len(profiles)} student profiles")

# Initialize services
logger.info("Initializing services...")
tts_service = TextToSpeechService()
feedback_agent = FeedbackAgent()
lesson_summary_agent = LessonSummaryAgent()
lesson_analyzer = LessonAnalyzer()
orchestrator = ParallelStudentOrchestrator(profiles, tts_service)
logger.info("All services initialized successfully")


# ============================================================================
# ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """Health check endpoint."""
    logger.debug("Health check requested")
    return {
        "status": "ok",
        "message": "Rehearsed Multi-Student API is running",
        "students_loaded": len(profiles),
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/students")
async def list_students():
    """List all available student profiles."""
    logger.info(f"Student list requested - returning {len(profiles)} profiles")
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
    logger.info(f"Processing /ask request - Prompt: {request.prompt[:100]}... - Stream feedback: {stream_feedback}")
    
    try:
        # Process prompt with all agents in parallel (text only)
        logger.debug("Starting parallel student processing (text only)")
        student_responses = await orchestrator.process_prompt_parallel(
            request, include_audio=False
        )
        logger.info(f"Student responses generated - {len(student_responses)} students processed")
        
        # Generate summary
        num_raising_hands = sum(1 for r in student_responses if r.would_raise_hand)
        summary = (
            f"{num_raising_hands} out of {len(student_responses)} students "
            f"would raise their hand to answer this question."
        )
        logger.debug(f"Summary: {summary}")
        
        students_data = MultiStudentResponse(
            students=student_responses,
            summary=summary,
        )
        
        # If not streaming feedback, return JSON immediately
        if not stream_feedback:
            logger.info("Returning JSON response (no streaming)")
            return students_data
        
        # Stream feedback via SSE
        logger.info("Starting SSE stream with feedback")
        async def event_stream():
            try:
                # Send student responses immediately
                yield f"event: students_response\n"
                yield f"data: {students_data.model_dump_json()}\n\n"
                await asyncio.sleep(0.1)
                logger.debug("Student responses sent via SSE")
                
                # Generate and stream feedback
                logger.debug("Generating teacher feedback")
                feedback = await feedback_agent.analyze_teacher_move(
                    latest_teacher_statement=request.prompt,
                    student_responses=student_responses,
                    conversation_history=request.conversation_history,
                    lesson_context=request.lesson_context,
                )
                logger.debug("Teacher feedback generated")
                
                # Send teacher feedback
                yield f"event: teacher_feedback\n"
                yield f"data: {feedback.model_dump_json()}\n\n"
                await asyncio.sleep(0.05)
                logger.debug("Teacher feedback sent via SSE")
                
                yield f"event: done\n"
                yield f"data: {{}}\n\n"
                logger.info("SSE stream completed successfully")
            except Exception as e:
                logger.error(f"Error in SSE stream: {str(e)}", exc_info=True)
                yield f"event: error\n"
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
        
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
        logger.error(f"Error in /ask endpoint: {str(e)}", exc_info=True)
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
    logger.info(f"Processing /ask/with-audio request - Prompt: {request.prompt[:100]}... - Stream feedback: {stream_feedback}")
    
    try:
        # Process prompt with all agents in parallel (with audio)
        logger.debug("Starting parallel student processing (with audio)")
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
        logger.info(f"Audio responses generated - {num_with_audio}/{len(student_responses)} with audio")
        
        students_data = MultiStudentResponse(
            students=student_responses,
            summary=summary,
        )
        
        # If not streaming feedback, return JSON immediately
        if not stream_feedback:
            logger.info("Returning JSON response with audio (no streaming)")
            return students_data
        
        # Stream feedback via SSE
        logger.info("Starting SSE stream with audio and feedback")
        async def event_stream():
            try:
                # Send student responses immediately
                yield f"event: students_response\n"
                yield f"data: {students_data.model_dump_json()}\n\n"
                await asyncio.sleep(0.1)
                logger.debug("Student responses with audio sent via SSE")
                
                # Generate and stream feedback
                logger.debug("Generating teacher feedback")
                feedback = await feedback_agent.analyze_teacher_move(
                    latest_teacher_statement=request.prompt,
                    student_responses=student_responses,
                    conversation_history=request.conversation_history,
                    lesson_context=request.lesson_context,
                )
                logger.debug("Teacher feedback generated")
                
                # Send teacher feedback
                yield f"event: teacher_feedback\n"
                yield f"data: {feedback.model_dump_json()}\n\n"
                await asyncio.sleep(0.05)
                logger.debug("Teacher feedback sent via SSE")
                
                yield f"event: done\n"
                yield f"data: {{}}\n\n"
                logger.info("SSE stream with audio completed successfully")
            except Exception as e:
                logger.error(f"Error in SSE stream (with audio): {str(e)}", exc_info=True)
                yield f"event: error\n"
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
        
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
        logger.error(f"Error in /ask/with-audio endpoint: {str(e)}", exc_info=True)
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
    logger.info(f"Processing /ask/with-feedback request - Prompt: {request.prompt[:100]}...")
    
    async def event_stream():
        try:
            # Step 1: Generate student responses immediately (non-blocking)
            logger.debug("Generating student responses")
            student_responses = await orchestrator.process_prompt_parallel(
                request, include_audio=request.include_audio if hasattr(request, 'include_audio') else False
            )
            logger.info(f"Student responses generated - {len(student_responses)} students")
            
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
            logger.debug("Student responses sent to client")
            
            # Small delay to ensure frontend receives student data first
            await asyncio.sleep(0.1)
            
            # Step 2: Generate feedback in background (streaming)
            logger.debug("Generating teacher feedback")
            feedback = await feedback_agent.analyze_teacher_move(
                latest_teacher_statement=request.prompt,
                student_responses=student_responses,
                conversation_history=request.conversation_history,
                lesson_context=request.lesson_context,
            )
            logger.debug("Teacher feedback generated")
            
            # Send teacher feedback
            yield f"event: teacher_feedback\n"
            yield f"data: {feedback.model_dump_json()}\n\n"
            await asyncio.sleep(0.05)
            logger.debug("Teacher feedback sent to client")
            
            # Signal completion
            yield f"event: done\n"
            yield f"data: {{}}\n\n"
            logger.info("SSE stream with feedback completed successfully")
            
        except Exception as e:
            logger.error(f"Error in /ask/with-feedback stream: {str(e)}", exc_info=True)
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
    logger.info("Processing /lesson/setup request")
    
    try:
        logger.debug(f"Analyzing lesson plan (length: {len(request.lesson_plan_text)} chars)")
        student_profiles = profiles
        lesson_context = await lesson_analyzer.analyze_lesson_plan(request, student_profiles)
        logger.info(f"Lesson analysis complete - Topic: {lesson_context.topic}, Grade: {lesson_context.grade_level}")
        return lesson_context
    except Exception as e:
        logger.error(f"Error in /lesson/setup endpoint: {str(e)}", exc_info=True)
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
    logger.info(f"Processing /lesson/end request - Transcript length: {len(request.conversation_transcript)} exchanges")
    
    try:
        logger.debug("Generating comprehensive lesson summary")
        summary = await lesson_summary_agent.generate_lesson_summary(
            lesson_context=request.lesson_context,
            conversation_transcript=request.conversation_transcript
        )
        logger.info("Lesson summary generated successfully")
        return summary
    except Exception as e:
        logger.error(f"Error in /lesson/end endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# STARTUP/SHUTDOWN EVENTS
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Log application startup."""
    logger.info("=" * 80)
    logger.info("Rehearsed Multi-Student API - Starting Up")
    logger.info("=" * 80)
    logger.info(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")
    logger.info(f"Log Level: {os.getenv('LOG_LEVEL', 'INFO')}")
    logger.info(f"Students Loaded: {len(profiles)}")
    logger.info("=" * 80)


@app.on_event("shutdown")
async def shutdown_event():
    """Log application shutdown."""
    logger.info("Rehearsed Multi-Student API - Shutting Down")


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level=os.getenv("LOG_LEVEL", "info").lower()
    )