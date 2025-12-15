"""
Question models for the Exam Grading Agent
"""
from enum import Enum
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field


class QuestionType(Enum):
    """Types of questions supported by the grading system"""
    MULTIPLE_CHOICE = "multiple_choice"
    SHORT_ANSWER = "short_answer"
    ESSAY = "essay"
    CODE = "code"
    NUMERICAL = "numerical"
    TRUE_FALSE = "true_false"


class DifficultyLevel(Enum):
    """Question difficulty levels"""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


@dataclass
class Question:
    """Represents a single exam question"""
    id: str
    text: str
    question_type: QuestionType
    points: float
    correct_answer: Any
    difficulty: DifficultyLevel = DifficultyLevel.MEDIUM
    topics: List[str] = field(default_factory=list)
    explanation: Optional[str] = None
    rubric: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # For MCQ questions
    options: Optional[List[str]] = None
    
    # For partial credit
    partial_credit_rules: Optional[Dict[str, float]] = None
    
    def __post_init__(self):
        """Validate question data"""
        if self.points <= 0:
            raise ValueError("Points must be positive")
        
        if self.question_type == QuestionType.MULTIPLE_CHOICE:
            if not self.options or len(self.options) < 2:
                raise ValueError("MCQ must have at least 2 options")


@dataclass
class Rubric:
    """Grading rubric for subjective questions"""
    criteria: Dict[str, Dict[str, Any]]
    total_points: float
    
    def __post_init__(self):
        """Validate rubric"""
        points_sum = sum(c.get('points', 0) for c in self.criteria.values())
        if abs(points_sum - self.total_points) > 0.01:
            raise ValueError("Rubric criteria points must sum to total_points")


@dataclass
class GradingConfig:
    """Configuration for grading behavior"""
    strictness: float = 0.7  # 0.0 (lenient) to 1.0 (strict)
    enable_partial_credit: bool = True
    semantic_matching: bool = True
    case_sensitive: bool = False
    ignore_whitespace: bool = True
    spelling_tolerance: float = 0.85  # Similarity threshold for spelling
    ai_grading_enabled: bool = True
    min_essay_length: int = 50  # Minimum words for essay
    code_execution: bool = False  # Execute code for validation