"""
Analytics and reporting for exam results
"""
from typing import List, Dict, Any
from collections import defaultdict
import statistics

from ..models.submission import ExamResult
from ..models.exam import Exam


class ExamAnalytics:
    """Analyzes exam results across multiple students"""
    
    def __init__(self, exam: Exam, results: List[ExamResult]):
        """
        Initialize analytics with exam and results
        
        Args:
            exam: The exam definition
            results: List of graded exam results
        """
        self.exam = exam
        self.results = results
    
    def get_class_statistics(self) -> Dict[str, Any]:
        """Get overall class statistics"""
        if not self.results:
            return {}
        
        scores = [r.percentage_score for r in self.results]
        total_points = [r.total_points_earned for r in self.results]
        
        return {
            'student_count': len(self.results),
            'mean_score': statistics.mean(scores),
            'median_score': statistics.median(scores),
            'std_dev': statistics.stdev(scores) if len(scores) > 1 else 0,
            'min_score': min(scores),
            'max_score': max(scores),
            'mean_points': statistics.mean(total_points),
            'passing_count': sum(1 for s in scores if s >= self.exam.passing_score),
            'passing_rate': sum(1 for s in scores if s >= self.exam.passing_score) / len(scores) * 100
        }
    
    def get_grade_distribution(self) -> Dict[str, int]:
        """Get distribution of letter grades"""
        distribution = defaultdict(int)
        
        for result in self.results:
            distribution[result.grade_letter] += 1
        
        return dict(distribution)
    
    def get_question_statistics(self) -> List[Dict[str, Any]]:
        """Analyze performance on each question"""
        question_stats = []
        
        for question in self.exam.questions:
            # Collect results for this question
            correct_count = 0
            total_points_earned = 0.0
            student_count = 0
            
            for result in self.results:
                q_result = result.get_question_result(question.id)
                if q_result:
                    student_count += 1
                    if q_result.is_correct:
                        correct_count += 1
                    total_points_earned += q_result.points_earned
            
            if student_count > 0:
                accuracy = correct_count / student_count * 100
                avg_points = total_points_earned / student_count
                
                # Determine difficulty based on accuracy
                actual_difficulty = "Easy" if accuracy > 80 else \
                                   "Medium" if accuracy > 50 else "Hard"
                
                question_stats.append({
                    'question_id': question.id,
                    'question_text': question.text[:100] + '...' if len(question.text) > 100 else question.text,
                    'question_type': question.question_type.value,
                    'expected_difficulty': question.difficulty.value,
                    'actual_difficulty': actual_difficulty,
                    'accuracy': accuracy,
                    'average_points': avg_points,
                    'max_points': question.points,
                    'students_attempted': student_count,
                    'students_correct': correct_count
                })
        
        # Sort by accuracy (hardest questions first)
        question_stats.sort(key=lambda x: x['accuracy'])
        
        return question_stats
    
    def get_common_mistakes(self, top_n: int = 5) -> List[Dict[str, Any]]:
        """Identify most commonly missed questions"""
        question_stats = self.get_question_statistics()
        
        # Get questions with lowest accuracy
        mistakes = []
        for stat in question_stats[:top_n]:
            if stat['accuracy'] < 80:  # Only include if < 80% got it right
                mistakes.append({
                    'question_id': stat['question_id'],
                    'question_text': stat['question_text'],
                    'accuracy': stat['accuracy'],
                    'students_missed': stat['students_attempted'] - stat['students_correct']
                })
        
        return mistakes
    
    def get_top_performers(self, top_n: int = 5) -> List[Dict[str, Any]]:
        """Get top performing students"""
        sorted_results = sorted(
            self.results,
            key=lambda r: r.percentage_score,
            reverse=True
        )
        
        return [
            {
                'student_id': r.student_id,
                'student_name': r.student_name,
                'score': r.percentage_score,
                'grade': r.grade_letter,
                'points': f"{r.total_points_earned:.1f}/{r.total_points_possible}"
            }
            for r in sorted_results[:top_n]
        ]
    
    def get_performance_by_topic(self) -> Dict[str, Dict[str, float]]:
        """Analyze performance by topic/subject area"""
        topic_stats = defaultdict(lambda: {'correct': 0, 'total': 0, 'points_earned': 0, 'points_possible': 0})
        
        for question in self.exam.questions:
            for topic in question.topics:
                for result in self.results:
                    q_result = result.get_question_result(question.id)
                    if q_result:
                        topic_stats[topic]['total'] += 1
                        if q_result.is_correct:
                            topic_stats[topic]['correct'] += 1
                        topic_stats[topic]['points_earned'] += q_result.points_earned
                        topic_stats[topic]['points_possible'] += q_result.points_possible
        
        # Calculate percentages
        return {
            topic: {
                'accuracy': stats['correct'] / stats['total'] * 100 if stats['total'] > 0 else 0,
                'average_score': stats['points_earned'] / stats['points_possible'] * 100 if stats['points_possible'] > 0 else 0,
                'questions_count': stats['total'] // len(self.results) if self.results else 0
            }
            for topic, stats in topic_stats.items()
        }
    
    def generate_report(self) -> str:
        """Generate a comprehensive text report"""
        lines = []
        lines.append("=" * 80)
        lines.append(f"EXAM ANALYSIS REPORT: {self.exam.title}")
        lines.append("=" * 80)
        lines.append("")
        
        # Class Statistics
        lines.append("CLASS STATISTICS")
        lines.append("-" * 80)
        stats = self.get_class_statistics()
        lines.append(f"Total Students: {stats.get('student_count', 0)}")
        lines.append(f"Mean Score: {stats.get('mean_score', 0):.2f}%")
        lines.append(f"Median Score: {stats.get('median_score', 0):.2f}%")
        lines.append(f"Standard Deviation: {stats.get('std_dev', 0):.2f}")
        lines.append(f"Score Range: {stats.get('min_score', 0):.2f}% - {stats.get('max_score', 0):.2f}%")
        lines.append(f"Passing Rate: {stats.get('passing_rate', 0):.2f}% ({stats.get('passing_count', 0)} students)")
        lines.append("")
        
        # Grade Distribution
        lines.append("GRADE DISTRIBUTION")
        lines.append("-" * 80)
        distribution = self.get_grade_distribution()
        for grade in ['A', 'B', 'C', 'D', 'F']:
            count = distribution.get(grade, 0)
            bar = '█' * count
            lines.append(f"{grade}: {bar} ({count})")
        lines.append("")
        
        # Question Analysis
        lines.append("QUESTION ANALYSIS")
        lines.append("-" * 80)
        question_stats = self.get_question_statistics()
        for i, stat in enumerate(question_stats[:10], 1):  # Top 10 hardest
            lines.append(f"{i}. Q{stat['question_id']}: {stat['accuracy']:.1f}% accuracy")
            lines.append(f"   Type: {stat['question_type']}, Difficulty: {stat['actual_difficulty']}")
            lines.append(f"   {stat['students_correct']}/{stat['students_attempted']} students correct")
            lines.append("")
        
        # Common Mistakes
        lines.append("MOST COMMONLY MISSED QUESTIONS")
        lines.append("-" * 80)
        mistakes = self.get_common_mistakes()
        for i, mistake in enumerate(mistakes, 1):
            lines.append(f"{i}. {mistake['question_text']}")
            lines.append(f"   Only {mistake['accuracy']:.1f}% correct ({mistake['students_missed']} missed)")
            lines.append("")
        
        # Topic Performance
        topic_perf = self.get_performance_by_topic()
        if topic_perf:
            lines.append("PERFORMANCE BY TOPIC")
            lines.append("-" * 80)
            for topic, perf in sorted(topic_perf.items(), key=lambda x: x[1]['accuracy']):
                lines.append(f"{topic}: {perf['accuracy']:.1f}% accuracy")
                lines.append(f"   Average Score: {perf['average_score']:.1f}%")
                lines.append("")
        
        # Top Performers
        lines.append("TOP PERFORMERS")
        lines.append("-" * 80)
        top = self.get_top_performers()
        for i, student in enumerate(top, 1):
            lines.append(f"{i}. {student['student_name']}: {student['score']:.2f}% ({student['grade']})")
        
        lines.append("")
        lines.append("=" * 80)
        
        return "\n".join(lines)