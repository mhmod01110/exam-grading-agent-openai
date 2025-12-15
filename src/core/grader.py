"""
Main exam grading engine
"""
from typing import List, Optional
from datetime import datetime

from ..models.exam import Exam
from ..models.submission import StudentSubmission, GradingResult, ExamResult
from ..models.question import QuestionType
from ..ai.openai_client import OpenAIGradingClient
from .evaluator import AnswerEvaluator


class ExamGrader:
    """Main grading engine that coordinates evaluation and AI grading"""
    
    def __init__(self, exam: Exam, api_key: Optional[str] = None):
        """
        Initialize grader with exam and optional API key
        
        Args:
            exam: The exam to grade submissions against
            api_key: Anthropic API key (optional, can use env var)
        """
        self.exam = exam
        self.evaluator = AnswerEvaluator(exam.grading_config)
        
        # Initialize AI client if enabled
        self.ai_client = None
        if exam.grading_config.ai_grading_enabled:
            try:
                self.ai_client = OpenAIGradingClient(api_key)
            except ValueError:
                print("Warning: AI grading disabled - no API key provided")
    
    def grade_submission(
        self,
        submission: StudentSubmission,
        use_ai: Optional[bool] = None
    ) -> ExamResult:
        """
        Grade a complete student submission
        
        Args:
            submission: Student's exam submission
            use_ai: Override exam config for AI usage (None = use config)
        
        Returns:
            Complete exam results with feedback
        """
        # Determine if we should use AI
        use_ai_grading = use_ai if use_ai is not None else \
                        self.exam.grading_config.ai_grading_enabled
        
        if use_ai_grading and not self.ai_client:
            print("Warning: AI grading requested but client not available")
            use_ai_grading = False
        
        # Grade each question
        question_results = []
        
        for question in self.exam.questions:
            answer = submission.get_answer(question.id)
            
            if answer is None:
                # Question not answered
                result = GradingResult(
                    question_id=question.id,
                    student_answer=None,
                    correct_answer=question.correct_answer,
                    points_earned=0.0,
                    points_possible=question.points,
                    is_correct=False,
                    feedback="Question not answered"
                )
            else:
                # Grade the answer
                result = self._grade_single_answer(
                    question,
                    answer.response,
                    use_ai_grading
                )
            
            question_results.append(result)
        
        # Calculate totals
        total_earned = sum(r.points_earned for r in question_results)
        total_possible = self.exam.total_points
        
        # Generate overall feedback
        overall_feedback = self._generate_overall_feedback(
            submission,
            question_results,
            total_earned,
            total_possible,
            use_ai_grading
        )
        
        # Create analytics
        analytics = self._generate_analytics(question_results)
        
        return ExamResult(
            student_id=submission.student_id,
            student_name=submission.student_name,
            exam_id=self.exam.id,
            question_results=question_results,
            total_points_earned=total_earned,
            total_points_possible=total_possible,
            overall_feedback=overall_feedback,
            analytics=analytics
        )
    
    def _grade_single_answer(
        self,
        question,
        student_answer,
        use_ai: bool
    ) -> GradingResult:
        """Grade a single answer"""
        
        # Determine if this question type requires AI
        ai_required_types = {
            QuestionType.ESSAY,
            QuestionType.CODE
        }
        
        needs_ai = question.question_type in ai_required_types
        
        # Start with basic evaluation
        points, is_correct, basic_feedback = self.evaluator.evaluate(
            question,
            student_answer
        )
        
        # Use AI for detailed grading if needed and available
        if use_ai and (needs_ai or not is_correct):
            try:
                ai_result = self.ai_client.grade_answer(
                    question_text=question.text,
                    correct_answer=question.correct_answer,
                    student_answer=student_answer,
                    question_type=question.question_type.value,
                    points_possible=question.points,
                    rubric=question.rubric,
                    strictness=self.exam.grading_config.strictness
                )
                
                # Use AI grading results
                points = ai_result.get('points_earned', points)
                is_correct = ai_result.get('is_correct', is_correct)
                feedback = ai_result.get('feedback', basic_feedback)
                analysis = ai_result.get('analysis', {})
                suggestions = ai_result.get('suggestions', [])
                
                return GradingResult(
                    question_id=question.id,
                    student_answer=student_answer,
                    correct_answer=question.correct_answer,
                    points_earned=points,
                    points_possible=question.points,
                    is_correct=is_correct,
                    feedback=feedback,
                    detailed_analysis=analysis,
                    suggestions=suggestions
                )
            
            except Exception as e:
                print(f"AI grading failed for question {question.id}: {e}")
                # Fall back to basic evaluation
        
        return GradingResult(
            question_id=question.id,
            student_answer=student_answer,
            correct_answer=question.correct_answer,
            points_earned=points,
            points_possible=question.points,
            is_correct=is_correct,
            feedback=basic_feedback
        )
    
    def _generate_overall_feedback(
            self,
            submission: StudentSubmission,
            results: List[GradingResult],
            total_earned: float,
            total_possible: float,
            use_ai: bool
        ) -> str:
            """Generate overall feedback for the exam in HTML format"""
            
            percentage = (total_earned / total_possible * 100) if total_possible > 0 else 0
            
            # 1. Determine grade styling and text
            grade_class = "grade-fail"
            performance_text = "Additional study recommended."
            
            if percentage >= 90:
                grade_class = "grade-excellent" 
                performance_text = "🌟 Excellent work!"
            elif percentage >= 80:
                grade_class = "grade-good"      
                performance_text = "👍 Good job!"
            elif percentage >= 70:
                grade_class = "grade-average"   
                performance_text = "Satisfactory performance."
            elif percentage >= 60:
                grade_class = "grade-pass"      
                performance_text = "Passing, but there's room for improvement."

            # 2. Build the Header HTML
            html_parts = []
            
            html_parts.append(f"""
            <div class="result-summary {grade_class}">
                <div class="score-header">
                    <h3>Overall Performance</h3>
                    <div class="score-large">
                        {total_earned:.1f} <span class="text-muted">/ {total_possible:.1f}</span>
                    </div>
                    <div class="percentage-badge">{percentage:.1f}%</div>
                </div>
                <div class="performance-text">
                    <strong>{performance_text}</strong>
                </div>
            </div>
            """)

            # 3. Add Quick Stats
            correct_count = sum(1 for r in results if r.is_correct)
            total_questions = len(results)
            
            html_parts.append(f"""
            <div class="stats-bar">
                <div class="stat-item">
                    <span class="icon">✅</span>
                    <span>Correct: <strong>{correct_count}/{total_questions}</strong></span>
                </div>
                <div class="stat-item">
                    <span class="icon">📊</span>
                    <span>Accuracy: <strong>{(correct_count/total_questions*100):.0f}%</strong></span>
                </div>
            </div>
            """)
            
            # 4. Generate and Format AI Feedback
            if use_ai and self.ai_client:
                try:
                    # Prepare simplified results for AI context
                    simple_results = [
                        {
                            "question_id": r.question_id,
                            "correct": r.is_correct,
                            "score": f"{r.points_earned}/{r.points_possible}"
                        }
                        for r in results
                    ]
                    
                    ai_feedback_text = self.ai_client.generate_overall_feedback(
                        exam_title=self.exam.title,
                        total_score=total_earned,
                        max_score=total_possible,
                        question_results=simple_results
                    )
                    
                    # --- FORMATTING UPDATES HERE ---
                    formatted_feedback = ai_feedback_text
                    
                    # 1. Replace **text** with <strong>text</strong> (Basic regex replacement)
                    import re
                    formatted_feedback = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', formatted_feedback)
                    
                    # 2. Convert bullet points
                    formatted_feedback = formatted_feedback.replace("- ", "<br>• ")
                    
                    # 3. Convert newlines to breaks
                    formatted_feedback = formatted_feedback.replace("\n", "<br>")
                    
                    html_parts.append(f"""
                    <div class="ai-feedback-container">
                        <h4>🤖 AI Analysis & Recommendations</h4>
                        <div class="ai-content">
                            {formatted_feedback}
                        </div>
                    </div>
                    """)
                
                except Exception as e:
                    print(f"Failed to generate AI feedback: {e}")
                    html_parts.append('<div class="alert alert-warning">AI Feedback unavailable at this time.</div>')
            
            return "\n".join(html_parts)
    
    def _generate_analytics(self, results: List[GradingResult]) -> dict:
        """Generate analytics from grading results"""
        
        total_questions = len(results)
        correct_answers = sum(1 for r in results if r.is_correct)
        
        # Performance by question type
        type_performance = {}
        for result in results:
            question = self.exam.get_question(result.question_id)
            if question:
                q_type = question.question_type.value
                if q_type not in type_performance:
                    type_performance[q_type] = {
                        'total': 0,
                        'correct': 0,
                        'points_earned': 0.0,
                        'points_possible': 0.0
                    }
                
                type_performance[q_type]['total'] += 1
                type_performance[q_type]['correct'] += 1 if result.is_correct else 0
                type_performance[q_type]['points_earned'] += result.points_earned
                type_performance[q_type]['points_possible'] += result.points_possible
        
        return {
            'total_questions': total_questions,
            'correct_answers': correct_answers,
            'accuracy': correct_answers / total_questions if total_questions > 0 else 0,
            'performance_by_type': type_performance
        }
    
    def grade_multiple_submissions(
        self,
        submissions: List[StudentSubmission],
        use_ai: Optional[bool] = None
    ) -> List[ExamResult]:
        """
        Grade multiple student submissions
        
        Args:
            submissions: List of student submissions
            use_ai: Override exam config for AI usage
        
        Returns:
            List of exam results
        """
        results = []
        
        for i, submission in enumerate(submissions, 1):
            print(f"Grading submission {i}/{len(submissions)} for {submission.student_name}...")
            result = self.grade_submission(submission, use_ai)
            results.append(result)
        
        return results