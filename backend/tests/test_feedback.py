"""Test the feedback streaming endpoint."""
import asyncio
import httpx


async def test_feedback_streaming():
    """Test SSE endpoint for real-time teacher feedback."""
    print("\n" + "="*80)
    print("TESTING: Teacher Feedback with Server-Sent Events")
    print("="*80)
    
    url = "http://localhost:8000/ask?stream_feedback=true"
    
    # Test prompt
    request_data = {
        "prompt": "What would be a parallel line to y = 2x + 3?",
        "conversation_history": [],
    }
    
    print(f"\n📝 Teacher Prompt: {request_data['prompt']}")
    print("\n" + "-"*80)
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        async with client.stream("POST", url, json=request_data) as response:
            print("\n🎓 STUDENT RESPONSES (Immediate):\n")
            
            students_received = False
            feedback_count = 0
            
            async for line in response.aiter_lines():
                if not line:
                    continue
                
                # Parse SSE format
                if line.startswith("event: "):
                    event_type = line.split("event: ")[1]
                elif line.startswith("data: "):
                    data = line.split("data: ", 1)[1]
                    
                    if event_type == "students_response":
                        import json
                        students_data = json.loads(data)
                        students_received = True
                        
                        for student in students_data['students']:
                            hand = "✋" if student.get('would_raise_hand', False) else "  "
                            response_text = student.get('response') or student.get('thinking_process', 'No response')
                            print(f"{hand} {student['student_name']}: {response_text[:100]}...")
                        
                        print(f"\n📊 {students_data['summary']}")
                        print("\n" + "-"*80)
                        print("\n💡 TEACHER FEEDBACK (Streaming):\n")
                    
                    elif event_type == "feedback_insight":
                        import json
                        insight = json.loads(data)
                        feedback_count += 1
                        
                        # Color code by severity
                        icon = "ℹ️" if insight['severity'] == 'info' else "💭" if insight['severity'] == 'suggestion' else "⚠️"
                        print(f"{icon} [{insight['category'].upper()}] {insight['message']}")
                    
                    elif event_type == "feedback_complete":
                        import json
                        complete_data = json.loads(data)
                        if complete_data.get('overall_observation'):
                            print(f"\n🎯 Overall: {complete_data['overall_observation']}")
                    
                    elif event_type == "done":
                        print("\n" + "-"*80)
                        print(f"\n✅ Stream Complete!")
                        print(f"   - Students responded: {students_received}")
                        print(f"   - Feedback insights: {feedback_count}")
                        break
                    
                    elif event_type == "error":
                        import json
                        error_data = json.loads(data)
                        print(f"\n❌ Error: {error_data['error']}")
                        break


async def test_multi_turn_feedback():
    """Test feedback with conversation history."""
    print("\n" + "="*80)
    print("TESTING: Multi-Turn Conversation with Feedback")
    print("="*80)
    
    url = "http://localhost:8000/ask?stream_feedback=true"
    
    # Second question in a sequence
    request_data = {
        "prompt": "Good! Now, why must parallel lines have the same slope?",
        "conversation_history": [
            {
                "speaker": "Teacher",
                "message": "What would be a parallel line to y = 2x + 3?"
            },
            {
                "speaker": "Alex",
                "message": "A parallel line would have the same slope but a different y-intercept, like y = 2x + 5."
            }
        ],
    }
    
    print(f"\n📝 Teacher Follow-Up: {request_data['prompt']}")
    print("   (After Alex answered about parallel lines)")
    print("\n" + "-"*80)
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        async with client.stream("POST", url, json=request_data) as response:
            feedback_received = False
            
            async for line in response.aiter_lines():
                if not line:
                    continue
                
                if line.startswith("event: "):
                    event_type = line.split("event: ")[1]
                elif line.startswith("data: "):
                    data = line.split("data: ", 1)[1]
                    
                    if event_type == "feedback_insight":
                        import json
                        insight = json.loads(data)
                        feedback_received = True
                        
                        # Focus on follow-up quality and equity
                        if insight['category'] in ['follow_up', 'equity']:
                            icon = "💭" if insight['severity'] == 'suggestion' else "ℹ️"
                            print(f"{icon} {insight['message']}")
                    
                    elif event_type == "done":
                        print("\n✅ Follow-up feedback received!")
                        break
    
    return feedback_received


if __name__ == "__main__":
    print("\n🚀 Starting Server-Sent Events Test...")
    print("   Make sure the server is running: poetry run uvicorn rehearsed_multi_student.api.main:app --reload")
    print()
    
    asyncio.run(test_feedback_streaming())
    asyncio.run(test_multi_turn_feedback())
    
    print("\n" + "="*80)
    print("✨ All SSE tests complete!")
    print("="*80 + "\n")
