"""Unit tests for lesson summary agent with Gemini API (real LLM calls).

Tests validate:
- End-of-lesson comprehensive feedback generation
- Mathematical discourse evaluation (revoicing, pressing for reasoning, connecting ideas)
- Strengths and growth areas identification
- Actionable next steps generation
- Response structure (LessonSummaryOutput schema)
"""

import pytest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from rehearsed_multi_student.agents.lesson_summary_agent import LessonSummaryAgent
from rehearsed_multi_student.models.domain import ConversationMessage
from rehearsed_multi_student.models.lesson_analyzer import LessonContext, StudentApproachOutput
from rehearsed_multi_student.models.lesson_summary_agent import EndLessonResponse


def create_lesson_context() -> LessonContext:
    """Create a lesson context for parallel lines in 8th grade algebra."""
    student_approaches = {
        "algorithmic_thinker": StudentApproachOutput(
            student_id="algorithmic_thinker",
            student_name="Vex",
            learning_style="algorithmic",
            thinking_approach="Vex thinks algorithmically - identifies slope as m=2, recognizes parallel means same slope, uses rule-based reasoning"
        ),
        "visual_thinker": StudentApproachOutput(
            student_id="visual_thinker",
            student_name="Chipper",
            learning_style="visual",
            thinking_approach="Chipper visualizes lines on graphs, understands parallelism as 'lines going the same direction', needs to see the visual"
        ),
    }
    
    return LessonContext(
        grade_level="8th grade",
        subject="Mathematics",
        topic="Linear Equations and Parallel Lines",
        learning_objectives=[
            "Understand that parallel lines have equal slopes",
            "Relate slope to parallelism geometrically",
            "Identify and create parallel lines given an equation"
        ],
        key_concepts=["slope", "parallel lines", "linear equations", "y-intercept"],
        context_summary="Students are learning about parallel lines in the coordinate plane and how slopes determine parallelism. This is foundational for understanding systems of equations.",
        mathematical_problem="We have the line y = 2x + 1. What would a parallel line look like?",
        student_approaches=student_approaches
    )


def validate_end_lesson_response(response: EndLessonResponse, test_name: str):
    """Validate that EndLessonResponse has correct structure and types."""
    print(f"\n  Validating {test_name}...")
    
    # Check lesson summary
    assert response.lesson_summary is not None, f"{test_name}: Missing lesson_summary"
    assert response.lesson_summary.total_exchanges > 0, f"{test_name}: total_exchanges should be > 0"
    assert len(response.lesson_summary.students_called_on) > 0, f"{test_name}: students_called_on empty"
    assert len(response.lesson_summary.participation_pattern) > 0, f"{test_name}: participation_pattern empty"
    assert len(response.lesson_summary.key_moments) > 0, f"{test_name}: key_moments empty"
    
    # Check overall feedback
    assert response.overall_feedback is not None, f"{test_name}: Missing overall_feedback"
    assert len(response.overall_feedback) > 50, f"{test_name}: overall_feedback too short"
    
    # Check strengths and growth
    assert response.strengths_and_growth is not None, f"{test_name}: Missing strengths_and_growth"
    assert len(response.strengths_and_growth.strengths) > 0, f"{test_name}: No strengths identified"
    assert len(response.strengths_and_growth.areas_for_growth) > 0, f"{test_name}: No growth areas identified"
    
    # Check next steps
    assert response.next_steps is not None, f"{test_name}: Missing next_steps"
    assert len(response.next_steps.immediate_actions) > 0, f"{test_name}: No immediate actions"
    assert len(response.next_steps.practice_focus) > 0, f"{test_name}: No practice focus"
    
    # Check celebration
    assert response.celebration is not None, f"{test_name}: Missing celebration"
    assert len(response.celebration) > 20, f"{test_name}: Celebration too short"
    
    print("    ✅ Structure valid")
    return True


@pytest.mark.asyncio
async def test_end_lesson_with_mathematical_discourse():
    """Test comprehensive end-of-lesson feedback focused on mathematical discourse."""
    
    print("\n" + "="*80)
    print("TEST: END-OF-LESSON FEEDBACK WITH MATHEMATICAL DISCOURSE FOCUS")
    print("="*80)
    
    agent = LessonSummaryAgent()
    lesson_context = create_lesson_context()
    
    # Create a lesson transcript with various types of discourse moves
    conversation = [
        ConversationMessage(speaker="teacher", message="We have the line y = 2x + 1. What would a parallel line look like?"),
        ConversationMessage(speaker="Vex", message="A parallel line would have the same slope, so y = 2x + 5 would work"),
        ConversationMessage(speaker="teacher", message="Good thinking! Why does changing the y-intercept keep the lines parallel?"),
        ConversationMessage(speaker="Vex", message="Because the slope stays the same - 2 in both cases"),
        ConversationMessage(speaker="teacher", message="Exactly. Can anyone describe what these two lines would look like on a graph?"),
        ConversationMessage(speaker="Chipper", message="They would go in the same direction but one is higher up"),
        ConversationMessage(speaker="teacher", message="Right! They never cross. How do you know they won't cross?"),
        ConversationMessage(speaker="Chipper", message="Because they're going the same steepness... I mean slope"),
        ConversationMessage(speaker="teacher", message="Yes! So let's connect this - Vex used the slope rule, and Chipper visualized it. Can you both see how your ideas fit together?"),
        ConversationMessage(speaker="Vex", message="Oh, so the slope being the same is WHY they're going the same direction!"),
        ConversationMessage(speaker="teacher", message="Exactly. The slope determines the direction, and parallel lines must have the same direction."),
    ]
    
    print(f"\n📚 Lesson: {lesson_context.topic}")
    print(f"📊 Problem: {lesson_context.mathematical_problem}")
    print(f"📝 Transcript: {len(conversation)} messages")
    print(f"👥 Students: {', '.join([s.student_name for s in lesson_context.student_approaches.values()])}")
    
    # Generate end-of-lesson feedback
    print("\n⏳ Generating comprehensive end-of-lesson feedback...")
    response = await agent.generate_lesson_summary(lesson_context, conversation)
    
    # Validate response
    validate_end_lesson_response(response, "discourse_focused")
    
    # Print results
    print("\n" + "="*80)
    print("📊 LESSON SUMMARY")
    print("="*80)
    print(f"Total Exchanges: {response.lesson_summary.total_exchanges}")
    print(f"Students Called On: {', '.join(response.lesson_summary.students_called_on)}")
    print(f"Participation Pattern: {response.lesson_summary.participation_pattern}")
    
    print("\n🔑 Key Moments:")
    for i, moment in enumerate(response.lesson_summary.key_moments, 1):
        print(f"  {i}. {moment}")
    
    print("\n" + "="*80)
    print("💬 OVERALL FEEDBACK (Mathematical Discourse Quality)")
    print("="*80)
    print(response.overall_feedback)
    
    print("\n" + "="*80)
    print("✅ STRENGTHS (What the teacher did well)")
    print("="*80)
    for strength in response.strengths_and_growth.strengths:
        print(f"• {strength}")
    
    print("\n" + "="*80)
    print("📈 AREAS FOR GROWTH (Mathematical Discourse Improvement)")
    print("="*80)
    for area in response.strengths_and_growth.areas_for_growth:
        print(f"• {area}")
    
    print("\n" + "="*80)
    print("🎯 NEXT STEPS (Math Talk Moves to Practice)")
    print("="*80)
    print("Immediate Actions:")
    for action in response.next_steps.immediate_actions:
        print(f"  • {action}")
    print(f"\nPractice Focus: {response.next_steps.practice_focus}")
    if response.next_steps.resources:
        print("Resources:")
        for resource in response.next_steps.resources:
            print(f"  • {resource}")
    
    print("\n" + "="*80)
    print("🎉 CELEBRATION")
    print("="*80)
    print(response.celebration)
    
    print("\n✅ Test passed - End-of-lesson feedback generated successfully!")


@pytest.mark.asyncio
async def test_end_lesson_brief_conversation():
    """Test with a shorter conversation to validate feedback generation."""
    
    print("\n" + "="*80)
    print("TEST: END-OF-LESSON FEEDBACK (BRIEF CONVERSATION)")
    print("="*80)
    
    agent = LessonSummaryAgent()
    lesson_context = create_lesson_context()
    
    # Create a shorter lesson transcript
    conversation = [
        ConversationMessage(speaker="teacher", message="What would a parallel line to y = 2x + 1 look like?"),
        ConversationMessage(speaker="Vex", message="It would have the same slope but different y-intercept"),
        ConversationMessage(speaker="teacher", message="Good! Why does the slope need to be the same?"),
        ConversationMessage(speaker="Vex", message="Because that's what makes lines parallel"),
    ]
    
    print(f"\n📚 Lesson: {lesson_context.topic}")
    print(f"📝 Transcript: {len(conversation)} messages")
    
    print("\n⏳ Generating feedback...")
    response = await agent.generate_lesson_summary(lesson_context, conversation)
    
    # Validate
    validate_end_lesson_response(response, "brief_conversation")
    
    print("\n📊 Summary:")
    print(f"  Exchanges: {response.lesson_summary.total_exchanges}")
    print(f"  Students: {', '.join(response.lesson_summary.students_called_on)}")
    print(f"  Strengths: {len(response.strengths_and_growth.strengths)}")
    print(f"  Growth Areas: {len(response.strengths_and_growth.areas_for_growth)}")
    
    print("\n💬 Overall Feedback (excerpt):")
    excerpt = response.overall_feedback[:150] + "..." if len(response.overall_feedback) > 150 else response.overall_feedback
    print(f"  {excerpt}")
    
    print("\n✅ Test passed - Brief conversation feedback generated successfully!")


if __name__ == "__main__":
    import asyncio
    print("🚀 Running Lesson Summary Agent Tests...")
    asyncio.run(test_end_lesson_with_mathematical_discourse())
    asyncio.run(test_end_lesson_brief_conversation())

