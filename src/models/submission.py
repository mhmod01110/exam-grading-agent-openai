"""
Student submission models for the Exam Grading Agent
"""
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from datetime import datetime


@dataclass
class Answer:
    """Represents a student's answer to a question"""
    question_id: str
    response: Any
    time_spent: Optional[int] = None  # seconds
    attempt_number: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StudentSubmission:
    """Represents a complete student exam submission"""
    student_id: str
    student_name: str
    exam_id: str
    answers: List[Answer]
    submitted_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_answer(self, question_id: str) -> Optional[Answer]:
        """Get answer for a specific question"""
        for answer in self.answers:
            if answer.question_id == question_id:
                return answer
        return None


@dataclass
class GradingResult:
    """Result of grading a single answer"""
    question_id: str
    student_answer: Any
    correct_answer: Any
    points_earned: float
    points_possible: float
    is_correct: bool
    feedback: str
    detailed_analysis: Optional[Dict[str, Any]] = None
    suggestions: List[str] = field(default_factory=list)
    
    @property
    def percentage(self) -> float:
        """Calculate percentage score"""
        if self.points_possible == 0:
            return 0.0
        return (self.points_earned / self.points_possible) * 100


@dataclass
class ExamResult:
    """Complete exam grading result for a student"""
    student_id: str
    student_name: str
    exam_id: str
    question_results: List[GradingResult]
    total_points_earned: float
    total_points_possible: float
    graded_at: datetime = field(default_factory=datetime.now)
    overall_feedback: str = ""
    analytics: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def percentage_score(self) -> float:
        """Calculate overall percentage"""
        if self.total_points_possible == 0:
            return 0.0
        return (self.total_points_earned / self.total_points_possible) * 100
    
    @property
    def grade_letter(self) -> str:
        """Convert percentage to letter grade"""
        pct = self.percentage_score
        if pct >= 90:
            return "A"
        elif pct >= 80:
            return "B"
        elif pct >= 70:
            return "C"
        elif pct >= 60:
            return "D"
        else:
            return "F"
    
    def get_question_result(self, question_id: str) -> Optional[GradingResult]:
        """Get result for a specific question"""
        for result in self.question_results:
            if result.question_id == question_id:
                return result
        return None