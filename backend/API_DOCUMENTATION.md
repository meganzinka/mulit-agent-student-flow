# API Documentation - Rehearsed Multi-Student Backend

Base URL: `http://localhost:8000` (development)

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

### `POST /lesson/setup`
Analyze a lesson plan (text or PDF) and extract structured context.

**Purpose:** Use this at the beginning of a session. The returned `LessonContext` should be stored in the frontend and included in subsequent `/ask` requests so students adapt to the grade level and topic.

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
  "context_summary": "In this 3rd grade lesson, students are introduced to fractions for the first time. At this developmental level, students need concrete visual representations (like pizza slices) to understand the concept. They should be thinking about fractions in terms of parts of physical objects rather than abstract numbers."
}
```

**Frontend Flow:**
1. User uploads lesson plan (text or PDF)
2. Convert PDF to base64 if needed
3. Call `POST /lesson/setup`
4. **Store the returned `LessonContext` in session state**
5. Include it in all subsequent `/ask` requests

---

## Ask Students (Text)

### `POST /ask`
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

### `POST /ask/with-audio`
Same as `/ask` but includes audio generation for student responses.

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

### `POST /ask?stream_feedback=true`
### `POST /ask/with-audio?stream_feedback=true`

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
data: {"category":"question_quality","message":"Your question 'If I cut a pizza into 4 equal pieces and eat 1 piece, what fraction did I eat?' effectively uses a concrete example (pizza) that's developmentally appropriate for 3rd graders learning fractions for the first time. This aligns well with your learning objective of helping students understand fractions as parts of a whole.","severity":"info"}
```

**Insight Categories:**
- `equity` - Who's being called on, participation patterns
- `wait_time` - Pausing for thinking time
- `question_quality` - Purposefulness of questions
- `follow_up` - Quality of follow-up questions
- `engagement` - Student engagement patterns

**Severity Levels:**
- `info` - Positive observation, celebrate wins
- `suggestion` - Room for improvement
- `concern` - Important issue to address

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
const eventSource = new EventSource('http://localhost:8000/ask?stream_feedback=true', {
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
const response = await fetch('http://localhost:8000/ask?stream_feedback=true', {
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

### `POST /lesson/end`
End the practice session and receive comprehensive feedback on the entire lesson.

**Purpose:** Call this when the teacher is finished practicing. Analyzes the complete conversation transcript and provides detailed feedback, strengths, areas for growth, and actionable next steps.

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
    "participation_pattern": "Primarily called on students who raised hands. Chipper participated 3 times, Vex 2 times, Riven was not called on.",
    "key_moments": [
      "Teacher used concrete pizza example to introduce fractions",
      "Followed up with Chipper to deepen understanding of numerator/denominator",
      "Vex provided procedural explanation of how to write fractions"
    ]
  },
  "overall_feedback": "You facilitated a solid introductory lesson on fractions that aligned well with your 3rd grade learning objectives. Your use of the pizza example was developmentally appropriate and helped students visualize the concept. You successfully called on students who were confident and ready to share, which kept the lesson moving. There's opportunity to extend your questioning to include all three students, particularly Riven who never raised a hand but could benefit from scaffolded questions.",
  "strengths_and_growth": {
    "strengths": [
      "Used concrete, relatable examples (pizza) that align with 3rd grade developmental level",
      "Asked follow-up questions to deepen understanding, such as 'Can you give me an example?'",
      "Clear focus on learning objectives throughout the lesson",
      "Created a supportive environment where students felt comfortable sharing"
    ],
    "areas_for_growth": [
      "Equity in participation - Riven was never called on despite being present. Consider using strategies to engage students who don't raise hands.",
      "Question variety - Most questions were recall-based. Try incorporating more open-ended questions like 'Why do you think...?' or 'What would happen if...?'",
      "Probing for reasoning - When students gave correct answers, you could press them to explain their mathematical thinking more explicitly"
    ]
  },
  "next_steps": {
    "immediate_actions": [
      "In your next practice, intentionally call on a student who hasn't raised their hand and provide scaffolding",
      "Try asking at least one 'Why?' or 'How do you know?' question to press for mathematical reasoning",
      "Before the lesson, plan 2-3 questions at different complexity levels to differentiate for all learners"
    ],
    "practice_focus": "Focus on equity in participation - develop strategies to engage students with varying confidence levels",
    "resources": [
      "Read: 'Five Practices for Orchestrating Productive Mathematics Discussions' by Smith & Stein",
      "Strategy: Use think-pair-share to give all students processing time before calling on anyone"
    ]
  },
  "celebration": "Great work! You created a welcoming environment and kept the lesson focused on your learning goals. Your concrete examples really helped students grasp a tricky concept. With practice, you'll develop even more strategies to engage all learners. Keep up the thoughtful questioning! 🎉"
}
```

**Frontend Flow:**
1. Teacher completes practice lesson
2. Click "End Lesson" button
3. Frontend sends `POST /lesson/end` with lesson context and full transcript
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
    
    const response = await fetch('http://localhost:8000/lesson/end', {
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
 * @property {('equity'|'wait_time'|'question_quality'|'follow_up'|'engagement')} category
 * @property {string} message - Specific, actionable feedback
 * @property {('info'|'suggestion'|'concern')} severity
 */
```

### EndLessonRequest
```javascript
/**
 * @typedef {Object} EndLessonRequest
 * @property {LessonContext} lesson_context
 * @property {ConversationMessage[]} conversation_transcript - Complete lesson transcript
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

    const response = await fetch('http://localhost:8000/lesson/setup', {
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
    const response = await fetch('http://localhost:8000/ask/with-audio?stream_feedback=true', {
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
