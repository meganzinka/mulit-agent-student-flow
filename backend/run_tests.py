#!/usr/bin/env python3
"""
Run all tests against the deployed Cloud Run API.
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from tests.test_lesson_context import test_lesson_context_workflow, test_pdf_lesson_plan
from tests.test_feedback import test_feedback_streaming, test_multi_turn_feedback


async def run_all_tests():
    """Run all integration tests against Cloud Run."""
    print("\n" + "="*80)
    print("🚀 RUNNING ALL TESTS AGAINST CLOUD RUN")
    print("   URL: https://rehearsed-multi-student-api-847407960490.us-central1.run.app")
    print("="*80)
    
    tests_passed = 0
    tests_failed = 0
    
    # Test 1: Lesson Context Workflow
    try:
        await test_lesson_context_workflow()
        tests_passed += 1
    except Exception as e:
        print(f"\n❌ Lesson Context Workflow FAILED: {e}")
        tests_failed += 1
    
    # Test 2: PDF Lesson Plan
    try:
        await test_pdf_lesson_plan()
        tests_passed += 1
    except Exception as e:
        print(f"\n❌ PDF Lesson Plan FAILED: {e}")
        tests_failed += 1
    
    # Test 3: Feedback Streaming
    try:
        await test_feedback_streaming()
        tests_passed += 1
    except Exception as e:
        print(f"\n❌ Feedback Streaming FAILED: {e}")
        tests_failed += 1
    
    # Test 4: Multi-Turn Feedback
    try:
        await test_multi_turn_feedback()
        tests_passed += 1
    except Exception as e:
        print(f"\n❌ Multi-Turn Feedback FAILED: {e}")
        tests_failed += 1
    
    # Summary
    print("\n\n" + "="*80)
    print("📊 TEST SUMMARY")
    print("="*80)
    print(f"✅ Passed: {tests_passed}")
    print(f"❌ Failed: {tests_failed}")
    print(f"📈 Total:  {tests_passed + tests_failed}")
    
    if tests_failed == 0:
        print("\n🎉 ALL TESTS PASSED!")
        print("="*80 + "\n")
        return 0
    else:
        print(f"\n⚠️  {tests_failed} TEST(S) FAILED")
        print("="*80 + "\n")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(run_all_tests())
    sys.exit(exit_code)
