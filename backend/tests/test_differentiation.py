"""Quick test to see differentiated student responses for algebra lesson."""
import asyncio
import httpx
import json


async def test_differentiation():
    """Test that students give different responses based on their learning styles."""
    
    # High school algebra lesson (should challenge struggling learner, favor algorithmic)
    algebra_lesson = {
        "grade_level": "9th grade",
        "subject": "Algebra 1",
        "topic": "Linear Expressions & Single-Variable Equations with Unit Conversions",
        "learning_objectives": [
            "Write and solve equations to represent contextual situations where estimations and unit conversions are required",
            "Define variables and units from a contextual situation",
            "Rearrange equations used to model a relationship to highlight a quantity of interest"
        ],
        "key_concepts": [
            "Linear Expressions",
            "Single-Variable Equations",
            "Unit Conversions",
            "Mathematical Modeling"
        ],
        "context_summary": "9th grade algebra students learning to model real-world situations with equations and solve them systematically"
    }
    
    # 3rd grade fractions lesson (should favor visual, challenge algorithmic with concepts)
    fractions_lesson = {
        "grade_level": "3rd grade",
        "subject": "Mathematics",
        "topic": "Introduction to Fractions - Understanding Parts of a Whole",
        "learning_objectives": [
            "Students will understand that a fraction represents a part of a whole",
            "Students will create visual models to represent simple fractions"
        ],
        "key_concepts": [
            "Fraction",
            "Numerator",
            "Denominator",
            "Equal parts",
            "Visual models"
        ],
        "context_summary": "3rd graders learning fractions through concrete visual models like pizza slices"
    }
    
    base_url = "https://rehearsed-multi-student-api-847407960490.us-central1.run.app"
    
    print("\n" + "="*80)
    print("TEST 1: ALGEBRA LESSON (Should favor Vex, challenge Riven)")
    print("="*80)
    
    async with httpx.AsyncClient(timeout=60.0, verify=False) as client:
        response = await client.post(
            f"{base_url}/ask",
            json={
                "prompt": "A car travels at 60 miles per hour. Write an equation to find how many feet per second that is. (Hint: 1 mile = 5280 feet)",
                "lesson_context": algebra_lesson
            }
        )
        
        data = response.json()
        print("\n🎓 Student Responses:\n")
        
        for student in data['students']:
            hand = "✋" if student['would_raise_hand'] else "  "
            print(f"{hand} {student['student_name']} (confidence: {student['confidence_score']:.1f})")
            print(f"   Says: \"{student['response']}\"")
            print(f"   Thinking: {student['thinking_process'][:150]}...")
            print()
    
    print("\n" + "="*80)
    print("TEST 2: FRACTIONS LESSON (Should favor Chipper, still accessible to all)")
    print("="*80)
    
    async with httpx.AsyncClient(timeout=60.0, verify=False) as client:
        response = await client.post(
            f"{base_url}/ask",
            json={
                "prompt": "If I have a chocolate bar with 8 equal pieces and I eat 3 pieces, what fraction did I eat?",
                "lesson_context": fractions_lesson
            }
        )
        
        data = response.json()
        print("\n🎓 Student Responses:\n")
        
        for student in data['students']:
            hand = "✋" if student['would_raise_hand'] else "  "
            print(f"{hand} {student['student_name']} (confidence: {student['confidence_score']:.1f})")
            print(f"   Says: \"{student['response']}\"")
            print(f"   Thinking: {student['thinking_process'][:150]}...")
            print()


if __name__ == "__main__":
    asyncio.run(test_differentiation())
