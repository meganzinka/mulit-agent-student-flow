# Rehearsed Multi-Student Backend

AI-powered classroom simulation system for teacher training with real-time feedback.

## Features

✅ **Parallel Student Agents**: 3 AI students (Vex, Chipper, Riven) with distinct learning styles  
✅ **K-12 Adaptive**: Students adapt to any grade level and topic via lesson context  
✅ **Real-Time Coaching**: SSE-based feedback on teacher questioning moves  
✅ **Audio Responses**: Gemini TTS generates student voice responses  
✅ **Lesson Plan Analysis**: PDF/text → structured context extraction  
✅ **Multi-Turn Conversations**: Maintains conversation history  
✅ **Cloud-Ready**: No disk I/O, stateless, container-ready

## Student Profiles

- **Vex** (Algorithmic): Step-by-step, procedural thinking
- **Chipper** (Visual): Visual/spatial reasoning, pattern recognition  
- **Riven** (Struggling): Needs support, uncertain participation

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

### Health & Discovery
- `GET /` - Health check
- `GET /students` - List student profiles

### Lesson Setup (NEW!)
```bash
POST /lesson/setup
{
  "lesson_plan_text": "3rd Grade Math - Fractions...",
  "lesson_plan_pdf_base64": "..."  # optional, PDF via base64
}
```
**Returns**: Structured lesson context (grade, topic, objectives, key concepts)

### Ask Students (Text)
```bash
POST /ask
POST /ask?stream_feedback=true  # with real-time coaching feedback (SSE)

{
  "prompt": "What is a fraction?",
  "lesson_context": {...},        # from /lesson/setup
  "conversation_history": [...]   # optional
}
```

### Ask Students (With Audio)
```bash
POST /ask/with-audio
POST /ask/with-audio?stream_feedback=true

{
  "prompt": "...",
  "lesson_context": {...},
  "conversation_history": [...]
}
```
**Returns**: Student responses + base64-encoded MP3 audio

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
            {"speaker": "Chipper", "message": "It's 3"}
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
├── src/rehearsed_multi_student/
│   ├── agents/               # AI agents with business logic
│   │   ├── student_agent.py    # Student personalities + decisions
│   │   └── feedback_agent.py   # Teacher coaching analysis
│   ├── services/             # Stateless utilities  
│   │   ├── tts_service.py      # Text-to-speech (Gemini TTS)
│   │   └── lesson_analyzer.py  # Lesson plan → context extraction
│   ├── models/               # Pydantic schemas
│   │   ├── schemas.py
│   │   └── feedback.py
│   ├── profiles/             # Student YAML configs
│   │   ├── algorithmic_student.yaml
│   │   ├── visual_student.yaml
│   │   └── struggling_student.yaml
│   └── api/                  # FastAPI endpoints
│       └── main.py
├── tests/                    # Test files
│   ├── test_agents.py
│   ├── test_feedback.py
│   └── test_lesson_context.py
└── pyproject.toml
```

## Running Tests

```bash
# All tests
poetry run python -m pytest tests/

# Specific tests
poetry run python tests/test_lesson_context.py
poetry run python tests/test_feedback.py
poetry run python tests/test_agents.py
```

## Tech Stack

- **FastAPI**: REST API + SSE streaming
- **Google GenAI**: Gemini 2.5 Flash for text generation
- **Google Cloud TTS**: Gemini TTS for audio (gemini-2.5-flash-tts)
- **Pydantic**: Data validation
- **Poetry**: Dependency management

## Workflow Example

1. **Teacher uploads lesson plan** → `POST /lesson/setup`
2. **Frontend stores lesson context** (grade level, objectives, etc.)
3. **Teacher asks question** → `POST /ask?stream_feedback=true` (includes lesson_context)
4. **Students respond** (adapted to grade level from lesson)
5. **Teacher receives coaching feedback** (via SSE, evaluates against lesson objectives)

## Cloud Deployment

Designed for **Cloud Run**:
- ✅ No disk I/O (PDFs via base64 inline data)
- ✅ Stateless (all context in requests)  
- ✅ ADC authentication
- ✅ Container-ready

## License

MIT
