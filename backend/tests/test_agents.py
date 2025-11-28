"""Simple test script to verify the system works."""

import asyncio
import pytest
from pathlib import Path
from rehearsed_multi_student.profiles.loader import ProfileLoader
from rehearsed_multi_student.agents.student_agent import ParallelStudentOrchestrator
from rehearsed_multi_student.models.schemas import TeacherPromptRequest, ConversationMessage, LessonContext
from rehearsed_multi_student.services.tts_service import TextToSpeechService


# Helper function to create lesson context
def create_lesson_context():
    """Create a standard lesson context for tests."""
    return LessonContext(
        grade_level="8th grade",
        subject="Mathematics",
        topic="Linear Equations and Parallel Lines",
        learning_objectives=["Understand parallel lines", "Relate slope to parallel lines"],
        key_concepts=["slope", "parallel lines", "linear equations"],
        context_summary="Students are learning about parallel lines in the coordinate plane and how slopes determine parallelism."
    )


@pytest.mark.asyncio
async def test_single_turn():
    """Test a single teacher prompt."""
    
    print("="*60)
    print("TEST 1: SINGLE TURN")
    print("="*60)
    
    # Load profiles - correct path from tests/ to src/
    profiles_dir = Path(__file__).parent.parent / "src" / "rehearsed_multi_student" / "profiles"
    loader = ProfileLoader(profiles_dir)
    profiles = loader.load_all_profiles()
    
    print(f"\n✓ Loaded {len(profiles)} student profiles")
    for profile in profiles:
        print(f"  - {profile.name} ({profile.learning_style})")
    
    # Create orchestrator (uses ADC)
    tts_service = TextToSpeechService()
    orchestrator = ParallelStudentOrchestrator(profiles, tts_service)
    print("\n✓ Created orchestrator with TTS service (using Application Default Credentials)")
    
    # Test prompt
    request = TeacherPromptRequest(
        prompt="We have the line y = 2x + 1. What would a parallel line look like?",
        lesson_context=create_lesson_context(),
        conversation_history=[]
    )
    
    print(f"\n📝 Teacher asks: {request.prompt}")
    print("\n⏳ Processing with all students in parallel...\n")
    
    # Process in parallel
    responses = await orchestrator.process_prompt_parallel(request)
    
    # Display results
    print("=" * 60)
    for response in responses:
        hand = "✋ RAISES HAND" if response.would_raise_hand else "   (stays quiet)"
        print(f"\n{response.student_name} {hand}")
        print(f"Confidence: {response.confidence_score:.1%}")
        print(f"Thinking: {response.thinking_process[:100]}...")
        if response.response:
            print(f"Would say: \"{response.response}\"")
        print("-" * 60)
    
    # Summary
    num_raising = sum(1 for r in responses if r.would_raise_hand)
    print(f"\n✓ {num_raising} out of {len(responses)} students would participate")
    
    return orchestrator, responses


@pytest.mark.asyncio
async def test_multi_turn():
    """Test a multi-turn conversation."""
    
    print("\n\n" + "="*60)
    print("TEST 2: MULTI-TURN CONVERSATION")
    print("="*60)
    
    # Load profiles
    profiles_dir = Path(__file__).parent.parent / "src" / "rehearsed_multi_student" / "profiles"
    loader = ProfileLoader(profiles_dir)
    profiles = loader.load_all_profiles()
    print(f"\n✓ Loaded {len(profiles)} student profiles")
    for profile in profiles:
        print(f"  - {profile.name} ({profile.learning_style})")
    tts_service = TextToSpeechService()
    orchestrator = ParallelStudentOrchestrator(profiles, tts_service)
    print(f"✓ Created orchestrator with {len(orchestrator.agents)} agents")
    
    # TURN 1: Initial question
    print("\n🔄 TURN 1: Initial Question")
    print("-"*60)
    
    request1 = TeacherPromptRequest(
        prompt="We have the line y = 2x + 1. What would a parallel line look like?",
        lesson_context=create_lesson_context(),
        conversation_history=[]
    )
    
    print(f"Teacher: \"{request1.prompt}\"")
    print("\n⏳ Getting student responses...\n")
    
    responses1 = await orchestrator.process_prompt_parallel(request1)
    
    # Show who raised hands
    for response in responses1:
        if response.would_raise_hand:
            print(f"✋ {response.student_name} raises hand (confidence: {response.confidence_score:.0%})")
    
    # Teacher calls on one student (pick first one who raised hand, or first student)
    maya_response = next((r for r in responses1 if r.would_raise_hand), responses1[0])
    
    print(f"\n👨‍🏫 Teacher calls on: {maya_response.student_name}")
    print(f"💬 {maya_response.student_name}: \"{maya_response.response}\"")
    
    # TURN 2: Follow-up question
    print("\n\n🔄 TURN 2: Follow-up Question")
    print("-"*60)
    
    conversation_history = [
        ConversationMessage(
            speaker="teacher",
            message="We have the line y = 2x + 1. What would a parallel line look like?"
        ),
        ConversationMessage(
            speaker=maya_response.student_name,
            message=maya_response.response or "Parallel lines have the same slope"
        )
    ]
    
    request2 = TeacherPromptRequest(
        prompt=f"OK, so {maya_response.student_name} says that parallel lines would have the same steepness. What would happen if they didn't have the same steepness?",
        lesson_context=create_lesson_context(),
        conversation_history=conversation_history
    )
    
    print(f"Teacher: \"{request2.prompt}\"")
    print("\n⏳ Getting student responses with conversation context...\n")
    
    responses2 = await orchestrator.process_prompt_parallel(request2)
    
    # Show who raised hands for turn 2
    for response in responses2:
        if response.would_raise_hand:
            print(f"✋ {response.student_name} raises hand (confidence: {response.confidence_score:.0%})")
    
    # Pick another student
    alex_response = next(
        (r for r in responses2 if r.would_raise_hand and r.student_name != maya_response.student_name), 
        responses2[0]
    )
    
    print(f"\n👨‍🏫 Teacher calls on: {alex_response.student_name}")
    print(f"💬 {alex_response.student_name}: \"{alex_response.response}\"")
    
    # TURN 3: Another follow-up
    print("\n\n🔄 TURN 3: Deeper Follow-up")
    print("-"*60)
    
    conversation_history.append(
        ConversationMessage(
            speaker="teacher",
            message=request2.prompt
        )
    )
    conversation_history.append(
        ConversationMessage(
            speaker=alex_response.student_name,
            message=alex_response.response or "They would intersect"
        )
    )
    
    request3 = TeacherPromptRequest(
        prompt="Can someone give me a specific example of two lines that would intersect exactly once?",
        lesson_context=create_lesson_context(),
        conversation_history=conversation_history
    )
    
    print(f"Teacher: \"{request3.prompt}\"")
    print("\n⏳ Getting student responses...\n")
    
    responses3 = await orchestrator.process_prompt_parallel(request3)
    
    # Show detailed responses for turn 3
    print("RESPONSES:")
    for response in responses3:
        hand = "✋" if response.would_raise_hand else "  "
        print(f"\n{hand} {response.student_name} (confidence: {response.confidence_score:.0%})")
        if response.would_raise_hand and response.response:
            print(f"   Would say: \"{response.response}\"")
    
    num_raising = sum(1 for r in responses3 if r.would_raise_hand)
    print(f"\n✓ Turn 3 Summary: {num_raising}/{len(responses3)} students would participate")


@pytest.mark.asyncio
async def test_audio_generation():
    """Test audio generation for student responses."""
    
    print("\n\n" + "="*60)
    print("TEST 3: AUDIO GENERATION")
    print("="*60)
    
    # Load profiles
    profiles_dir = Path(__file__).parent.parent / "src" / "rehearsed_multi_student" / "profiles"
    loader = ProfileLoader(profiles_dir)
    profiles = loader.load_all_profiles()
    tts_service = TextToSpeechService()
    orchestrator = ParallelStudentOrchestrator(profiles, tts_service)
    
    print("\n✓ TTS service initialized")
    
    request = TeacherPromptRequest(
        prompt="We have the line y = 2x + 1. What would a parallel line look like?",
        lesson_context=create_lesson_context(),
        conversation_history=[]
    )
    
    print(f"\nTeacher: \"{request.prompt}\"")
    print("\n⏳ Generating responses WITH AUDIO...\n")
    
    # Get responses with audio
    responses = await orchestrator.process_prompt_parallel(request, include_audio=True)
    
    print("AUDIO GENERATION RESULTS:")
    print("="*60)
    
    # Create audio output directory
    import base64
    audio_dir = Path(__file__).parent / "audio_output"
    audio_dir.mkdir(exist_ok=True)
    
    for response in responses:
        has_audio = "✅ Audio generated" if response.audio_base64 else "❌ No audio"
        audio_size = f"({len(response.audio_base64)} chars)" if response.audio_base64 else ""
        
        print(f"\n{response.student_name}:")
        print(f"  Raises hand: {response.would_raise_hand}")
        print(f"  Confidence: {response.confidence_score:.0%}")
        print(f"  Audio: {has_audio} {audio_size}")
        if response.response:
            print(f"  Says: \"{response.response}\"")
            
            # Save audio to file
            if response.audio_base64:
                audio_file = audio_dir / f"{response.student_name.lower()}_response.mp3"
                try:
                    audio_bytes = base64.b64decode(response.audio_base64)
                    audio_file.write_bytes(audio_bytes)
                    print(f"  💾 Saved to: {audio_file}")
                    print(f"     File size: {len(audio_bytes)} bytes")
                except Exception as e:
                    print(f"  ❌ Error saving audio: {e}")
    
    # Summary
    num_with_audio = sum(1 for r in responses if r.audio_base64)
    num_with_text = sum(1 for r in responses if r.response)
    print(f"\n✓ Generated audio for {num_with_audio}/{num_with_text} text responses")
    print(f"✓ Audio files saved to: {audio_dir}")
    print(f"\n💡 To listen: open {audio_dir}")



async def main():
    """Run all tests."""
    # await test_single_turn()
    # await test_multi_turn()
    await test_audio_generation()


if __name__ == "__main__":
    asyncio.run(main())
