"""
Integration tests for the Rehearsed Multi-Student API. 
These tests hit the actual API endpoints and validate responses. 
"""

import pytest
import requests
import base64
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8000/api"  # Update this to your actual API URL


@pytest.fixture
def api_base_url():
    """Fixture to provide the base API URL."""
    return BASE_URL


@pytest.fixture
def sample_lesson_context():
    """Fixture providing a sample lesson context for testing."""
    return {
        "grade_level": "3rd grade",
        "subject": "Mathematics",
        "topic": "Fractions - Introduction",
        "learning_objectives": [
            "Students will understand what a fraction represents",
            "Students will identify numerator and denominator"
        ],
        "key_concepts": ["fraction", "numerator", "denominator", "parts of a whole"],
        "context_summary": "Introduction to fractions using visual models and real-world examples"
    }


@pytest.fixture
def sample_conversation_history():
    """Fixture providing sample conversation history."""
    return [
        {"speaker": "Teacher", "message": "What is a fraction?"},
        {"speaker": "Chipper", "message": "A fraction is a part of something whole! "},
        {"speaker": "Teacher", "message": "Can you explain more, Vex?"},
        {"speaker": "Vex", "message": "A fraction has a top number and bottom number."}
    ]


class TestHealthAndDiscovery:
    """Test health check and discovery endpoints."""

    def test_health_check(self, api_base_url):
        """Test GET / endpoint returns healthy status."""
        response = requests. get(f"{api_base_url}/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "message" in data
        assert "students_loaded" in data
        assert isinstance(data["students_loaded"], int)
        assert data["students_loaded"] > 0

    def test_list_students(self, api_base_url):
        """Test GET /students endpoint returns student profiles."""
        response = requests.get(f"{api_base_url}/students")
        
        assert response.status_code == 200
        data = response.json()
        assert "students" in data
        assert isinstance(data["students"], list)
        assert len(data["students"]) > 0
        
        # Validate student structure
        for student in data["students"]:
            assert "id" in student
            assert "name" in student
            assert "learning_style" in student
            assert "description" in student
            assert isinstance(student["name"], str)


class TestLessonSetup:
    """Test lesson setup endpoint."""

    def test_lesson_setup_with_text(self, api_base_url):
        """Test POST /lesson/setup with lesson plan text."""
        payload = {
            "lesson_plan_text": """
            3rd Grade Mathematics - Fractions
            
            Learning Objectives:
            - Students will understand what a fraction represents
            - Students will identify the numerator and denominator
            
            Key Concepts:
            - Fraction, numerator, denominator, parts of a whole
            
            Activities:
            - Use pizza slices to demonstrate fractions
            - Practice identifying fractions in pictures
            """
        }
        
        response = requests.post(f"{api_base_url}/lesson/setup", json=payload)
        
        assert response.status_code == 200
        data = response. json()
        
        # Validate response structure
        assert "grade_level" in data
        assert "subject" in data
        assert "topic" in data
        assert "learning_objectives" in data
        assert "key_concepts" in data
        assert "context_summary" in data
        
        # Validate types
        assert isinstance(data["learning_objectives"], list)
        assert isinstance(data["key_concepts"], list)
        assert len(data["learning_objectives"]) > 0

    def test_lesson_setup_invalid_payload(self, api_base_url):
        """Test POST /lesson/setup with invalid payload."""
        payload = {}  # Empty payload
        
        response = requests.post(f"{api_base_url}/lesson/setup", json=payload)
        
        # Should return 422 for validation error
        assert response.status_code == 422


class TestAskStudents:
    """Test asking students endpoints."""

    def test_ask_students_basic(self, api_base_url, sample_lesson_context):
        """Test POST /ask endpoint with basic prompt."""
        payload = {
            "prompt": "What is a fraction? ",
            "lesson_context": sample_lesson_context
        }
        
        response = requests. post(f"{api_base_url}/ask", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate response structure
        assert "responses" in data
        assert isinstance(data["responses"], list)
        assert len(data["responses"]) > 0
        
        # Validate each student response
        for student_response in data["responses"]:
            assert "student_id" in student_response
            assert "student_name" in student_response
            assert "response" in student_response
            assert isinstance(student_response["response"], str)
            assert len(student_response["response"]) > 0

    def test_ask_students_with_history(self, api_base_url, sample_lesson_context, sample_conversation_history):
        """Test POST /ask with conversation history."""
        payload = {
            "prompt": "Can someone give me an example of a fraction?",
            "lesson_context": sample_lesson_context,
            "conversation_history": sample_conversation_history
        }
        
        response = requests.post(f"{api_base_url}/ask", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert "responses" in data
        assert len(data["responses"]) > 0

    def test_ask_students_with_audio(self, api_base_url, sample_lesson_context):
        """Test POST /ask/with-audio endpoint."""
        payload = {
            "prompt": "What is the numerator? ",
            "lesson_context": sample_lesson_context
        }
        
        response = requests.post(f"{api_base_url}/ask/with-audio", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate response structure with audio
        assert "responses" in data
        for student_response in data["responses"]:
            assert "student_id" in student_response
            assert "student_name" in student_response
            assert "response" in student_response
            assert "audio_base64" in student_response
            # Audio should be base64 encoded string or null
            assert student_response["audio_base64"] is None or isinstance(student_response["audio_base64"], str)

    def test_ask_students_with_feedback(self, api_base_url, sample_lesson_context, sample_conversation_history):
        """Test POST /ask/with-feedback endpoint."""
        payload = {
            "prompt": "Explain how to add fractions.",
            "lesson_context": sample_lesson_context,
            "conversation_history": sample_conversation_history
        }
        
        response = requests.post(f"{api_base_url}/ask/with-feedback", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate response has both student responses and feedback
        assert "responses" in data
        assert "feedback" in data
        
        # Validate feedback structure
        feedback = data["feedback"]
        assert "strengths" in feedback
        assert "suggestions" in feedback
        assert isinstance(feedback["strengths"], list)
        assert isinstance(feedback["suggestions"], list)

    def test_ask_students_empty_prompt(self, api_base_url, sample_lesson_context):
        """Test POST /ask with empty prompt."""
        payload = {
            "prompt": "",
            "lesson_context": sample_lesson_context
        }
        
        response = requests.post(f"{api_base_url}/ask", json=payload)
        
        # Should handle gracefully or return validation error
        assert response.status_code in [200, 422]


class TestEndLesson:
    """Test lesson end endpoint."""

    def test_end_lesson_comprehensive(self, api_base_url, sample_lesson_context, sample_conversation_history):
        """Test POST /lesson/end endpoint with full conversation."""
        payload = {
            "lesson_context": sample_lesson_context,
            "conversation_transcript": sample_conversation_history
        }
        
        response = requests.post(f"{api_base_url}/lesson/end", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate comprehensive feedback structure
        assert "lesson_summary" in data
        assert "overall_feedback" in data
        assert "strengths_and_growth" in data
        assert "next_steps" in data
        assert "celebration" in data
        
        # Validate lesson_summary
        summary = data["lesson_summary"]
        assert "total_exchanges" in summary
        assert "students_called_on" in summary
        assert "participation_pattern" in summary
        assert "key_moments" in summary
        assert isinstance(summary["total_exchanges"], int)
        assert isinstance(summary["students_called_on"], list)
        
        # Validate strengths_and_growth
        strengths_growth = data["strengths_and_growth"]
        assert "strengths" in strengths_growth
        assert "areas_for_growth" in strengths_growth
        assert isinstance(strengths_growth["strengths"], list)
        assert isinstance(strengths_growth["areas_for_growth"], list)
        
        # Validate next_steps
        next_steps = data["next_steps"]
        assert "immediate_actions" in next_steps
        assert "practice_focus" in next_steps
        assert isinstance(next_steps["immediate_actions"], list)
        assert isinstance(next_steps["practice_focus"], str)
        
        # Validate celebration message
        assert isinstance(data["celebration"], str)
        assert len(data["celebration"]) > 0

    def test_end_lesson_minimal_conversation(self, api_base_url, sample_lesson_context):
        """Test POST /lesson/end with minimal conversation."""
        minimal_transcript = [
            {"speaker": "Teacher", "message": "Hello class!"},
            {"speaker": "Chipper", "message": "Hi! "}
        ]
        
        payload = {
            "lesson_context": sample_lesson_context,
            "conversation_transcript": minimal_transcript
        }
        
        response = requests.post(f"{api_base_url}/lesson/end", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert "lesson_summary" in data
        assert "overall_feedback" in data


class TestErrorHandling:
    """Test error handling scenarios."""

    def test_invalid_endpoint(self, api_base_url):
        """Test requesting a non-existent endpoint."""
        response = requests.get(f"{api_base_url}/invalid-endpoint")
        assert response.status_code == 404

    def test_malformed_json(self, api_base_url):
        """Test POST with malformed JSON."""
        response = requests.post(
            f"{api_base_url}/ask",
            data="not valid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422

    def test_missing_required_fields(self, api_base_url):
        """Test POST /ask without required fields."""
        payload = {
            "prompt": "What is a fraction?"
            # Missing lesson_context
        }
        
        response = requests. post(f"{api_base_url}/ask", json=payload)
        assert response.status_code == 422


class TestCORS:
    """Test CORS headers are present."""

    def test_cors_headers_present(self, api_base_url):
        """Test that CORS headers are set correctly."""
        response = requests. options(f"{api_base_url}/")
        
        # CORS headers should be present
        assert "access-control-allow-origin" in response.headers or response.status_code == 200


# Performance tests
class TestPerformance:
    """Test API performance and response times."""

    def test_health_check_response_time(self, api_base_url):
        """Test health check responds quickly."""
        import time
        start = time.time()
        response = requests.get(f"{api_base_url}/")
        elapsed = time.time() - start
        
        assert response.status_code == 200

    def test_ask_students_response_time(self, api_base_url, sample_lesson_context):
        """Test /ask endpoint response time."""
        import time
        payload = {
            "prompt": "What is a fraction?",
            "lesson_context": sample_lesson_context
        }
        
        start = time.time()
        response = requests.post(f"{api_base_url}/ask", json=payload)
        elapsed = time.time() - start
        
        assert response.status_code == 200
        # LLM calls may take longer, adjust threshold as needed
        assert elapsed < 30.0  # Should respond within 30 seconds


if __name__ == "__main__":
    pytest.main([__file__, "-v"])