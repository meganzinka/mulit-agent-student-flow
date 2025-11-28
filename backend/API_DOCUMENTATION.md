# API Documentation - Rehearsed Multi-Student Backend

Base URL: `http://localhost:8000/api` (development)

**Note:** All endpoints are prefixed with `/api` for load balancer routing. When deployed to Cloud Run behind a load balancer, the base URL will be `https://demo.rehearsed.io/api`.

**Focus:** All feedback provided by this API is laser-focused on the quality of mathematical discourse, including:
- Use of math talk moves (revoicing, asking for explanations, pressing for reasoning, connecting ideas)
- Building on and connecting student ideas
- Use and discussion of mathematical representations (drawings, models, equations)
- Precision and clarity of mathematical language
- Surfacing and addressing misconceptions

## Table of Contents
1. [Health & Discovery](#health--discovery)
2. [Lesson Setup](#lesson-setup)
3. [Ask Students (Text)](#ask-students-text)
4. [Ask Students (With Audio)](#ask-students-with-audio)
5. [Streaming Feedback (SSE)](#streaming-feedback-sse)
6. [End Lesson](#end-lesson)
7. [Data Models](#data-models)

---

## Health & Discovery

### `GET /api/`
Health check endpoint.

**Response:**
```json
{
  "status": "ok",
  "message": "Rehearsed Multi-Student API is running",
  "students_loaded": 3
}
```

### `GET /api/students`
List all available student profiles.

**Response:**
```json
{
  "students": [
    {
      "id": "algorithmic_thinker",
      "name": "Vex",
      "learning_style": "algorithmic",
      "description": "Step-by-step, formula-focused, procedural thinker"
    },
    {
      "id": "visual_thinker",
      "name": "Chipper",
      "learning_style": "visual",
      "description": "Diagram-focused, pattern recognition, spatial reasoning"
    },
    {
      "id": "struggling_learner",
      "name": "Riven",
      "learning_style": "struggling",
      "description": "Low confidence, needs support, difficulty articulating"
    }
  ]
}
```

---

## Lesson Setup

### `POST /api/lesson/setup`
Analyze a lesson plan (text or PDF) and extract structured context.

**Purpose:** Use this at the beginning of a session. The returned `LessonContext` should be stored in the frontend and included in subsequent `/api/ask` requests so students adapt to the grade level and topic. 

The lesson analyzer calls Gemini to extract:
- Grade level, subject, and topic
- Learning objectives and key concepts
- Context summary (how students at this level think about the topic)
- The mathematical problem being discussed
- How each student profile would approach this problem

**Request:**
```json
{
  "lesson_plan_text": "3rd Grade Mathematics\n\nTopic: Fractions...",
  "lesson_plan_pdf_base64": "JVBERi0xLjQKJeLjz9..."  // optional
}
```

**Request Fields:**
- `lesson_plan_text` (string, optional): Plain text of the lesson plan
- `lesson_plan_pdf_base64` (string, optional): Base64-encoded PDF file
- **Note:** Must provide at least one of the above

**Response:**
```json
{
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
  "context_summary": "In this 3rd grade lesson, students are introduced to fractions for the first time. At this developmental level, students need concrete visual representations (like pizza slices) to understand the concept. They should be thinking about fractions in terms of parts of physical objects rather than abstract numbers.",
  "mathematical_problem": "If you cut a pizza into 4 equal pieces and eat 1 piece, what fraction of the pizza did you eat?",
  "student_approaches": {
    "algorithmic_thinker": {
      "student_id": "algorithmic_thinker",
      "student_name": "Vex",
      "approach_description": "Vex will focus on the procedural steps: identifying the whole (4 pieces), counting the part (1 piece), and forming the fraction 1/4. Prefers explicit instructions and formulas.",
      "strengths": ["Systematic thinking", "Clear step-by-step reasoning"],
      "misconceptions": ["May struggle with non-standard representations", "Might rely too heavily on procedures without understanding"]
    },
    "visual_thinker": {
      "student_id": "visual_thinker",
      "student_name": "Chipper",
      "approach_description": "Chipper will visualize the pizza as circles or rectangles divided into parts. Uses mental images and patterns to understand fractions.",
      "strengths": ["Spatial reasoning", "Pattern recognition"],
      "misconceptions": ["May have difficulty with abstract notation", "Might struggle when visuals aren't available"]
    },
    "struggling_learner": {
      "student_id": "struggling_learner",
      "student_name": "Riven",
      "approach_description": "Riven needs concrete, real-world examples and support. May struggle with both abstract thinking and visual representations, requiring step-by-step guidance.",
      "strengths": ["Responds to encouragement", "Benefits from concrete examples"],
      "misconceptions": ["Low confidence", "May confuse the numerator and denominator"]
    }
  }
}
```

**Frontend Flow:**
1. User uploads lesson plan (text or PDF)
2. Convert PDF to base64 if needed
3. Call `POST /api/lesson/setup`
4. **Store the returned `LessonContext` in session state**
5. Include it in all subsequent `/api/ask` requests

---

## Ask Students (Text)

### `POST /api/ask`
Send a teacher prompt to all students and get their text responses.

**Query Parameters:**
- `stream_feedback` (boolean, optional): If `true`, returns SSE stream with feedback. If `false` or omitted, returns JSON immediately.

**Request:**
```json
{
  "prompt": "If I cut a pizza into 4 equal pieces and eat 1 piece, what fraction did I eat?",
  "lesson_context": {
    "grade_level": "3rd grade",
    "subject": "Mathematics",
    "topic": "Fractions - Understanding Parts of a Whole",
    "learning_objectives": [...],
    "key_concepts": [...],
    "context_summary": "..."
  },
  "conversation_history": [
    {
      "speaker": "Teacher",
      "message": "What is a fraction?"
    },
    {
      "speaker": "Chipper",
      "message": "A fraction is like a part of something bigger!"
    }
  ]
}
```

**Request Fields:**
- `prompt` (string, required): The teacher's question
- `lesson_context` (object, optional): The `LessonContext` from `/lesson/setup`
  - If omitted, students default to "8th grade" behavior
  - **Best practice:** Always include this after lesson setup
- `conversation_history` (array, optional): Previous messages for context
  - Each message has `speaker` and `message` fields

**Response (when `stream_feedback=false` or omitted):**
```json
{
  "students": [
    {
      "student_id": "algorithmic_thinker",
      "student_name": "Vex",
      "would_raise_hand": true,
      "confidence_score": 0.85,
      "thinking_process": "I know the pizza was cut into 4 pieces, so the bottom number is 4. I ate 1 piece, so the top number is 1.",
      "response": "One fourth! Or you could write it as 1/4.",
      "audio_base64": null
    },
    {
      "student_id": "visual_thinker",
      "student_name": "Chipper",
      "would_raise_hand": true,
      "confidence_score": 0.9,
      "thinking_process": "I can picture the pizza cut into 4 slices. If you take away 1 slice, that's 1 out of 4.",
      "response": "You ate 1 out of 4 pieces, so that's 1/4!",
      "audio_base64": null
    },
    {
      "student_id": "struggling_learner",
      "student_name": "Riven",
      "would_raise_hand": false,
      "confidence_score": 0.5,
      "thinking_process": "Um, there were 4 pieces... and 1 was eaten... so maybe 1 and 4 go together somehow?",
      "response": "I think it's... 1 over 4? Like 1/4?",
      "audio_base64": null
    }
  ],
  "summary": "2 out of 3 students would raise their hand to answer this question."
}
```

**Response (when `stream_feedback=true`):**
See [Streaming Feedback (SSE)](#streaming-feedback-sse) section.

---

## Ask Students (With Audio)

### `POST /api/ask/with-audio`
Same as `/api/ask` but includes audio generation for student responses.

**Query Parameters:**
- `stream_feedback` (boolean, optional): Same as `/ask`

**Request:**
Same as `/ask` endpoint.

**Response:**
Same as `/ask`, but each student includes:
```json
{
  "student_id": "algorithmic_thinker",
  "student_name": "Vex",
  "would_raise_hand": true,
  "confidence_score": 0.85,
  "thinking_process": "...",
  "response": "One fourth! Or you could write it as 1/4.",
  "audio_base64": "//NExAAAAAANIAAAAAExBTUUzLjEwMFVVVVVVVVVVVVVVVVVVVVVV..."
}
```

**Audio Details:**
- Format: MP3
- Encoding: Base64 string
- Generated using: Gemini TTS (gemini-2.5-flash-tts)
- Unique voices per student:
  - Vex: Zubenelgenubi (male, methodical)
  - Chipper: Kore (female, animated)
  - Riven: Pulcherrima (female, hesitant)

**Decoding Audio (Frontend):**
```javascript
// Convert base64 to audio blob
const audioBlob = await fetch(`data:audio/mp3;base64,${student.audio_base64}`)
  .then(res => res.blob());

// Play audio
const audio = new Audio(URL.createObjectURL(audioBlob));
audio.play();
```

---

## Streaming Feedback (SSE)

### `POST /api/ask?stream_feedback=true`
### `POST /api/ask/with-audio?stream_feedback=true`

When `stream_feedback=true`, the response is a **Server-Sent Events (SSE)** stream.

**Flow:**
1. Students respond immediately (sent first)
2. Feedback is generated and streamed in real-time
3. Stream closes when complete

**Event Types:**

#### `students_response`
Sent immediately with all student responses.

```
event: students_response
data: {"students":[...],"summary":"2 out of 3 students would raise their hand."}
```

#### `feedback_insight`
Each coaching insight is streamed as it's generated.

```
event: feedback_insight
data: {"category":"question_quality","message":"You asked an open-ended question that invites students to share their thinking. This is a great way to surface student understanding before correcting misconceptions.","severity":"info"}
```

**Insight Categories (for backward compatibility):**
- `equity` - Participation and access patterns
- `question_quality` - Effectiveness of the teacher's question
- `engagement` - Student engagement levels
- Other categories based on mathematical discourse analysis

**Severity Levels:**
- `info` - Positive observation, celebrate wins
- `suggestion` - Room for improvement
- `concern` - Important issue to address

**Note:** The feedback now focuses exclusively on mathematical discourse quality (math talk moves, reasoning, representations, precision of language, misconception handling) rather than general classroom management strategies.

#### `feedback_complete`
Overall summary of the interaction.

```
event: feedback_complete
data: {"overall_observation":"Strong start! Your concrete example engages visual and concrete thinkers while remaining accessible to struggling learners."}
```

#### `done`
Signals end of stream.

```
event: done
data: {}
```

#### `error`
Sent if an error occurs during feedback generation.

```
event: error
data: {"error":"Feedback generation failed: ..."}
```

**Frontend Implementation (JavaScript):**
```javascript
const eventSource = new EventSource('http://localhost:8000/api/ask?stream_feedback=true', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    prompt: "...",
    lesson_context: {...},
    conversation_history: [...]
  })
});

eventSource.addEventListener('students_response', (e) => {
  const data = JSON.parse(e.data);
  // Display student responses immediately
  displayStudents(data.students);
});

eventSource.addEventListener('feedback_insight', (e) => {
  const insight = JSON.parse(e.data);
  // Display each insight as it arrives
  addFeedbackInsight(insight);
});

eventSource.addEventListener('feedback_complete', (e) => {
  const data = JSON.parse(e.data);
  // Display overall summary
  showOverallFeedback(data.overall_observation);
});

eventSource.addEventListener('done', () => {
  eventSource.close();
});

eventSource.addEventListener('error', (e) => {
  const error = JSON.parse(e.data);
  console.error('Feedback error:', error);
  eventSource.close();
});
```

**Note:** For a simple POST request with SSE, you may need to use `fetch` with streaming instead of `EventSource`:

```javascript
const response = await fetch('http://localhost:8000/api/ask?stream_feedback=true', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ prompt: "...", lesson_context: {...} })
});

const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const { value, done } = await reader.read();
  if (done) break;
  
  const chunk = decoder.decode(value);
  const lines = chunk.split('\n');
  
  for (const line of lines) {
    if (line.startsWith('event: ')) {
      const eventType = line.slice(7);
    } else if (line.startsWith('data: ')) {
      const data = JSON.parse(line.slice(6));
      // Handle based on eventType
    }
  }
}
```

---

## End Lesson

### `POST /api/lesson/end`
End the practice session and receive comprehensive feedback focused on the quality of mathematical discussion.

**Purpose:** Call this when the teacher is finished practicing. This endpoint analyzes the complete conversation transcript and provides feedback laser-focused on the quality of mathematical discourse. Feedback includes:
- Strengths in promoting mathematical discussion (e.g., use of math talk moves, pressing for reasoning, connecting ideas, use of representations, precision of mathematical language)
- Areas for growth in mathematical discourse quality
- Actionable next steps and strategies to improve future math discussions (e.g., revoicing, pressing for reasoning, connecting student ideas)
- Celebration and encouragement

**Request:**
```json
{
  "lesson_context": {
    "grade_level": "3rd grade",
    "subject": "Mathematics",
    "topic": "Fractions - Understanding Parts of a Whole",
    "learning_objectives": [
      "Students will understand that a fraction represents a part of a whole",
      "Students will identify numerator and denominator"
    ],
    "key_concepts": ["Fraction", "Numerator", "Denominator"],
    "context_summary": "..."
  },
  "conversation_transcript": [
    {
      "speaker": "Teacher",
      "message": "What is a fraction?"
    },
    {
      "speaker": "Chipper",
      "message": "A fraction is like a part of something bigger!"
    },
    {
      "speaker": "Teacher",
      "message": "Great! Can you give me an example?"
    },
    {
      "speaker": "Chipper",
      "message": "Like if you cut a pizza into 4 slices, each slice is 1/4"
    }
  ]
}
```

**Request Fields:**
- `lesson_context` (object, required): The same `LessonContext` from `/lesson/setup`
- `conversation_transcript` (array, required): Complete history of all messages
  - Include ALL teacher prompts and student responses
  - Each message has `speaker` (Teacher or student name) and `message` fields

**Response:**
```json
{
  "lesson_summary": {
    "total_exchanges": 8,
    "students_called_on": ["Chipper", "Vex"],
    "participation_pattern": "Chipper and Vex actively participated, responding to teacher prompts. Riven was present but not called on. Teacher used open-ended questions and concrete examples to engage students.",
    "key_moments": [
      "Teacher used concrete pizza example to introduce fractions",
      "Chipper explained fractions using real-world context",
      "Vex provided procedural explanation and reasoning for 1/4",
      "Teacher asked for mathematical reasoning and pressed for explanation"
    ]
  },
  "overall_feedback": "You facilitated a mathematical discussion that encouraged students to connect real-world examples to fraction concepts. You used open-ended questions and pressed for reasoning, which are key moves in math talk. Incorporating more math talk moves such as revoicing, connecting student ideas, and using representations will further enrich the mathematical discourse and deepen understanding.",
  "strengths_and_growth": {
    "strengths": [
      "Used open-ended questions to elicit student thinking (e.g., 'What is a fraction?')",
      "Pressed for mathematical reasoning by asking students to explain their answers",
      "Connected math to real-world context (pizza example)",
      "Created a supportive environment for sharing ideas"
    ],
    "areas_for_growth": [
      "Use more math talk moves such as revoicing and connecting student ideas",
      "Incorporate mathematical representations (drawings, models, equations) and discuss them explicitly",
      "Press for deeper reasoning and encourage students to build on each other's ideas"
    ]
  },
  "next_steps": {
    "immediate_actions": [
      "Try revoicing a student idea to clarify and highlight mathematical language",
      "Ask students to compare or connect their ideas during discussion",
      "Encourage students to use and discuss visual models or representations"
    ],
    "practice_focus": "Focus on using math talk moves (revoicing, pressing for reasoning, connecting ideas)",
    "resources": [
      "Read: 'Five Practices for Orchestrating Productive Mathematics Discussions' by Smith & Stein",
      "Resource: https://www.nctm.org/Classroom-Resources/Illuminations/Lessons/Building-Fractions-with-Manipulatives/"
    ]
  },
  "celebration": "Great work facilitating a mathematical discussion! Your use of open-ended questions and real-world examples helped students connect to the math. With more math talk moves and explicit use of representations, you'll foster even richer mathematical discourse. Keep up the thoughtful questioning and encouragement! 🎉"
}
```

**Frontend Flow:**
1. Teacher completes practice lesson
2. Click "End Lesson" button
3. Frontend sends `POST /api/lesson/end` with lesson context and full transcript
4. Display comprehensive feedback to teacher
5. Teacher can review strengths, growth areas, and next steps

**Frontend Implementation:**
```javascript
// React Component
import { useState } from 'react';

function EndLesson({ lessonContext, conversationHistory }) {
  const [feedback, setFeedback] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleEndLesson = async () => {
    setLoading(true);
    
    const response = await fetch('http://localhost:8000/api/lesson/end', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        lesson_context: lessonContext,
        conversation_transcript: conversationHistory
      })
    });

    const data = await response.json();
    setFeedback(data);
    setLoading(false);
  };

  if (!feedback) {
    return (
      <button onClick={handleEndLesson} disabled={loading}>
        {loading ? 'Generating Feedback...' : 'End Lesson'}
      </button>
    );
  }

  return (
    <div className="lesson-feedback">
      <h2>Lesson Summary</h2>
      <p>Total Exchanges: {feedback.lesson_summary.total_exchanges}</p>
      <p>Students Called On: {feedback.lesson_summary.students_called_on.join(', ')}</p>
      <p>{feedback.lesson_summary.participation_pattern}</p>
      
      <h3>Key Moments</h3>
      <ul>
        {feedback.lesson_summary.key_moments.map((moment, i) => (
          <li key={i}>{moment}</li>
        ))}
      </ul>

      <h2>Overall Feedback</h2>
      <p>{feedback.overall_feedback}</p>

      <h2>Your Strengths</h2>
      <ul>
        {feedback.strengths_and_growth.strengths.map((strength, i) => (
          <li key={i} className="strength">✅ {strength}</li>
        ))}
      </ul>

      <h2>Areas for Growth</h2>
      <ul>
        {feedback.strengths_and_growth.areas_for_growth.map((area, i) => (
          <li key={i} className="growth">📈 {area}</li>
        ))}
      </ul>

      <h2>Next Steps</h2>
      <h3>Try These in Your Next Lesson:</h3>
      <ul>
        {feedback.next_steps.immediate_actions.map((action, i) => (
          <li key={i}>{action}</li>
        ))}
      </ul>
      <p><strong>Practice Focus:</strong> {feedback.next_steps.practice_focus}</p>
      
      {feedback.next_steps.resources && (
        <>
          <h3>Recommended Resources:</h3>
          <ul>
            {feedback.next_steps.resources.map((resource, i) => (
              <li key={i}>{resource}</li>
            ))}
          </ul>
        </>
      )}

      <div className="celebration">
        <h2>🎉 Celebration</h2>
        <p>{feedback.celebration}</p>
      </div>
    </div>
  );
}
```

---

## Data Models

### LessonContext
```javascript
/**
 * @typedef {Object} LessonContext
 * @property {string} grade_level - e.g., "3rd grade", "High School"
 * @property {string} subject - e.g., "Mathematics", "Algebra"
 * @property {string} topic - e.g., "Fractions - Parts of a Whole"
 * @property {string[]} learning_objectives
 * @property {string[]} key_concepts
 * @property {string} context_summary - How students at this level think about the topic
 * @property {string} mathematical_problem - The specific problem being discussed (e.g., "If you cut a pizza...")
 * @property {Object<string, StudentApproachOutput>} student_approaches - How each student profile approaches this problem, indexed by student_id
 */

/**
 * @typedef {Object} StudentApproachOutput
 * @property {string} student_id - e.g., "algorithmic_thinker"
 * @property {string} student_name - e.g., "Vex"
 * @property {string} approach_description - How this student would approach the problem
 * @property {string[]} strengths - Cognitive strengths for this topic
 * @property {string[]} misconceptions - Common misconceptions this student might have
 */
```

### ConversationMessage
```javascript
/**
 * @typedef {Object} ConversationMessage
 * @property {string} speaker - "Teacher", "Vex", "Chipper", "Riven"
 * @property {string} message
 */
```

### StudentResponse
```javascript
/**
 * @typedef {Object} StudentResponse
 * @property {string} student_id - "algorithmic_thinker", "visual_thinker", "struggling_learner"
 * @property {string} student_name - "Vex", "Chipper", "Riven"
 * @property {boolean} would_raise_hand
 * @property {number} confidence_score - 0.0 - 1.0
 * @property {string} thinking_process - Internal reasoning
 * @property {string|null} response - What they'd say (always present)
 * @property {string|null} audio_base64 - Only in /ask/with-audio
 */
```

### FeedbackInsight
```javascript
/**
 * @typedef {Object} FeedbackInsight
 * @property {string} category - Category of insight (e.g., 'question_quality', 'equity', 'engagement')
 * @property {string} message - Feedback message (specific, actionable)
 * @property {('info'|'suggestion'|'concern')} severity - Severity level
 */
```

### TeacherFeedback (Real-time coaching feedback)
```javascript
/**
 * @typedef {Object} TeacherFeedback
 * @property {string|null} question_type - Type of question demonstrated: 'build_on', 'probing', 'visibility', or null
 * @property {string} feedback - Analysis of the teacher's statement. What they did well, areas to improve. Specific and grounded in the mathematical problem and student responses.
 * @property {string} suggestion - Actionable coaching suggestion. Framed as something to consider or try next. Focuses on strengthening mathematical discourse.
 */
```

### EndLessonRequest
```javascript
/**
 * @typedef {Object} EndLessonRequest
 * @property {LessonContext} lesson_context - The lesson that was taught (from /api/lesson/setup)
 * @property {ConversationMessage[]} conversation_transcript - Complete transcript of all messages during the lesson
 */
```

### LessonSummary
```javascript
/**
 * @typedef {Object} LessonSummary
 * @property {number} total_exchanges - Number of teacher-student exchanges
 * @property {string[]} students_called_on - Which students were called on
 * @property {string} participation_pattern - Summary of participation patterns
 * @property {string[]} key_moments - Notable moments in the lesson
 */
```

### StrengthsAndGrowth
```javascript
/**
 * @typedef {Object} StrengthsAndGrowth
 * @property {string[]} strengths - What the teacher did well
 * @property {string[]} areas_for_growth - Areas to improve
 */
```

### NextSteps
```javascript
/**
 * @typedef {Object} NextSteps
 * @property {string[]} immediate_actions - Things to try in the next lesson
 * @property {string} practice_focus - What skill to focus on
 * @property {string[]} resources - Suggested resources (optional)
 */
```

### EndLessonResponse
```javascript
/**
 * @typedef {Object} EndLessonResponse
 * @property {LessonSummary} lesson_summary
 * @property {string} overall_feedback - Overall narrative feedback
 * @property {StrengthsAndGrowth} strengths_and_growth
 * @property {NextSteps} next_steps
 * @property {string} celebration - Positive reinforcement message
 */
```

---

## Example Workflow

### 1. Setup Lesson
```javascript
// React Component Example
import { useState } from 'react';

function LessonSetup() {
  const [lessonContext, setLessonContext] = useState(null);

  const handleFileUpload = async (file) => {
    const pdfBase64 = await convertFileToBase64(file);

    const response = await fetch('http://localhost:8000/api/lesson/setup', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        lesson_plan_text: "",
        lesson_plan_pdf_base64: pdfBase64
      })
    });

    const context = await response.json();
    setLessonContext(context);
    // Or store in localStorage/sessionStorage:
    localStorage.setItem('lessonContext', JSON.stringify(context));
  };

  return (
    <div>
      <input type="file" onChange={(e) => handleFileUpload(e.target.files[0])} />
      {lessonContext && <p>Lesson loaded: {lessonContext.topic}</p>}
    </div>
  );
}
```

### 2. Ask Question (First Turn)
```javascript
// React Component with SSE
import { useState } from 'react';

function AskQuestion({ lessonContext }) {
  const [students, setStudents] = useState([]);
  const [feedback, setFeedback] = useState([]);
  const [question, setQuestion] = useState('');

  const askStudents = async () => {
    const response = await fetch('http://localhost:8000/api/ask/with-audio?stream_feedback=true', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        prompt: question,
        lesson_context: lessonContext,
        conversation_history: []
      })
    });

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let eventType = '';

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value);
      const lines = chunk.split('\n');

      for (const line of lines) {
        if (line.startsWith('event: ')) {
          eventType = line.slice(7).trim();
        } else if (line.startsWith('data: ')) {
          const data = JSON.parse(line.slice(6));

          if (eventType === 'students_response') {
            setStudents(data.students);
          } else if (eventType === 'feedback_insight') {
            setFeedback(prev => [...prev, data]);
          }
        }
      }
    }
  };

  return (
    <div>
      <input value={question} onChange={(e) => setQuestion(e.target.value)} />
      <button onClick={askStudents}>Ask Students</button>

      {students.map(student => (
        <div key={student.student_id}>
          <h3>{student.student_name} {student.would_raise_hand ? '✋' : ''}</h3>
          <p>{student.response}</p>
          {student.audio_base64 && (
            <audio controls src={`data:audio/mp3;base64,${student.audio_base64}`} />
          )}
        </div>
      ))}

      {feedback.map((insight, i) => (
        <div key={i} className={`feedback-${insight.severity}`}>
          <strong>{insight.category}:</strong> {insight.message}
        </div>
      ))}
    </div>
  );
}
```

### 3. Ask Follow-Up (Multi-Turn)
```javascript
// React Component with Conversation History
import { useState } from 'react';

function Conversation({ lessonContext }) {
  const [conversationHistory, setConversationHistory] = useState([]);
  const [students, setStudents] = useState([]);

  const callOnStudent = (studentName, studentResponse) => {
    // Add to conversation history
    setConversationHistory(prev => [
      ...prev,
      { speaker: "Teacher", message: `${studentName}, what do you think?` },
      { speaker: studentName, message: studentResponse }
    ]);
  };

  const askFollowUp = async (followUpQuestion) => {
    const response = await fetch('http://localhost:8000/ask?stream_feedback=true', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        prompt: followUpQuestion,
        lesson_context: lessonContext,
        conversation_history: conversationHistory
      })
    });

    // Handle SSE stream (same as above)
  };

  return (
    <div>
      {/* Display conversation history */}
      {conversationHistory.map((msg, i) => (
        <div key={i}>
          <strong>{msg.speaker}:</strong> {msg.message}
        </div>
      ))}

      {/* Display current student responses */}
      {students.map(student => (
        <button
          key={student.student_id}
          onClick={() => callOnStudent(student.student_name, student.response)}
        >
          Call on {student.student_name}
        </button>
      ))}
    </div>
  );
}
```

---

## Error Handling

All endpoints return standard HTTP status codes:

**200 OK** - Success
**400 Bad Request** - Invalid request (missing required fields)
**500 Internal Server Error** - Server error (e.g., Gemini API failure)

**Error Response:**
```json
{
  "detail": "Error message describing what went wrong"
}
```

---

## CORS

The API has CORS enabled for all origins in development. In production, configure appropriately.

---

## Rate Limiting

Currently no rate limiting. Consider implementing in production.

---

## Questions?

For issues or questions, contact the backend team or file an issue in the GitHub repo.
