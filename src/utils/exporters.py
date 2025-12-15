"""
Export grading results to various formats
"""
import json
import csv
from typing import List
from datetime import datetime
from pathlib import Path

from ..models.submission import ExamResult
from ..models.exam import Exam


class ResultExporter:
    """Export exam results to different formats"""
    
    @staticmethod
    def to_json(results: List[ExamResult], filepath: str) -> None:
        """Export results to JSON file"""
        data = [
            {
                'student_id': r.student_id,
                'student_name': r.student_name,
                'exam_id': r.exam_id,
                'total_score': r.total_points_earned,
                'max_score': r.total_points_possible,
                'percentage': r.percentage_score,
                'grade': r.grade_letter,
                'graded_at': r.graded_at.isoformat(),
                'question_results': [
                    {
                        'question_id': qr.question_id,
                        'points_earned': qr.points_earned,
                        'points_possible': qr.points_possible,
                        'is_correct': qr.is_correct,
                        'feedback': qr.feedback
                    }
                    for qr in r.question_results
                ]
            }
            for r in results
        ]
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    @staticmethod
    def to_csv(results: List[ExamResult], filepath: str) -> None:
        """Export results summary to CSV file"""
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Header
            writer.writerow([
                'Student ID',
                'Student Name',
                'Total Score',
                'Max Score',
                'Percentage',
                'Grade',
                'Graded At'
            ])
            
            # Data rows
            for result in results:
                writer.writerow([
                    result.student_id,
                    result.student_name,
                    f"{result.total_points_earned:.2f}",
                    f"{result.total_points_possible:.2f}",
                    f"{result.percentage_score:.2f}",
                    result.grade_letter,
                    result.graded_at.strftime('%Y-%m-%d %H:%M:%S')
                ])
    
    @staticmethod
    def to_detailed_csv(results: List[ExamResult], exam: Exam, filepath: str) -> None:
        """Export detailed results with per-question scores to CSV"""
        if not results:
            return
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Build header
            header = ['Student ID', 'Student Name']
            for question in exam.questions:
                header.append(f"Q{question.id}")
            header.extend(['Total Score', 'Percentage', 'Grade'])
            
            writer.writerow(header)
            
            # Data rows
            for result in results:
                row = [result.student_id, result.student_name]
                
                for question in exam.questions:
                    q_result = result.get_question_result(question.id)
                    if q_result:
                        row.append(f"{q_result.points_earned:.1f}/{q_result.points_possible:.1f}")
                    else:
                        row.append("0/0")
                
                row.extend([
                    f"{result.total_points_earned:.2f}",
                    f"{result.percentage_score:.2f}",
                    result.grade_letter
                ])
                
                writer.writerow(row)
    
    @staticmethod
    def to_individual_report(result: ExamResult, exam: Exam, filepath: str) -> None:
        """Generate individual student report as text file"""
        lines = []
        
        lines.append("=" * 80)
        lines.append(f"EXAM RESULTS REPORT")
        lines.append("=" * 80)
        lines.append("")
        
        lines.append(f"Student: {result.student_name} (ID: {result.student_id})")
        lines.append(f"Exam: {exam.title}")
        lines.append(f"Date: {result.graded_at.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        
        lines.append("-" * 80)
        lines.append("OVERALL PERFORMANCE")
        lines.append("-" * 80)
        lines.append(f"Score: {result.total_points_earned:.2f} / {result.total_points_possible:.2f}")
        lines.append(f"Percentage: {result.percentage_score:.2f}%")
        lines.append(f"Grade: {result.grade_letter}")
        lines.append("")
        
        if result.overall_feedback:
            lines.append("OVERALL FEEDBACK:")
            lines.append(result.overall_feedback)
            lines.append("")
        
        lines.append("-" * 80)
        lines.append("QUESTION-BY-QUESTION BREAKDOWN")
        lines.append("-" * 80)
        lines.append("")
        
        for i, q_result in enumerate(result.question_results, 1):
            question = exam.get_question(q_result.question_id)
            
            lines.append(f"Question {i} (ID: {q_result.question_id})")
            if question:
                lines.append(f"Type: {question.question_type.value}")
                lines.append(f"Question: {question.text}")
            
            lines.append(f"Your Answer: {q_result.student_answer}")
            lines.append(f"Score: {q_result.points_earned:.2f} / {q_result.points_possible:.2f}")
            lines.append(f"Status: {'✓ Correct' if q_result.is_correct else '✗ Incorrect'}")
            lines.append("")
            
            lines.append("Feedback:")
            lines.append(q_result.feedback)
            
            if q_result.suggestions:
                lines.append("")
                lines.append("Suggestions for Improvement:")
                for suggestion in q_result.suggestions:
                    lines.append(f"  • {suggestion}")
            
            lines.append("")
            lines.append("-" * 80)
            lines.append("")
        
        lines.append("=" * 80)
        lines.append("END OF REPORT")
        lines.append("=" * 80)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))
    
    @staticmethod
    def generate_all_reports(
        results: List[ExamResult],
        exam: Exam,
        output_dir: str = "exam_results"
    ) -> None:
        """Generate all export formats"""
        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        exam_name = exam.id.replace(" ", "_")
        
        # Export summary files
        ResultExporter.to_json(
            results,
            str(output_path / f"{exam_name}_results_{timestamp}.json")
        )
        
        ResultExporter.to_csv(
            results,
            str(output_path / f"{exam_name}_summary_{timestamp}.csv")
        )
        
        ResultExporter.to_detailed_csv(
            results,
            exam,
            str(output_path / f"{exam_name}_detailed_{timestamp}.csv")
        )
        
        # Create individual reports directory
        individual_dir = output_path / f"{exam_name}_individual_reports_{timestamp}"
        individual_dir.mkdir(exist_ok=True)
        
        # Generate individual reports
        for result in results:
            safe_name = result.student_name.replace(" ", "_")
            ResultExporter.to_individual_report(
                result,
                exam,
                str(individual_dir / f"{safe_name}_{result.student_id}.txt")
            )
        
        print(f"All reports generated in: {output_path}")