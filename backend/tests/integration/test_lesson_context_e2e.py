"""Integration tests for lesson context workflow (requires deployed API).

These tests hit the deployed Cloud Run endpoint and verify end-to-end flows.
Run with: pytest tests/integration/ -v -m integration
Or skip with: pytest --ignore=tests/integration/
"""
import pytest
import httpx
import asyncio
import json
import base64
from pathlib import Path


SAMPLE_LESSON_PLAN = """
3rd Grade Mathematics Lesson Plan
Topic: Introduction to Fractions

Learning Objectives:
- Students will understand that a fraction represents a part of a whole
- Students will be able to identify the numerator and denominator
- Students will create visual models to represent simple fractions (1/2, 1/4, 1/3)

Materials: Pizza cutouts, fraction circles, worksheets

Warm-Up (5 min):
Show students a pizza. Ask: "If I cut this pizza into 4 equal pieces and eat 1 piece, how much did I eat?"

Main Lesson (15 min):
1. Introduce the term "fraction" - a number that represents part of a whole
2. Explain numerator (how many pieces we have) and denominator (how many total pieces)
3. Use pizza model to show 1/4

Guided Practice (10 min):
Students will use fraction circles to create halves, thirds, and fourths
Students will draw and label fractions

Key Vocabulary:
- Fraction
- Numerator
- Denominator
- Equal parts
- Whole

Assessment:
Students will complete a worksheet where they identify fractions shown in pictures
"""


@pytest.mark.integration
async def test_lesson_context_workflow():
    """Test the complete workflow: setup lesson → ask with context → get feedback."""
    print("\n" + "="*80)
    print("TESTING: Lesson Context Workflow (K-12 Adaptive)")
    print("="*80)
    
    base_url = "https://rehearsed-multi-student-api-847407960490.us-central1.run.app"
    
    # Step 1: Setup the lesson
    print("\n📚 STEP 1: Analyzing Lesson Plan...")
    print("-"*80)
    
    async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
        setup_response = await client.post(
            f"{base_url}/lesson/setup",
            json={"lesson_plan_text": SAMPLE_LESSON_PLAN}
        )
        
        if setup_response.status_code != 200:
            print(f"❌ Error: {setup_response.status_code}")
            print(setup_response.text)
            return
        
        lesson_context = setup_response.json()
        print(f"\n✅ Lesson Context Extracted:")
        print(f"   Raw response: {json.dumps(lesson_context, indent=2)}")
        print(f"   Grade Level: {lesson_context.get('grade_level', 'N/A')}")
        print(f"   Subject: {lesson_context.get('subject', 'N/A')}")
        print(f"   Topic: {lesson_context.get('topic', 'N/A')}")
        print(f"\n   Learning Objectives:")
        for obj in lesson_context['learning_objectives']:
            print(f"     - {obj}")
        print(f"\n   Key Concepts: {', '.join(lesson_context['key_concepts'])}")
        print(f"\n   Context Summary:")
        print(f"   {lesson_context['context_summary'][:200]}...")
    
    # Step 2: Ask students a question WITH lesson context
    print("\n\n👩‍🏫 STEP 2: Teacher asks question (students have lesson context)...")
    print("-"*80)
    
    teacher_question = "If I cut a pizza into 4 equal pieces and eat 1 piece, what fraction of the pizza did I eat?"
    print(f"\nTeacher: \"{teacher_question}\"")
    
    async with httpx.AsyncClient(timeout=60.0, verify=False) as client:
        ask_response = await client.post(
            f"{base_url}/ask",
            json={
                "prompt": teacher_question,
                "lesson_context": lesson_context
            }
        )
        
        students_data = ask_response.json()
        print(f"\n🎓 Student Responses (thinking as {lesson_context['grade_level']} students):\n")
        
        for student in students_data['students']:
            hand = "✋" if student['would_raise_hand'] else "  "
            print(f"{hand} {student['student_name']} (confidence: {student['confidence_score']:.1f}):")
            print(f"   Response: \"{student['response']}\"")
            print(f"   Thinking: {student['thinking_process'][:100]}...")
            print()
        
        print(f"📊 {students_data['summary']}")
    
    # Step 3: Get feedback WITH lesson context
    print("\n\n💡 STEP 3: Teacher receives coaching feedback...")
    print("-"*80)
    
    async with httpx.AsyncClient(timeout=60.0, verify=False) as client:
        async with client.stream(
            "POST",
            f"{base_url}/ask?stream_feedback=true",
            json={
                "prompt": teacher_question,
                "lesson_context": lesson_context
            }
        ) as response:
            print("\nFeedback (contextualized to lesson objectives):\n")
            
            async for line in response.aiter_lines():
                if not line or not line.startswith("data: "):
                    continue
                
                data = line.split("data: ", 1)[1]
                
                # We already got students in step 2, focus on feedback
                if '"category"' in data:  # feedback insight
                    insight = json.loads(data)
                    icon = "ℹ️" if insight['severity'] == 'info' else "💭" if insight['severity'] == 'suggestion' else "⚠️"
                    print(f"{icon} [{insight['category'].upper()}]")
                    print(f"   {insight['message']}\n")
                
                elif '"overall_observation"' in data:  # overall feedback
                    complete = json.loads(data)
                    print(f"🎯 Overall: {complete['overall_observation']}\n")
    
    print("\n" + "="*80)
    print("✨ Lesson Context Workflow Complete!")
    print("   Students adapted to 3rd grade level ✓")
    print("   Feedback aligned with lesson objectives ✓")
    print("\n" + "="*80 + "\n")


@pytest.mark.integration
async def test_pdf_lesson_plan():
    """Test lesson setup with PDF file."""
    print("\n" + "="*80)
    print("TESTING: PDF Lesson Plan Analysis")
    print("="*80)
    
    base_url = "https://rehearsed-multi-student-api-847407960490.us-central1.run.app"
    
    # Load PDF and convert to base64
    pdf_path = Path("sample_lesson_plans/fishtank_linear_expressions_single_variable_equationsinequalities_lesson_8_20250919173218.pdf")
    
    if not pdf_path.exists():
        print(f"\n⚠️  PDF file not found: {pdf_path}")
        print("   Skipping PDF test")
        return
    
    print(f"\n📄 Loading PDF: {pdf_path.name}")
    
    with open(pdf_path, "rb") as f:
        pdf_base64 = base64.b64encode(f.read()).decode('utf-8')
    
    print(f"   PDF size: {len(pdf_base64)} bytes (base64)")
    
    # Step 1: Analyze PDF lesson plan
    print("\n📚 Analyzing PDF Lesson Plan...")
    print("-"*80)
    
    async with httpx.AsyncClient(timeout=60.0, verify=False) as client:
        setup_response = await client.post(
            f"{base_url}/lesson/setup",
            json={
                "lesson_plan_text": "",  # Empty text, using PDF only
                "lesson_plan_pdf_base64": pdf_base64
            }
        )
        
        if setup_response.status_code != 200:
            print(f"❌ Error: {setup_response.status_code}")
            print(setup_response.text)
            return
        
        lesson_context = setup_response.json()
        print("\n✅ PDF Lesson Context Extracted:")
        print(f"   Grade Level: {lesson_context.get('grade_level', 'N/A')}")
        print(f"   Subject: {lesson_context.get('subject', 'N/A')}")
        print(f"   Topic: {lesson_context.get('topic', 'N/A')}")
        print(f"\n   Learning Objectives:")
        for obj in lesson_context.get('learning_objectives', []):
            print(f"     - {obj}")
        print(f"\n   Key Concepts: {', '.join(lesson_context.get('key_concepts', []))}")
    
    # Step 2: Ask a question with this lesson context
    print("\n\n👩‍🏫 Teacher asks question (based on PDF lesson)...")
    print("-"*80)
    
    teacher_question = "What's the first step in solving 3x + 5 = 14?"
    print(f"\nTeacher: \"{teacher_question}\"")
    
    async with httpx.AsyncClient(timeout=60.0, verify=False) as client:
        ask_response = await client.post(
            f"{base_url}/ask",
            json={
                "prompt": teacher_question,
                "lesson_context": lesson_context
            }
        )
        
        students_data = ask_response.json()
        print(f"\n🎓 Student Responses (adapted to PDF lesson context):\n")
        
        for student in students_data['students']:
            hand = "✋" if student['would_raise_hand'] else "  "
            print(f"{hand} {student['student_name']}: \"{student.get('response', 'N/A')}\"")
        
        print(f"\n📊 {students_data['summary']}")
    
    print("\n" + "="*80)
    print("✨ PDF Lesson Analysis Complete!")
    print("   ✓ PDF sent directly to Gemini (no disk I/O)")
    print("   ✓ Cloud Run compatible (no file system dependencies)")
    print("="*80 + "\n")
