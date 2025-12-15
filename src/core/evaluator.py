"""
Answer evaluation logic for different question types
"""
import re
from typing import Any, Tuple
from difflib import SequenceMatcher
from ..models.question import QuestionType, Question, GradingConfig


class AnswerEvaluator:
    """Evaluates student answers against correct answers"""
    
    def __init__(self, config: GradingConfig):
        self.config = config
    
    def evaluate(
        self,
        question: Question,
        student_answer: Any
    ) -> Tuple[float, bool, str]:
        """
        Evaluate a student answer
        
        Returns:
            Tuple of (points_earned, is_correct, basic_feedback)
        """
        if student_answer is None or student_answer == "":
            return 0.0, False, "No answer provided"
        
        # Route to appropriate evaluator based on question type
        evaluators = {
            QuestionType.MULTIPLE_CHOICE: self._evaluate_mcq,
            QuestionType.TRUE_FALSE: self._evaluate_true_false,
            QuestionType.NUMERICAL: self._evaluate_numerical,
            QuestionType.SHORT_ANSWER: self._evaluate_short_answer,
            QuestionType.ESSAY: self._evaluate_essay,
            QuestionType.CODE: self._evaluate_code,
        }
        
        evaluator = evaluators.get(question.question_type)
        if not evaluator:
            return 0.0, False, f"Unknown question type: {question.question_type}"
        
        return evaluator(question, student_answer)
    
    def _evaluate_mcq(
        self,
        question: Question,
        student_answer: Any
    ) -> Tuple[float, bool, str]:
        """Evaluate multiple choice question"""
        correct = str(question.correct_answer).strip()
        student = str(student_answer).strip()
        
        if not self.config.case_sensitive:
            correct = correct.lower()
            student = student.lower()
        
        is_correct = correct == student
        points = question.points if is_correct else 0.0
        
        feedback = "Correct!" if is_correct else \
                   f"Incorrect. The correct answer is: {question.correct_answer}"
        
        return points, is_correct, feedback
    
    def _evaluate_true_false(
        self,
        question: Question,
        student_answer: Any
    ) -> Tuple[float, bool, str]:
        """Evaluate true/false question"""
        # Normalize answers
        true_values = {"true", "t", "yes", "y", "1", "correct"}
        false_values = {"false", "f", "no", "n", "0", "incorrect"}
        
        student = str(student_answer).strip().lower()
        correct = str(question.correct_answer).strip().lower()
        
        # Normalize correct answer
        if correct in true_values:
            correct_bool = True
        elif correct in false_values:
            correct_bool = False
        else:
            return 0.0, False, "Invalid correct answer format"
        
        # Normalize student answer
        if student in true_values:
            student_bool = True
        elif student in false_values:
            student_bool = False
        else:
            return 0.0, False, "Invalid answer format. Please answer True or False"
        
        is_correct = correct_bool == student_bool
        points = question.points if is_correct else 0.0
        
        feedback = "Correct!" if is_correct else \
                   f"Incorrect. The correct answer is: {question.correct_answer}"
        
        return points, is_correct, feedback
    
    def _evaluate_numerical(
        self,
        question: Question,
        student_answer: Any
    ) -> Tuple[float, bool, str]:
        """Evaluate numerical answer with tolerance"""
        try:
            correct = float(question.correct_answer)
            student = float(student_answer)
            
            # Use 1% tolerance by default or from question metadata
            tolerance = question.metadata.get('tolerance', 0.01)
            diff = abs(correct - student)
            tolerance_value = abs(correct * tolerance)
            
            is_correct = diff <= tolerance_value
            
            if is_correct:
                points = question.points
                feedback = "Correct!"
            elif diff <= tolerance_value * 2 and self.config.enable_partial_credit:
                # Partial credit for close answers
                points = question.points * 0.5
                feedback = f"Close! The exact answer is {correct}"
            else:
                points = 0.0
                feedback = f"Incorrect. The correct answer is: {correct}"
            
            return points, is_correct, feedback
        
        except (ValueError, TypeError):
            return 0.0, False, "Invalid numerical format"
    
    def _evaluate_short_answer(
        self,
        question: Question,
        student_answer: Any
    ) -> Tuple[float, bool, str]:
        """Evaluate short answer with fuzzy matching"""
        correct = str(question.correct_answer).strip()
        student = str(student_answer).strip()
        
        if self.config.ignore_whitespace:
            correct = " ".join(correct.split())
            student = " ".join(student.split())
        
        if not self.config.case_sensitive:
            correct = correct.lower()
            student = student.lower()
        
        # Exact match
        if correct == student:
            return question.points, True, "Correct!"
        
        # Check for keyword matching if partial credit enabled
        if self.config.enable_partial_credit:
            similarity = self._calculate_similarity(correct, student)
            
            if similarity >= 0.95:
                return question.points, True, "Correct!"
            elif similarity >= self.config.spelling_tolerance:
                points = question.points * 0.8
                return points, False, \
                       "Mostly correct, minor differences from expected answer"
            elif similarity >= 0.6:
                points = question.points * 0.5
                return points, False, \
                       "Partially correct, but missing key elements"
        
        return 0.0, False, f"Incorrect. Expected: {question.correct_answer}"
    
    def _evaluate_essay(
        self,
        question: Question,
        student_answer: Any
    ) -> Tuple[float, bool, str]:
        """Basic essay evaluation (requires AI for full grading)"""
        student_text = str(student_answer).strip()
        word_count = len(student_text.split())
        
        if word_count < self.config.min_essay_length:
            return 0.0, False, \
                   f"Answer too short. Minimum {self.config.min_essay_length} words required"
        
        # Basic checks - AI grading will provide full evaluation
        return question.points * 0.5, False, \
               "Essay submitted. Detailed grading requires AI evaluation"
    
    def _evaluate_code(
        self,
        question: Question,
        student_answer: Any
    ) -> Tuple[float, bool, str]:
        """Basic code evaluation (syntax check only)"""
        student_code = str(student_answer).strip()
        
        if len(student_code) < 10:
            return 0.0, False, "Code submission too short"
        
        # Basic syntax check for Python
        try:
            compile(student_code, '<string>', 'exec')
            return question.points * 0.3, False, \
                   "Code syntax valid. Full evaluation requires execution"
        except SyntaxError as e:
            return 0.0, False, f"Syntax error: {str(e)}"
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity ratio between two texts"""
        return SequenceMatcher(None, text1, text2).ratio()