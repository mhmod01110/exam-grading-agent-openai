"""
Exam model for the Exam Grading Agent
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from .question import Question, GradingConfig


@dataclass
class Exam:
    """Represents a complete exam with questions and configuration"""
    id: str
    title: str
    description: str
    questions: List[Question]
    grading_config: GradingConfig = field(default_factory=GradingConfig)
    created_at: datetime = field(default_factory=datetime.now)
    subject: Optional[str] = None
    duration_minutes: Optional[int] = None
    passing_score: float = 60.0  # Percentage
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def total_points(self) -> float:
        """Calculate total points for the exam"""
        return sum(q.points for q in self.questions)
    
    @property
    def question_count(self) -> int:
        """Get total number of questions"""
        return len(self.questions)
    
    def get_question(self, question_id: str) -> Optional[Question]:
        """Get a specific question by ID"""
        for question in self.questions:
            if question.id == question_id:
                return question
        return None
    
    def get_questions_by_type(self, question_type) -> List[Question]:
        """Get all questions of a specific type"""
        return [q for q in self.questions if q.question_type == question_type]
    
    def get_questions_by_topic(self, topic: str) -> List[Question]:
        """Get all questions related to a topic"""
        return [q for q in self.questions if topic in q.topics]
    
    def validate(self) -> List[str]:
        """Validate exam structure and return any errors"""
        errors = []
        
        if not self.questions:
            errors.append("Exam must have at least one question")
        
        question_ids = set()
        for q in self.questions:
            if q.id in question_ids:
                errors.append(f"Duplicate question ID: {q.id}")
            question_ids.add(q.id)
        
        if self.passing_score < 0 or self.passing_score > 100:
            errors.append("Passing score must be between 0 and 100")
        
        return errors