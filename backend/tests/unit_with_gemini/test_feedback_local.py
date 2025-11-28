"""Test the feedback agent with local Gemini API (not server-sent events).

Tests the new feedback system that provides:
- question_type: Classification of question (build_on, probing, visibility, or None)
- feedback: Analysis grounded in the specific math problem and student responses
- suggestion: Actionable coaching tip
"""

import pytest
from pathlib import Path
from src.rehearsed_multi_student.profiles.loader import ProfileLoader
from src.rehearsed_multi_student.agents.student_agent import ParallelStudentOrchestrator
from src.rehearsed_multi_student.agents.feedback_agent import FeedbackAgent
from src.rehearsed_multi_student.models.student_agent import TeacherPromptRequest
from src.rehearsed_multi_student.models.lesson_analyzer import LessonContext, StudentApproachOutput
from src.rehearsed_multi_student.services.tts_service import TextToSpeechService


def create_lesson_context_with_approaches():
    """Create lesson context with student approaches for testing."""
    student_approaches = {
        "algorithmic_thinker": StudentApproachOutput(
            student_id="algorithmic_thinker",
            student_name="Vex",
            learning_style="algorithmic",
            thinking_approach="Vex approaches this systematically: identifying slope m=2, then recognizing parallel lines need same slope. For y=2x+1, they think: y=2x+b where b≠1."
        ),
        "visual_thinker": StudentApproachOutput(
            student_id="visual_thinker",
            student_name="Chipper",
            learning_style="visual",
            thinking_approach="Chipper visualizes the line on a coordinate plane with slope 2. They mentally draw parallel lines all going at the same angle, understanding that shifting up/down keeps them parallel."
        ),
        "struggling_learner": StudentApproachOutput(
            student_id="struggling_learner",
            student_name="Riven",
            learning_style="struggling",
            thinking_approach="Riven recalls 'parallel lines go the same direction' but struggles with precision. Needs scaffolding about steepness. May confuse slope/y-intercept but can identify similar patterns."
        ),
    }
    
    return LessonContext(
        grade_level="8th grade",
        subject="Mathematics",
        topic="Linear Equations and Parallel Lines",
        learning_objectives=["Understand parallel lines", "Relate slope to parallelism"],
        key_concepts=["slope", "parallel lines", "linear equations"],
        context_summary="Students learning about parallel lines in the coordinate plane and how slopes determine parallelism.",
        mathematical_problem="We have the line y = 2x + 1. What would a parallel line look like?",
        student_approaches=student_approaches
    )


@pytest.mark.asyncio
async def test_feedback_on_build_on_question():
    """Test feedback when teacher asks a build-on question."""
    
    print("\n" + "="*80)
    print("TEST 1: FEEDBACK ON BUILD-ON QUESTION")
    print("="*80)
    
    # Load profiles and create orchestrator
    profiles_dir = Path(__file__).parent.parent / "src" / "rehearsed_multi_student" / "profiles"
    loader = ProfileLoader(profiles_dir)
    profiles = loader.load_all_profiles()
    
    orchestrator = ParallelStudentOrchestrator(profiles, TextToSpeechService())
    feedback_agent = FeedbackAgent()
    lesson_context = create_lesson_context_with_approaches()
    
    print(f"\n📚 Problem: {lesson_context.mathematical_problem}")
    
    # Get initial student responses
    request = TeacherPromptRequest(
        prompt="We have the line y = 2x + 1. What would a parallel line look like?",
        lesson_context=lesson_context,
        conversation_history=[]
    )
    
    responses = await orchestrator.process_prompt_parallel(request)
    
    print("\n👨‍🏫 Initial teacher prompt asked")
    for r in responses:
        if r.would_raise_hand:
            print(f"  ✋ {r.student_name} responded")
    
    # Teacher follows up with a BUILD ON question
    teacher_statement = "Vex, you said parallel lines have the same slope. Can you explain WHY the y-intercept doesn't have to be the same?"
    
    print(f"\n👨‍🏫 Teacher Follow-Up: \"{teacher_statement}\"")
    print("   (This is a BUILD ON question - asking for explanation/reasoning)")
    
    # Get feedback on this teacher move
    feedback = await feedback_agent.analyze_teacher_move(
        latest_teacher_statement=teacher_statement,
        student_responses=responses,
        lesson_context=lesson_context
    )
    
    print("\n" + "="*80)
    print("💡 FEEDBACK:")
    print("="*80)
    print(f"\nQuestion Type: {feedback.question_type or 'None identified'}")
    print(f"\nAnalysis:\n{feedback.feedback}")
    print(f"\nCoaching Suggestion:\n{feedback.suggestion}")
    
    # Validate the feedback
    assert feedback.feedback is not None, "Feedback should not be empty"
    assert feedback.suggestion is not None, "Suggestion should not be empty"
    assert feedback.question_type in ["build_on", "probing", "visibility", None], f"Invalid question type: {feedback.question_type}"
    print("\n✅ Feedback validation passed")


@pytest.mark.asyncio
async def test_feedback_on_probing_question():
    """Test feedback when teacher asks a probing question."""
    
    print("\n\n" + "="*80)
    print("TEST 2: FEEDBACK ON PROBING QUESTION")
    print("="*80)
    
    profiles_dir = Path(__file__).parent.parent / "src" / "rehearsed_multi_student" / "profiles"
    loader = ProfileLoader(profiles_dir)
    profiles = loader.load_all_profiles()
    
    orchestrator = ParallelStudentOrchestrator(profiles, TextToSpeechService())
    feedback_agent = FeedbackAgent()
    lesson_context = create_lesson_context_with_approaches()
    
    # Get student responses to initial prompt
    request = TeacherPromptRequest(
        prompt="We have the line y = 2x + 1. What would a parallel line look like?",
        lesson_context=lesson_context,
        conversation_history=[]
    )
    
    responses = await orchestrator.process_prompt_parallel(request)
    
    # Teacher asks a PROBING question
    teacher_statement = "Why does the line have to have a slope of 2? What would happen if we used a different slope like 3?"
    
    print(f"\n👨‍🏫 Teacher Question: \"{teacher_statement}\"")
    print("   (This is a PROBING question - asking for explanation and connections)")
    
    feedback = await feedback_agent.analyze_teacher_move(
        latest_teacher_statement=teacher_statement,
        student_responses=responses,
        lesson_context=lesson_context
    )
    
    print("\n" + "="*80)
    print("💡 FEEDBACK:")
    print("="*80)
    print(f"\nQuestion Type: {feedback.question_type or 'None identified'}")
    print(f"\nAnalysis:\n{feedback.feedback}")
    print(f"\nCoaching Suggestion:\n{feedback.suggestion}")
    
    assert feedback.feedback is not None
    assert feedback.suggestion is not None
    print("\n✅ Feedback validation passed")


@pytest.mark.asyncio
async def test_feedback_on_visibility_question():
    """Test feedback when teacher asks a visibility question."""
    
    print("\n\n" + "="*80)
    print("TEST 3: FEEDBACK ON VISIBILITY QUESTION")
    print("="*80)
    
    profiles_dir = Path(__file__).parent.parent / "src" / "rehearsed_multi_student" / "profiles"
    loader = ProfileLoader(profiles_dir)
    profiles = loader.load_all_profiles()
    
    orchestrator = ParallelStudentOrchestrator(profiles, TextToSpeechService())
    feedback_agent = FeedbackAgent()
    lesson_context = create_lesson_context_with_approaches()
    
    # Get student responses
    request = TeacherPromptRequest(
        prompt="We have the line y = 2x + 1. What would a parallel line look like?",
        lesson_context=lesson_context,
        conversation_history=[]
    )
    
    responses = await orchestrator.process_prompt_parallel(request)
    
    # Teacher asks a VISIBILITY question
    teacher_statement = "Can someone describe what two parallel lines would look like on a coordinate grid? How would you know just by looking at them that they're parallel?"
    
    print(f"\n👨‍🏫 Teacher Question: \"{teacher_statement}\"")
    print("   (This is a VISIBILITY question - making math visual and accessible)")
    
    feedback = await feedback_agent.analyze_teacher_move(
        latest_teacher_statement=teacher_statement,
        student_responses=responses,
        lesson_context=lesson_context
    )
    
    print("\n" + "="*80)
    print("💡 FEEDBACK:")
    print("="*80)
    print(f"\nQuestion Type: {feedback.question_type or 'None identified'}")
    print(f"\nAnalysis:\n{feedback.feedback}")
    print(f"\nCoaching Suggestion:\n{feedback.suggestion}")
    
    assert feedback.feedback is not None
    assert feedback.suggestion is not None
    print("\n✅ Feedback validation passed")


@pytest.mark.asyncio
async def test_feedback_on_weak_move():
    """Test feedback when teacher makes a weak pedagogical move."""
    
    print("\n\n" + "="*80)
    print("TEST 4: FEEDBACK ON WEAK PEDAGOGICAL MOVE")
    print("="*80)
    
    profiles_dir = Path(__file__).parent.parent / "src" / "rehearsed_multi_student" / "profiles"
    loader = ProfileLoader(profiles_dir)
    profiles = loader.load_all_profiles()
    
    orchestrator = ParallelStudentOrchestrator(profiles, TextToSpeechService())
    feedback_agent = FeedbackAgent()
    lesson_context = create_lesson_context_with_approaches()
    
    # Get student responses
    request = TeacherPromptRequest(
        prompt="We have the line y = 2x + 1. What would a parallel line look like?",
        lesson_context=lesson_context,
        conversation_history=[]
    )
    
    responses = await orchestrator.process_prompt_parallel(request)
    
    # Teacher makes a WEAK move - just confirming, not probing
    teacher_statement = "Okay, so parallel lines have the same slope. Good."
    
    print(f"\n👨‍🏫 Teacher Statement: \"{teacher_statement}\"")
    print("   (This is a weak move - just confirming, not building on thinking)")
    
    feedback = await feedback_agent.analyze_teacher_move(
        latest_teacher_statement=teacher_statement,
        student_responses=responses,
        lesson_context=lesson_context
    )
    
    print("\n" + "="*80)
    print("💡 FEEDBACK:")
    print("="*80)
    print(f"\nQuestion Type: {feedback.question_type or 'None identified'}")
    print(f"\nAnalysis:\n{feedback.feedback}")
    print(f"\nCoaching Suggestion:\n{feedback.suggestion}")
    
    # On a weak move, we should get None for question_type and coaching about improvement
    assert feedback.question_type is None, "Weak moves should have None question_type"
    assert "consider" in feedback.suggestion.lower() or "could" in feedback.suggestion.lower(), \
        "Suggestion should recommend improvement"
    print("\n✅ Feedback validation passed - correctly identified weak move")


@pytest.mark.asyncio
async def test_feedback_with_conversation_history():
    """Test feedback considering prior conversation context."""
    
    print("\n\n" + "="*80)
    print("TEST 5: FEEDBACK WITH CONVERSATION HISTORY")
    print("="*80)
    
    profiles_dir = Path(__file__).parent.parent / "src" / "rehearsed_multi_student" / "profiles"
    loader = ProfileLoader(profiles_dir)
    profiles = loader.load_all_profiles()
    
    orchestrator = ParallelStudentOrchestrator(profiles, TextToSpeechService())
    feedback_agent = FeedbackAgent()
    lesson_context = create_lesson_context_with_approaches()
    
    from src.rehearsed_multi_student.models.domain import ConversationMessage
    
    # Simulate a multi-turn conversation
    conversation_history = [
        ConversationMessage(speaker="teacher", message="We have the line y = 2x + 1. What would a parallel line look like?"),
        ConversationMessage(speaker="Vex", message="A parallel line would need the same slope, so y = 2x + 5 would work."),
        ConversationMessage(speaker="teacher", message="Good thinking! Why does the y-intercept change but the slope stays the same?"),
        ConversationMessage(speaker="Vex", message="Because moving the line up or down doesn't change how steep it is."),
    ]
    
    print("\n📋 Conversation so far:")
    for msg in conversation_history:
        print(f"   {msg.speaker}: {msg.message}")
    
    # Get new responses
    request = TeacherPromptRequest(
        prompt="So what would you call two lines with the same slope but different y-intercepts?",
        lesson_context=lesson_context,
        conversation_history=conversation_history
    )
    
    responses = await orchestrator.process_prompt_parallel(request)
    
    print(f"\n👨‍🏫 New Teacher Question: \"{request.prompt}\"")
    
    feedback = await feedback_agent.analyze_teacher_move(
        latest_teacher_statement=request.prompt,
        student_responses=responses,
        conversation_history=conversation_history,
        lesson_context=lesson_context
    )
    
    print("\n" + "="*80)
    print("💡 FEEDBACK (considering prior conversation):")
    print("="*80)
    print(f"\nQuestion Type: {feedback.question_type or 'None identified'}")
    print(f"\nAnalysis:\n{feedback.feedback}")
    print(f"\nCoaching Suggestion:\n{feedback.suggestion}")
    
    assert feedback.feedback is not None
    print("\n✅ Feedback considers conversation history")
