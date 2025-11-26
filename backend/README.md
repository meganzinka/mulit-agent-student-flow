# Rehearsed Multi-Student Backend

A parallel student agent system for teacher training using Google's Gemini AI.

## Overview

This backend simulates 3 distinct 8th-grade math students with different learning styles:
- **Alex** (Algorithmic Thinker): Step-by-step, formula-focused
- **Maya** (Visual Thinker): Diagram-focused, pattern recognition
- **Jordan** (Struggling Learner): Low confidence, difficulty articulating

When a teacher asks a question, all three student agents process it simultaneously and determine:
1. Would they raise their hand?
2. How confident are they?
3. What's their thinking process?
4. What would they say?

## Setup

### Prerequisites
- Python 3.12 or 3.13
- Poetry for package management
- Google Cloud account with ADC configured (run `gcloud auth application-default login`)

### Installation

1. **Clone and navigate to backend:**
```bash
cd backend
```

2. **Install dependencies:**
```bash
poetry install
# Or with dev dependencies for testing:
poetry install --extras dev
```

3. **Configure Google Cloud authentication:**
```bash
gcloud auth application-default login
```

4. **Activate virtual environment:**
```bash
poetry shell
```

## Running the API

### Development Server

```bash
poetry run uvicorn rehearsed_multi_student.api.main:app --reload
```

The API will be available at `http://localhost:8000`

### API Documentation

Once running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API Endpoints

### `GET /`
Health check endpoint.

**Response:**
```json
{
  "status": "ok",
  "message": "Rehearsed Multi-Student API is running",
  "students_loaded": 3
}
```

### `GET /students`
List all available student profiles.

**Response:**
```json
{
  "students": [
    {
      "id": "algorithmic_thinker",
      "name": "Alex",
      "learning_style": "algorithmic",
      "description": "Step-by-step, formula-focused, procedural thinker"
    },
    ...
  ]
}
```

### `POST /ask`
Send a prompt to all students and get their responses.

**Request Body:**
```json
{
  "prompt": "We have the line y = 2x + 1. What would a parallel line be?",
  "lesson_context": "Students are learning about parallel lines and slopes in linear equations.",
  "conversation_history": [
    {
      "speaker": "teacher",
      "message": "What is the slope of y = 2x + 1?"
    },
    {
      "speaker": "Alex",
      "message": "The slope is 2"
    }
  ]
}
```

**Response:**
```json
{
  "students": [
    {
      "student_id": "algorithmic_thinker",
      "student_name": "Alex",
      "would_raise_hand": true,
      "confidence_score": 0.8,
      "thinking_process": "I know parallel lines have the same slope...",
      "response": "It would be any line with slope 2, like y = 2x + 3"
    },
    ...
  ],
  "summary": "2 out of 3 students would raise their hand to answer this question."
}
```

## Example Usage

### Using curl

```bash
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "If we have y = 2/5x + 1, how would you create a system with one solution?",
    "lesson_context": "Working on systems of linear equations",
    "conversation_history": []
  }'
```

### Using Python

```python
import requests

response = requests.post(
    "http://localhost:8000/ask",
    json={
        "prompt": "What is the slope of a line perpendicular to y = 3x + 2?",
        "lesson_context": "Exploring perpendicular lines",
        "conversation_history": [
            {"speaker": "teacher", "message": "What's the slope of y = 3x + 2?"},
            {"speaker": "Maya", "message": "It's 3"}
        ]
    }
)

data = response.json()
for student in data["students"]:
    print(f"{student['student_name']}: {'✋' if student['would_raise_hand'] else '  '}")
    if student["response"]:
        print(f"  Says: {student['response']}")
```

## Project Structure

```
backend/
├── src/
│   └── rehearsed_multi_student/
│       ├── api/              # FastAPI application
│       │   └── main.py
│       ├── agents/           # Student agent logic
│       │   └── student_agent.py
│       ├── models/           # Pydantic models
│       │   └── schemas.py
│       └── profiles/         # Student profiles
│           ├── loader.py
│           ├── algorithmic_student.yaml
│           ├── visual_student.yaml
│           └── struggling_student.yaml
├── pyproject.toml
└── README.md
```

## Student Profiles

Student profiles are defined in YAML files with:
- **Traits**: confidence, participation willingness, processing speed
- **Strengths & Challenges**: Learning characteristics
- **Hand-raising criteria**: What makes them participate
- **Response patterns**: Typical language they use
- **Thinking approach**: How they process information

Edit the YAML files in `src/rehearsed_multi_student/profiles/` to customize student behavior.

## Next Steps

Future features to implement:
- [ ] Dynamic agent generation: Given a profile template and lesson topic, generate custom student YAML
- [ ] Audio streaming for student responses
- [ ] More diverse student archetypes
- [ ] Session memory (students remember previous questions)
- [ ] Teacher feedback integration

## Development

### Run Tests
```bash
# Run the simple test script
poetry run python test_agents.py

# Run pytest (when tests are added)
poetry run pytest
```

### Format Code
```bash
poetry run black .
poetry run isort .
```

## License

MIT
