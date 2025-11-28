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
│   ├── agents/                   # AI agents with business logic
│   │   ├── student_agent.py        # Parallel student simulator
│   │   ├── feedback_agent.py       # Real-time teaching feedback
│   │   └── lesson_summary_agent.py # End-of-lesson comprehensive feedback
│   ├── services/                # Stateless business logic services
│   │   ├── tts_service.py         # Text-to-speech (Gemini TTS)
│   │   └── lesson_analyzer.py     # Lesson plan → context + student approaches
│   ├── models/                  # Pydantic schemas organized by component
│   │   ├── domain.py              # Shared: StudentProfile, ConversationMessage, VoiceSettings
│   │   ├── lesson_analyzer/       # Lesson analyzer component
│   │   │   ├── request.py           # Input: LessonSetupRequest
│   │   │   ├── outputs.py           # LLM output: LessonAnalysisOutput
│   │   │   └── context.py           # Service output: LessonContext + StudentApproach
│   │   ├── student_agent/        # Student agent component
│   │   │   ├── request.py           # Input: TeacherPromptRequest
│   │   │   └── response.py          # Output: StudentResponse, MultiStudentResponse
│   │   ├── feedback_agent/       # Feedback agent component
│   │   │   ├── request.py           # Input: FeedbackContext
│   │   │   └── response.py          # Output: TeacherFeedback
│   │   └── lesson_summary_agent/ # Lesson summary agent component
│   │       ├── request.py           # Input: EndLessonRequest
│   │       ├── outputs.py           # LLM output: LessonSummaryOutput
│   │       └── response.py          # Output: EndLessonResponse
│   ├── profiles/                # Student personality configs (YAML)
│   │   ├── algorithmic_student.yaml
│   │   ├── visual_student.yaml
│   │   └── struggling_student.yaml
│   ├── prompts/                 # LLM system prompts organized by component
│   │   ├── student_agent_prompts.py
│   │   ├── feedback_agent_prompts.py
│   │   ├── lesson_analyzer_prompts.py
│   │   └── lesson_summary_prompts.py
│   ├── api/                     # FastAPI endpoints
│   │   └── main.py
│   └── config.py               # Application configuration
├── tests/                       # Integration and unit tests
│   ├── test_agents.py
│   ├── test_feedback.py
│   ├── test_lesson_context.py
│   ├── test_differentiation.py
│   └── test_end_lesson.py
├── pyproject.toml
├── run_tests.py               # Integration test runner
└── README.md
```

## Data Model Architecture

The models are organized by **component** rather than "type of model", making it easy to understand what each component needs:

### Lesson Analyzer Component
```
Input:  LessonSetupRequest (lesson plan text/PDF)
         ↓
   [Gemini Analysis]
         ↓
Output: LessonContext (includes student approaches for each profile)
```

### Student Agent Component
```
Input:  TeacherPromptRequest (teacher question + lesson context + conversation)
         ↓
   [Gemini Generation]
         ↓
Output: StudentResponse (raise hand?, confidence, response text, thinking)
```

### Feedback Agent Component
```
Input:  FeedbackContext (lesson context + conversation + latest teacher move)
         ↓
   [Gemini Analysis]
         ↓
Output: TeacherFeedback (coaching insights on math discourse quality)
```

### Lesson Summary Agent Component
```
Input:  EndLessonRequest (lesson context + full transcript)
         ↓
   [Gemini Analysis]
         ↓
Output: EndLessonResponse (comprehensive feedback, strengths, next steps)
```

## Running Tests

```bash
# All tests (requires pytest and dev dependencies)
poetry run pytest tests/

# Specific test
poetry run pytest tests/test_agents.py -v

# Integration tests against deployed API
poetry run python run_tests.py
```

## Key Architectural Concepts

### Single Lesson Analysis, Multiple Interpretations
When a teacher uploads a lesson plan:
1. **Lesson Analyzer** calls Gemini **once** to extract:
   - Core lesson info (grade level, topic, objectives)
   - Mathematical problem being discussed
   - Key subskills/success criteria
   - **For each student profile**: How that student would approach this problem

2. Each **Student Agent** receives:
   - The shared lesson context
   - **Their own** student approach (how they think about the problem differently)
   - The teacher's prompt

This enables **authentic differentiation**: each student genuinely thinks about the problem their own way.

### Component-Based Model Organization
Models are organized by component (lesson_analyzer, student_agent, etc.) rather than by "type" (inputs, outputs, schemas). This makes it immediately clear:
- What does component X receive? → Look in `component_x/request.py`
- What does component X return? → Look in `component_x/response.py`
- What does the LLM return for component X? → Look in `component_x/outputs.py`

### Shared Context Architecture
```
┌─────────────────────────────────────┐
│      Lesson Setup Phase             │
│  (LessonSetupRequest → LessonContext)│
└──────────────┬──────────────────────┘
               │
     ┌─────────▼─────────────────────────────────────────┐
     │         Lesson Context (Shared by All)           │
     │  ┌────────────────────────────────────────────┐   │
     │  │ • Grade level, topic, objectives           │   │
     │  │ • Mathematical problem being discussed      │   │
     │  │ • Subskills/success criteria               │   │
     │  │ • Student approaches (indexed by ID)        │   │
     │  │   - Each student's thinking approach        │   │
     │  │   - How they'd approach this problem        │   │
     │  └────────────────────────────────────────────┘   │
     └──────────────┬──────────────────────────────────────┘
                    │
        ┌───────────┴──────────┬──────────────┬──────────────┐
        │                      │              │              │
        ▼                      ▼              ▼              ▼
   ┌────────────┐     ┌──────────────┐  ┌────────────┐  ┌────────────┐
   │  Student   │     │   Student    │  │  Feedback  │  │   Lesson   │
   │   Agent 1  │     │   Agent 2    │  │   Agent    │  │  Summary   │
   │ (Vex)      │     │  (Chipper)   │  │            │  │   Agent    │
   │            │     │              │  │            │  │            │
   │ Receives:  │     │  Receives:   │  │ Receives:  │  │ Receives:  │
   │ • LessonCtx│     │  • LessonCtx │  │ • LessonCtx│  │ • LessonCtx│
   │ • Their own│     │  • Their own │  │ • Full     │  │ • Full     │
   │   approach │     │    approach  │  │   history  │  │   history  │
   │ • Question │     │  • Question  │  │ • Latest   │  │            │
   │            │     │              │  │   move     │  │            │
   └────────────┘     └──────────────┘  └────────────┘  └────────────┘
```

### Real-Time Feedback Flow
```
Teacher Question → Student Responses (parallel) → Feedback Agent analyzes move
                                                   (evaluates against subskills)
                                                   → Real-time coaching (SSE)
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
