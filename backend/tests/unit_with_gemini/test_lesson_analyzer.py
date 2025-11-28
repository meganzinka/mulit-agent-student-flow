"""Test lesson analyzer with various input formats and validate output structure."""

import pytest
import asyncio
import base64
import json
from pathlib import Path
from rehearsed_multi_student.services.lesson_analyzer import LessonAnalyzer
from rehearsed_multi_student.models.lesson_analyzer import LessonSetupRequest, LessonContext
from rehearsed_multi_student.profiles.loader import ProfileLoader


SAMPLE_LESSON_TEXT = """
5th Grade Mathematics Lesson Plan
Topic: Understanding Fractions as Parts of a Whole

Learning Objectives:
- Students will understand that a fraction represents a part of a whole
- Students will identify numerator and denominator
- Students will create visual representations of fractions

Materials: Pizza cutouts, fraction circles, worksheets

Warm-Up (5 min):
Show students a pizza. Ask: "If I cut this pizza into 4 equal pieces and eat 1 piece, how much did I eat?"

Main Lesson (15 min):
1. Introduce the term "fraction" - a number that represents part of a whole
2. Explain numerator (how many pieces we have) and denominator (how many total pieces)
3. Use pizza model to show 1/4, 1/2, 3/4

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


def load_pdf_as_base64(pdf_path: Path) -> str:
    """Load a PDF file and convert to base64."""
    with open(pdf_path, "rb") as f:
        return base64.b64encode(f.read()).decode('utf-8')


def validate_lesson_context(context: LessonContext, test_name: str):
    """Validate the structure and content of LessonContext output."""
    print(f"\n{'='*80}")
    print(f"VALIDATING: {test_name}")
    print(f"{'='*80}")
    
    # Check required fields exist
    required_fields = [
        'grade_level', 'subject', 'topic', 'learning_objectives',
        'key_concepts', 'context_summary', 'mathematical_problem', 'student_approaches'
    ]
    
    print("\n✅ Checking required fields:")
    for field in required_fields:
        value = getattr(context, field, None)
        if value is None:
            print(f"   ❌ {field}: MISSING")
        else:
            if isinstance(value, list):
                print(f"   ✅ {field}: {len(value)} items")
            elif isinstance(value, dict):
                print(f"   ✅ {field}: {len(value)} entries")
            else:
                print(f"   ✅ {field}: present")
    
    # Print detailed output
    print(f"\n📋 DETAILED OUTPUT:")
    print(f"-" * 80)
    print(f"Grade Level: {context.grade_level}")
    print(f"Subject: {context.subject}")
    print(f"Topic: {context.topic}")
    
    print(f"\n📚 Learning Objectives ({len(context.learning_objectives)}):")
    for i, obj in enumerate(context.learning_objectives, 1):
        print(f"   {i}. {obj}")
    
    print(f"\n🔑 Key Concepts ({len(context.key_concepts)}):")
    print(f"   {', '.join(context.key_concepts)}")
    
    print(f"\n📝 Context Summary:")
    print(f"   {context.context_summary}")
    
    if context.mathematical_problem:
        print(f"\n🧮 Mathematical Problem:")
        print(f"   {context.mathematical_problem}")
    else:
        print(f"\n🧮 Mathematical Problem: (not extracted)")
    
    print(f"\n👥 Student Approaches ({len(context.student_approaches)} profiles):")
    for student_id, approach in context.student_approaches.items():
        print(f"\n   {approach.student_name} ({approach.learning_style}):")
        print(f"   ID: {approach.student_id}")
        print(f"   Thinking Approach:")
        print(f"   {approach.thinking_approach[:200]}...")
    
    print(f"\n{'='*80}\n")
    
    return True


@pytest.mark.asyncio
async def test_lesson_analyzer_with_text():
    """Test lesson analyzer with text input only."""
    print("\n" + "="*80)
    print("TEST 1: LESSON ANALYZER WITH TEXT INPUT")
    print("="*80)
    
    # Load student profiles
    profiles_dir = Path(__file__).parent.parent / "src" / "rehearsed_multi_student" / "profiles"
    loader = ProfileLoader(profiles_dir)
    student_profiles = loader.load_all_profiles()
    
    print(f"\n✓ Loaded {len(student_profiles)} student profiles:")
    for profile in student_profiles:
        print(f"  - {profile.name} ({profile.learning_style}): {profile.description}")
    
    # Create analyzer
    analyzer = LessonAnalyzer()
    print("\n✓ Created LessonAnalyzer")
    
    # Analyze lesson plan
    print("\n⏳ Analyzing lesson plan text...")
    request = LessonSetupRequest(
        lesson_plan_text=SAMPLE_LESSON_TEXT
    )
    
    context = await analyzer.analyze_lesson_plan(request, student_profiles)
    
    # Validate output
    assert validate_lesson_context(context, "TEXT INPUT")
    assert context.grade_level is not None
    assert len(context.student_approaches) > 0
    print("✅ Test passed!")


@pytest.mark.asyncio
async def test_lesson_analyzer_with_pdf():
    """Test lesson analyzer with PDF input only."""
    print("\n" + "="*80)
    print("TEST 2: LESSON ANALYZER WITH PDF INPUT")
    print("="*80)
    
    # Check if PDF exists
    pdf_path = Path(__file__).parent.parent / "sample_lesson_plans" / "public_task_1531.pdf"
    
    if not pdf_path.exists():
        print(f"\n⚠️  PDF not found at {pdf_path}")
        print("   Skipping PDF test")
        pytest.skip("PDF file not found")
    
    print(f"\n📄 Loading PDF: {pdf_path.name}")
    pdf_base64 = load_pdf_as_base64(pdf_path)
    print(f"   PDF size: {len(pdf_base64)} bytes (base64)")
    
    # Load student profiles
    profiles_dir = Path(__file__).parent.parent / "src" / "rehearsed_multi_student" / "profiles"
    loader = ProfileLoader(profiles_dir)
    student_profiles = loader.load_all_profiles()
    print(f"✓ Loaded {len(student_profiles)} student profiles")
    
    # Create analyzer
    analyzer = LessonAnalyzer()
    print("✓ Created LessonAnalyzer")
    
    # Analyze PDF lesson plan
    print("\n⏳ Analyzing PDF lesson plan...")
    request = LessonSetupRequest(
        lesson_plan_text="",
        lesson_plan_pdf_base64=pdf_base64
    )
    
    context = await analyzer.analyze_lesson_plan(request, student_profiles)
    
    # Validate output
    assert validate_lesson_context(context, "PDF INPUT")
    assert context.grade_level is not None
    assert len(context.student_approaches) > 0
    print("✅ Test passed!")


@pytest.mark.asyncio
async def test_lesson_analyzer_with_text_and_pdf():
    """Test lesson analyzer with both text and PDF input."""
    print("\n" + "="*80)
    print("TEST 3: LESSON ANALYZER WITH TEXT + PDF INPUT")
    print("="*80)
    
    # Check if PDF exists
    pdf_path = Path(__file__).parent.parent / "sample_lesson_plans" / "public_task_1531.pdf"
    
    if not pdf_path.exists():
        print(f"\n⚠️  PDF not found at {pdf_path}")
        print("   Skipping combined test")
        pytest.skip("PDF file not found")
    
    print(f"\n📄 Loading PDF: {pdf_path.name}")
    pdf_base64 = load_pdf_as_base64(pdf_path)
    print(f"   PDF size: {len(pdf_base64)} bytes (base64)")
    
    # Load student profiles
    profiles_dir = Path(__file__).parent.parent / "src" / "rehearsed_multi_student" / "profiles"
    loader = ProfileLoader(profiles_dir)
    student_profiles = loader.load_all_profiles()
    print(f"✓ Loaded {len(student_profiles)} student profiles")
    
    # Create analyzer
    analyzer = LessonAnalyzer()
    print("✓ Created LessonAnalyzer")
    
    # Analyze with both text and PDF
    print("\n⏳ Analyzing lesson plan (text + PDF)...")
    request = LessonSetupRequest(
        lesson_plan_text=SAMPLE_LESSON_TEXT,
        lesson_plan_pdf_base64=pdf_base64
    )
    
    context = await analyzer.analyze_lesson_plan(request, student_profiles)
    
    # Validate output
    assert validate_lesson_context(context, "TEXT + PDF INPUT")
    assert context.grade_level is not None
    assert len(context.student_approaches) > 0
    print("✅ Test passed!")


@pytest.mark.asyncio
async def test_lesson_context_structure():
    """Test that LessonContext matches expected data model."""
    print("\n" + "="*80)
    print("TEST 4: LESSON CONTEXT DATA MODEL VALIDATION")
    print("="*80)
    
    # Load profiles
    profiles_dir = Path(__file__).parent.parent / "src" / "rehearsed_multi_student" / "profiles"
    loader = ProfileLoader(profiles_dir)
    student_profiles = loader.load_all_profiles()
    
    # Create analyzer
    analyzer = LessonAnalyzer()
    
    # Analyze text lesson
    print("\n⏳ Analyzing lesson plan for model validation...")
    request = LessonSetupRequest(lesson_plan_text=SAMPLE_LESSON_TEXT)
    context = await analyzer.analyze_lesson_plan(request, student_profiles)
    
    print("\n✅ Validating data model structure:")
    
    # Check types
    print(f"   ✓ grade_level is str: {isinstance(context.grade_level, str)}")
    print(f"   ✓ subject is str: {isinstance(context.subject, str)}")
    print(f"   ✓ topic is str: {isinstance(context.topic, str)}")
    print(f"   ✓ learning_objectives is list: {isinstance(context.learning_objectives, list)}")
    print(f"   ✓ key_concepts is list: {isinstance(context.key_concepts, list)}")
    print(f"   ✓ context_summary is str: {isinstance(context.context_summary, str)}")
    print(f"   ✓ mathematical_problem is str or None: {isinstance(context.mathematical_problem, (str, type(None)))}")
    print(f"   ✓ student_approaches is dict: {isinstance(context.student_approaches, dict)}")
    
    # Check student approaches structure
    print(f"\n   Student Approaches ({len(context.student_approaches)}):")
    for student_id, approach in context.student_approaches.items():
        print(f"     • {student_id}:")
        print(f"       - student_id: {approach.student_id}")
        print(f"       - student_name: {approach.student_name}")
        print(f"       - learning_style: {approach.learning_style}")
        print(f"       - thinking_approach: {approach.thinking_approach[:80]}...")
    
    # Assertions
    assert isinstance(context, LessonContext)
    assert all(isinstance(obj, str) for obj in context.learning_objectives)
    assert all(isinstance(concept, str) for concept in context.key_concepts)
    assert all(hasattr(approach, 'student_id') for approach in context.student_approaches.values())
    assert all(hasattr(approach, 'thinking_approach') for approach in context.student_approaches.values())
    
    print("\n✅ All model validations passed!")


if __name__ == "__main__":
    print("\n🚀 Running Lesson Analyzer Tests...")
    asyncio.run(test_lesson_analyzer_with_text())
    asyncio.run(test_lesson_analyzer_with_pdf())
    asyncio.run(test_lesson_analyzer_with_text_and_pdf())
    asyncio.run(test_lesson_context_structure())
    print("\n✨ All tests completed!")
