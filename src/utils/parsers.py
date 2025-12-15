"""
Parse input files for exams and submissions
"""
import json
import csv
from typing import List, Dict, Any
from datetime import datetime

from ..models.exam import Exam
from ..models.question import Question, QuestionType, DifficultyLevel, GradingConfig
from ..models.submission import StudentSubmission, Answer


class ExamParser:
    """Parse exam definitions from various formats"""
    
    @staticmethod
    def from_json(filepath: str) -> Exam:
        """Load exam from JSON file"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Parse questions
        questions = []
        for q_data in data.get('questions', []):
            question = Question(
                id=q_data['id'],
                text=q_data['text'],
                question_type=QuestionType(q_data['type']),
                points=float(q_data['points']),
                correct_answer=q_data['correct_answer'],
                difficulty=DifficultyLevel(q_data.get('difficulty', 'medium')),
                topics=q_data.get('topics', []),
                explanation=q_data.get('explanation'),
                rubric=q_data.get('rubric'),
                options=q_data.get('options'),
                partial_credit_rules=q_data.get('partial_credit_rules'),
                metadata=q_data.get('metadata', {})
            )
            questions.append(question)
        
        # Parse grading config
        config_data = data.get('grading_config', {})
        grading_config = GradingConfig(
            strictness=config_data.get('strictness', 0.7),
            enable_partial_credit=config_data.get('enable_partial_credit', True),
            semantic_matching=config_data.get('semantic_matching', True),
            case_sensitive=config_data.get('case_sensitive', False),
            ignore_whitespace=config_data.get('ignore_whitespace', True),
            spelling_tolerance=config_data.get('spelling_tolerance', 0.85),
            ai_grading_enabled=config_data.get('ai_grading_enabled', True),
            min_essay_length=config_data.get('min_essay_length', 50)
        )
        
        # Create exam
        exam = Exam(
            id=data['id'],
            title=data['title'],
            description=data['description'],
            questions=questions,
            grading_config=grading_config,
            subject=data.get('subject'),
            duration_minutes=data.get('duration_minutes'),
            passing_score=data.get('passing_score', 60.0),
            metadata=data.get('metadata', {})
        )
        
        return exam
    
    @staticmethod
    def to_json(exam: Exam, filepath: str) -> None:
        """Save exam to JSON file"""
        data = {
            'id': exam.id,
            'title': exam.title,
            'description': exam.description,
            'subject': exam.subject,
            'duration_minutes': exam.duration_minutes,
            'passing_score': exam.passing_score,
            'metadata': exam.metadata,
            'grading_config': {
                'strictness': exam.grading_config.strictness,
                'enable_partial_credit': exam.grading_config.enable_partial_credit,
                'semantic_matching': exam.grading_config.semantic_matching,
                'case_sensitive': exam.grading_config.case_sensitive,
                'ignore_whitespace': exam.grading_config.ignore_whitespace,
                'spelling_tolerance': exam.grading_config.spelling_tolerance,
                'ai_grading_enabled': exam.grading_config.ai_grading_enabled,
                'min_essay_length': exam.grading_config.min_essay_length
            },
            'questions': [
                {
                    'id': q.id,
                    'text': q.text,
                    'type': q.question_type.value,
                    'points': q.points,
                    'correct_answer': q.correct_answer,
                    'difficulty': q.difficulty.value,
                    'topics': q.topics,
                    'explanation': q.explanation,
                    'rubric': q.rubric,
                    'options': q.options,
                    'partial_credit_rules': q.partial_credit_rules,
                    'metadata': q.metadata
                }
                for q in exam.questions
            ]
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


class SubmissionParser:
    """Parse student submissions from various formats"""
    
    @staticmethod
    def from_json(filepath: str) -> List[StudentSubmission]:
        """Load submissions from JSON file"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        submissions = []
        
        for sub_data in data:
            answers = [
                Answer(
                    question_id=ans['question_id'],
                    response=ans['response'],
                    time_spent=ans.get('time_spent'),
                    attempt_number=ans.get('attempt_number', 1),
                    metadata=ans.get('metadata', {})
                )
                for ans in sub_data['answers']
            ]
            
            submission = StudentSubmission(
                student_id=sub_data['student_id'],
                student_name=sub_data['student_name'],
                exam_id=sub_data['exam_id'],
                answers=answers,
                submitted_at=datetime.fromisoformat(sub_data.get('submitted_at', datetime.now().isoformat())),
                metadata=sub_data.get('metadata', {})
            )
            
            submissions.append(submission)
        
        return submissions
    
    @staticmethod
    def from_csv(filepath: str, exam_id: str) -> List[StudentSubmission]:
        """
        Load submissions from CSV file
        
        Expected CSV format:
        student_id,student_name,q1_answer,q2_answer,...
        """
        submissions = []
        
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                student_id = row['student_id']
                student_name = row['student_name']
                
                # Extract answers (all columns except student info)
                answers = []
                for key, value in row.items():
                    if key.startswith('q') and '_answer' in key:
                        question_id = key.replace('_answer', '')
                        answers.append(Answer(
                            question_id=question_id,
                            response=value
                        ))
                
                submission = StudentSubmission(
                    student_id=student_id,
                    student_name=student_name,
                    exam_id=exam_id,
                    answers=answers
                )
                
                submissions.append(submission)
        
        return submissions
    
    @staticmethod
    def to_json(submissions: List[StudentSubmission], filepath: str) -> None:
        """Save submissions to JSON file"""
        data = [
            {
                'student_id': sub.student_id,
                'student_name': sub.student_name,
                'exam_id': sub.exam_id,
                'submitted_at': sub.submitted_at.isoformat(),
                'metadata': sub.metadata,
                'answers': [
                    {
                        'question_id': ans.question_id,
                        'response': ans.response,
                        'time_spent': ans.time_spent,
                        'attempt_number': ans.attempt_number,
                        'metadata': ans.metadata
                    }
                    for ans in sub.answers
                ]
            }
            for sub in submissions
        ]
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)