"""Models package - organized by component."""

# Shared domain models
from .domain import (
    StudentProfile,
    StudentTraits,
    HandRaisingCriteria,
    ConversationMessage,
    VoiceSettings,
)

# Lesson Analyzer
from .lesson_analyzer import (
    LessonSetupRequest,
    LessonContext,
    StudentApproach,
    LessonAnalysisOutput,
    StudentApproachOutput,
)

# Student Agent
from .student_agent import (
    TeacherPromptRequest,
    StudentResponse,
    MultiStudentResponse,
)

# Feedback Agent
from .feedback_agent import (
    FeedbackContext,
    FeedbackInsight,
    TeacherFeedback,
)

# Lesson Summary Agent
from .lesson_summary_agent import (
    EndLessonRequest,
    EndLessonResponse,
    LessonSummary,
    StrengthsAndGrowth,
    NextSteps,
    LessonSummaryOutput,
    LessonSummaryDetail,
    StrengthsAndGrowthOutput,
    NextStepsOutput,
)

__all__ = [
    # Domain
    "StudentProfile",
    "StudentTraits",
    "HandRaisingCriteria",
    "ConversationMessage",
    "VoiceSettings",
    # Lesson Analyzer
    "LessonSetupRequest",
    "LessonContext",
    "StudentApproach",
    "LessonAnalysisOutput",
    "StudentApproachOutput",
    # Student Agent
    "TeacherPromptRequest",
    "StudentResponse",
    "MultiStudentResponse",
    # Feedback Agent
    "FeedbackContext",
    "FeedbackInsight",
    "TeacherFeedback",
    # Lesson Summary Agent
    "EndLessonRequest",
    "EndLessonResponse",
    "LessonSummary",
    "StrengthsAndGrowth",
    "NextSteps",
    "LessonSummaryOutput",
    "LessonSummaryDetail",
    "StrengthsAndGrowthOutput",
    "NextStepsOutput",
]
