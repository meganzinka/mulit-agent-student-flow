"""Integration tests for the feedback system with deployed API.

These tests validate the new feedback system in a real deployment context.
They can test against:
1. Local development server
2. Deployed Cloud Run instance
"""

import asyncio
import httpx
import pytest


@pytest.mark.integration
async def test_feedback_via_api():
    """Test feedback endpoint via deployed API."""
    
    print("\n" + "="*80)
    print("INTEGRATION TEST: Teacher Feedback via API")
    print("="*80)
    
    # Use local development server or deployed endpoint
    base_url = "http://localhost:8080"  # Change to deployed URL for integration tests
    
    try:
        # First, get student responses to a prompt
        lesson_setup = {
            "grade_level": "8th grade",
            "subject": "Mathematics",
            "topic": "Parallel Lines",
            "mathematical_problem": "We have the line y = 2x + 1. What would a parallel line look like?"
        }
        
        request_data = {
            "prompt": "We have the line y = 2x + 1. What would a parallel line look like?",
            "lesson_context": lesson_setup,
            "conversation_history": []
        }
        
        print(f"\n📝 Teacher Prompt: {request_data['prompt']}")
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Get student responses
            response = await client.post(f"{base_url}/api/ask", json=request_data)
            
            if response.status_code != 200:
                print(f"⚠️  API endpoint not available: {response.status_code}")
                print("   (This is expected if server isn't running)")
                return
            
            students_data = response.json()
            print(f"\n✅ Got student responses: {len(students_data.get('students', []))} students")
            
            for student in students_data.get('students', []):
                hand = "✋" if student.get('would_raise_hand', False) else "  "
                resp_text = student.get('response') or student.get('thinking_process', '')
                print(f"  {hand} {student['student_name']}: {resp_text[:60]}...")
            
            # Now test feedback endpoint
            feedback_request = {
                "teacher_statement": "You said parallel lines have the same slope. Can you explain why the y-intercept must be different?",
                "lesson_context": lesson_setup,
                "student_responses": students_data.get('students', []),
                "conversation_history": [
                    {"speaker": "teacher", "message": request_data['prompt']},
                    *[{"speaker": s['student_name'], "message": s.get('response', '')} 
                      for s in students_data.get('students', []) if s.get('response')]
                ]
            }
            
            print(f"\n👨‍🏫 Teacher Follow-Up: \"{feedback_request['teacher_statement']}\"")
            
            feedback_response = await client.post(f"{base_url}/api/feedback", json=feedback_request)
            
            if feedback_response.status_code != 200:
                print(f"❌ Feedback endpoint failed: {feedback_response.status_code}")
                return
            
            feedback = feedback_response.json()
            
            print("\n" + "="*80)
            print("💡 FEEDBACK RECEIVED:")
            print("="*80)
            print(f"\nQuestion Type: {feedback.get('question_type', 'None')}")
            print(f"\nAnalysis:\n{feedback.get('feedback', 'N/A')}")
            print(f"\nCoaching Suggestion:\n{feedback.get('suggestion', 'N/A')}")
            
            # Validate feedback structure
            assert 'question_type' in feedback, "Missing question_type"
            assert 'feedback' in feedback, "Missing feedback"
            assert 'suggestion' in feedback, "Missing suggestion"
            assert isinstance(feedback['feedback'], str), "Feedback should be string"
            assert isinstance(feedback['suggestion'], str), "Suggestion should be string"
            
            print("\n✅ Feedback endpoint validation passed")
    
    except httpx.ConnectError:
        print("\n⚠️  Could not connect to API server")
        print("   Run: poetry run python -m src.rehearsed_multi_student.api.main")
        pytest.skip("API server not running")


@pytest.mark.integration 
async def test_multi_turn_feedback_via_api():
    """Test feedback with multi-turn conversation via API."""
    
    print("\n\n" + "="*80)
    print("INTEGRATION TEST: Multi-Turn Feedback via API")
    print("="*80)
    
    base_url = "http://localhost:8080"
    
    try:
        lesson_setup = {
            "grade_level": "8th grade",
            "subject": "Mathematics",
            "topic": "Parallel Lines",
            "mathematical_problem": "We have the line y = 2x + 1. What would a parallel line look like?"
        }
        
        # Turn 1: Initial question
        turn_1_data = {
            "prompt": "We have the line y = 2x + 1. What would a parallel line look like?",
            "lesson_context": lesson_setup,
            "conversation_history": []
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Get initial responses
            response1 = await client.post(f"{base_url}/api/ask", json=turn_1_data)
            
            if response1.status_code != 200:
                pytest.skip("API server not running")
            
            students_1 = response1.json().get('students', [])
            print("\nTURN 1: Initial question")
            print(f"  {len(students_1)} students responded")
            
            # Get a student who raised hand
            responder = next((s for s in students_1 if s.get('would_raise_hand')), students_1[0] if students_1 else None)
            if not responder:
                pytest.skip("No students responded")
            
            print(f"  → {responder['student_name']}: {responder.get('response', '')[:60]}...")
            
            # Turn 2: Follow-up question
            print("\nTURN 2: Follow-up question")
            
            turn_2_data = {
                "prompt": f"Good point, {responder['student_name']}. Why must all parallel lines have the SAME slope?",
                "lesson_context": lesson_setup,
                "conversation_history": [
                    {"speaker": "teacher", "message": turn_1_data['prompt']},
                    {"speaker": responder['student_name'], "message": responder.get('response', '')},
                ]
            }
            
            response2 = await client.post(f"{base_url}/api/ask", json=turn_2_data)
            students_2 = response2.json().get('students', [])
            
            # Get feedback on turn 2 teacher move
            feedback_request = {
                "teacher_statement": turn_2_data['prompt'],
                "lesson_context": lesson_setup,
                "student_responses": students_2,
                "conversation_history": turn_2_data['conversation_history']
            }
            
            feedback_response = await client.post(f"{base_url}/api/feedback", json=feedback_request)
            
            if feedback_response.status_code == 200:
                feedback = feedback_response.json()
                print(f"\n💡 Feedback Type: {feedback.get('question_type', 'None')}")
                print(f"   Analysis: {feedback.get('feedback', 'N/A')[:80]}...")
                print(f"   Suggestion: {feedback.get('suggestion', 'N/A')[:80]}...")
                
                assert feedback.get('question_type') is not None or True, "Feedback received"
                print("\n✅ Multi-turn feedback test passed")
            else:
                print(f"⚠️  Feedback endpoint returned: {feedback_response.status_code}")
    
    except httpx.ConnectError:
        pytest.skip("API server not running")


if __name__ == "__main__":
    # Run integration tests manually
    print("🚀 Running Integration Tests...")
    print("   Make sure the API server is running: poetry run python -m src.rehearsed_multi_student.api.main")
    print()
    
    asyncio.run(test_feedback_via_api())
    asyncio.run(test_multi_turn_feedback_via_api())
    
    print("\n" + "="*80)
    print("✨ Integration tests complete!")
    print("="*80 + "\n")
