"""Test the end lesson endpoint."""
import httpx
import asyncio


async def test_end_lesson():
    """Test comprehensive end-of-lesson feedback."""
    
    # Sample lesson context
    lesson_context = {
        "grade_level": "3rd grade",
        "subject": "Mathematics",
        "topic": "Fractions - Understanding Parts of a Whole",
        "learning_objectives": [
            "Students will understand that a fraction represents a part of a whole",
            "Students will identify numerator and denominator",
            "Students will create visual models for simple fractions"
        ],
        "key_concepts": [
            "Fraction",
            "Numerator",
            "Denominator",
            "Equal parts",
            "Whole"
        ],
        "context_summary": "In this 3rd grade lesson, students are introduced to fractions for the first time. At this developmental level, students need concrete visual representations to understand the concept."
    }
    
    # Sample conversation transcript
    conversation_transcript = [
        {"speaker": "Teacher", "message": "What is a fraction?"},
        {"speaker": "Chipper", "message": "A fraction is like a part of something bigger!"},
        {"speaker": "Teacher", "message": "Great! Can you give me an example?"},
        {"speaker": "Chipper", "message": "Like if you cut a pizza into 4 slices, each slice is 1/4"},
        {"speaker": "Teacher", "message": "Perfect! Now, if I cut a pizza into 4 equal pieces and eat 1 piece, what fraction did I eat?"},
        {"speaker": "Vex", "message": "One fourth! Or you could write it as 1/4."},
        {"speaker": "Teacher", "message": "Excellent! How did you know that, Vex?"},
        {"speaker": "Vex", "message": "I know the pizza was cut into 4 pieces, so the bottom number is 4. You ate 1 piece, so the top number is 1."},
        {"speaker": "Teacher", "message": "That's right! What do we call the top number and the bottom number?"},
        {"speaker": "Chipper", "message": "The top is the numerator and the bottom is the denominator!"},
    ]
    
    print("🧪 Testing END LESSON endpoint")
    print("=" * 60)
    print(f"📚 Lesson: {lesson_context['topic']}")
    print(f"📝 Transcript Length: {len(conversation_transcript)} messages")
    print()
    
    async with httpx.AsyncClient(verify=False, timeout=60.0) as client:
        response = await client.post(
            "https://rehearsed-multi-student-api-847407960490.us-central1.run.app/lesson/end",
            json={
                "lesson_context": lesson_context,
                "conversation_transcript": conversation_transcript
            }
        )
        
        if response.status_code != 200:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
            return
        
        data = response.json()
        
        print("📊 LESSON SUMMARY:")
        print(f"   Total Exchanges: {data['lesson_summary']['total_exchanges']}")
        print(f"   Students Called On: {', '.join(data['lesson_summary']['students_called_on'])}")
        print(f"   Participation Pattern: {data['lesson_summary']['participation_pattern']}")
        print()
        
        print("🔑 KEY MOMENTS:")
        for i, moment in enumerate(data['lesson_summary']['key_moments'], 1):
            print(f"   {i}. {moment}")
        print()
        
        print("💬 OVERALL FEEDBACK:")
        print(f"   {data['overall_feedback']}")
        print()
        
        print("✅ STRENGTHS:")
        for strength in data['strengths_and_growth']['strengths']:
            print(f"   • {strength}")
        print()
        
        print("📈 AREAS FOR GROWTH:")
        for area in data['strengths_and_growth']['areas_for_growth']:
            print(f"   • {area}")
        print()
        
        print("🎯 NEXT STEPS:")
        print("   Immediate Actions:")
        for action in data['next_steps']['immediate_actions']:
            print(f"      • {action}")
        print(f"   Practice Focus: {data['next_steps']['practice_focus']}")
        if data['next_steps'].get('resources'):
            print("   Resources:")
            for resource in data['next_steps']['resources']:
                print(f"      • {resource}")
        print()
        
        print("🎉 CELEBRATION:")
        print(f"   {data['celebration']}")
        print()
        
        print("✅ Test completed successfully!")


if __name__ == "__main__":
    asyncio.run(test_end_lesson())
