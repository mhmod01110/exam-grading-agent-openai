#!/usr/bin/env python3
"""
Exam Grading & Feedback Agent - Main Application
"""
import argparse
import sys
from pathlib import Path

from src.core.grader import ExamGrader
from src.analytics.analyzer import ExamAnalytics
from src.utils.parsers import ExamParser, SubmissionParser
from src.utils.exporters import ResultExporter
from config.settings import settings


def main():
    """Main application entry point"""
    parser = argparse.ArgumentParser(
        description="Exam Grading & Feedback Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Grade submissions with AI
  python main.py grade --exam exam.json --submissions submissions.json
  
  # Grade without AI (basic grading only)
  python main.py grade --exam exam.json --submissions submissions.json --no-ai
  
  # Generate analytics report
  python main.py analyze --exam exam.json --results results.json
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Grade command
    grade_parser = subparsers.add_parser('grade', help='Grade student submissions')
    grade_parser.add_argument('--exam', required=True, help='Path to exam JSON file')
    grade_parser.add_argument('--submissions', required=True, help='Path to submissions JSON file')
    grade_parser.add_argument('--output', default=None, help='Output directory for results')
    grade_parser.add_argument('--no-ai', action='store_true', help='Disable AI grading')
    grade_parser.add_argument('--api-key', default=None, help='Anthropic API key')
    
    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze grading results')
    analyze_parser.add_argument('--exam', required=True, help='Path to exam JSON file')
    analyze_parser.add_argument('--results', required=True, help='Path to results JSON file')
    analyze_parser.add_argument('--output', default=None, help='Output file for report')
    
    # Create example command
    example_parser = subparsers.add_parser('create-example', help='Create example exam and submissions')
    example_parser.add_argument('--output-dir', default='examples', help='Output directory')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    try:
        if args.command == 'grade':
            return grade_command(args)
        elif args.command == 'analyze':
            return analyze_command(args)
        elif args.command == 'create-example':
            return create_example_command(args)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    
    return 0


def grade_command(args):
    """Execute grading command"""
    print("=" * 80)
    print("EXAM GRADING & FEEDBACK AGENT")
    print("=" * 80)
    print()
    
    # Load exam
    print(f"Loading exam from: {args.exam}")
    exam = ExamParser.from_json(args.exam)
    print(f"✓ Loaded exam: {exam.title}")
    print(f"  - {exam.question_count} questions")
    print(f"  - Total points: {exam.total_points}")
    print()
    
    # Validate exam
    errors = exam.validate()
    if errors:
        print("Exam validation errors:")
        for error in errors:
            print(f"  ✗ {error}")
        return 1
    
    # Load submissions
    print(f"Loading submissions from: {args.submissions}")
    submissions = SubmissionParser.from_json(args.submissions)
    print(f"✓ Loaded {len(submissions)} submissions")
    print()
    
    # Check API key for AI grading
    use_ai = not args.no_ai
    if use_ai:
        api_key = args.api_key or settings.ANTHROPIC_API_KEY
        if not api_key:
            print("⚠ Warning: No API key provided, AI grading will be disabled")
            use_ai = False
        else:
            print("✓ AI grading enabled")
    else:
        print("ℹ AI grading disabled")
        api_key = None
    print()
    
    # Initialize grader
    print("Initializing grader...")
    grader = ExamGrader(exam, api_key=api_key)
    print()
    
    # Grade submissions
    print("Grading submissions...")
    print("-" * 80)
    results = grader.grade_multiple_submissions(submissions, use_ai=use_ai)
    print("-" * 80)
    print()
    
    # Print summary
    print("GRADING COMPLETE")
    print("-" * 80)
    for result in results:
        print(f"{result.student_name}: {result.percentage_score:.2f}% ({result.grade_letter})")
    print()
    
    # Export results
    output_dir = args.output or str(settings.RESULTS_DIR)
    print(f"Exporting results to: {output_dir}")
    ResultExporter.generate_all_reports(results, exam, output_dir)
    print("✓ All reports generated")
    print()
    
    print("=" * 80)
    print("DONE")
    print("=" * 80)
    
    return 0


def analyze_command(args):
    """Execute analysis command"""
    print("=" * 80)
    print("EXAM ANALYSIS")
    print("=" * 80)
    print()
    
    # Load exam
    print(f"Loading exam from: {args.exam}")
    exam = ExamParser.from_json(args.exam)
    print(f"✓ Loaded exam: {exam.title}")
    print()
    
    # Load results
    print(f"Loading results from: {args.results}")
    import json
    with open(args.results, 'r') as f:
        results_data = json.load(f)
    
    # Convert to ExamResult objects
    from src.models.submission import ExamResult, GradingResult
    from datetime import datetime
    
    results = []
    for r_data in results_data:
        question_results = [
            GradingResult(
                question_id=qr['question_id'],
                student_answer=None,
                correct_answer=None,
                points_earned=qr['points_earned'],
                points_possible=qr['points_possible'],
                is_correct=qr['is_correct'],
                feedback=qr['feedback']
            )
            for qr in r_data['question_results']
        ]
        
        result = ExamResult(
            student_id=r_data['student_id'],
            student_name=r_data['student_name'],
            exam_id=r_data['exam_id'],
            question_results=question_results,
            total_points_earned=r_data['total_score'],
            total_points_possible=r_data['max_score'],
            graded_at=datetime.fromisoformat(r_data['graded_at'])
        )
        results.append(result)
    
    print(f"✓ Loaded {len(results)} results")
    print()
    
    # Generate analytics
    print("Generating analytics...")
    analytics = ExamAnalytics(exam, results)
    report = analytics.generate_report()
    print()
    
    # Print report
    print(report)
    
    # Save to file if requested
    if args.output:
        with open(args.output, 'w') as f:
            f.write(report)
        print(f"\n✓ Report saved to: {args.output}")
    
    return 0


def create_example_command(args):
    """Create example exam and submissions"""
    from src.models.exam import Exam
    from src.models.question import Question, QuestionType, DifficultyLevel, GradingConfig
    from src.models.submission import StudentSubmission, Answer
    from datetime import datetime
    
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
    
    print(f"Creating example files in: {output_dir}")
    print()
    
    # Create example exam
    questions = [
        Question(
            id="q1",
            text="What is the capital of France?",
            question_type=QuestionType.SHORT_ANSWER,
            points=5.0,
            correct_answer="Paris",
            difficulty=DifficultyLevel.EASY,
            topics=["Geography", "Europe"],
            explanation="Paris is the capital and largest city of France."
        ),
        Question(
            id="q2",
            text="What is 15 + 27?",
            question_type=QuestionType.NUMERICAL,
            points=3.0,
            correct_answer="42",
            difficulty=DifficultyLevel.EASY,
            topics=["Mathematics", "Arithmetic"]
        ),
        Question(
            id="q3",
            text="Which of the following is a programming language?",
            question_type=QuestionType.MULTIPLE_CHOICE,
            points=5.0,
            correct_answer="C",
            options=["A) HTML", "B) CSS", "C) Python", "D) JSON"],
            difficulty=DifficultyLevel.MEDIUM,
            topics=["Computer Science", "Programming"]
        ),
        Question(
            id="q4",
            text="Explain the concept of photosynthesis in plants.",
            question_type=QuestionType.ESSAY,
            points=15.0,
            correct_answer="Photosynthesis is the process by which plants convert light energy into chemical energy (glucose) using carbon dioxide and water, releasing oxygen as a byproduct.",
            difficulty=DifficultyLevel.HARD,
            topics=["Biology", "Plant Science"],
            rubric={
                "definition": {"points": 5, "description": "Clear definition of photosynthesis"},
                "process": {"points": 5, "description": "Explanation of the process"},
                "inputs_outputs": {"points": 5, "description": "Mention of inputs (CO2, H2O, light) and outputs (glucose, O2)"}
            }
        ),
        Question(
            id="q5",
            text="The Earth is flat. True or False?",
            question_type=QuestionType.TRUE_FALSE,
            points=2.0,
            correct_answer="False",
            difficulty=DifficultyLevel.EASY,
            topics=["Science", "Geography"]
        )
    ]
    
    exam = Exam(
        id="sample_exam_001",
        title="Sample General Knowledge Exam",
        description="A sample exam covering various subjects",
        questions=questions,
        subject="General Knowledge",
        duration_minutes=60,
        passing_score=70.0
    )
    
    # Save exam
    exam_path = output_dir / "example_exam.json"
    ExamParser.to_json(exam, str(exam_path))
    print(f"✓ Created exam: {exam_path}")
    
    # Create example submissions
    submissions = [
        StudentSubmission(
            student_id="S001",
            student_name="Alice Johnson",
            exam_id=exam.id,
            answers=[
                Answer(question_id="q1", response="Paris"),
                Answer(question_id="q2", response="42"),
                Answer(question_id="q3", response="C"),
                Answer(question_id="q4", response="Photosynthesis is how plants make food using sunlight, water, and carbon dioxide. They produce glucose for energy and release oxygen."),
                Answer(question_id="q5", response="False")
            ]
        ),
        StudentSubmission(
            student_id="S002",
            student_name="Bob Smith",
            exam_id=exam.id,
            answers=[
                Answer(question_id="q1", response="London"),
                Answer(question_id="q2", response="42"),
                Answer(question_id="q3", response="A"),
                Answer(question_id="q4", response="Plants use sunlight to make energy."),
                Answer(question_id="q5", response="False")
            ]
        ),
        StudentSubmission(
            student_id="S003",
            student_name="Carol Davis",
            exam_id=exam.id,
            answers=[
                Answer(question_id="q1", response="paris"),
                Answer(question_id="q2", response="43"),
                Answer(question_id="q3", response="C"),
                Answer(question_id="q4", response="Photosynthesis is the process where plants convert light energy from the sun into chemical energy stored in glucose. They use carbon dioxide from the air and water from the soil, and release oxygen as a waste product. This process occurs in chloroplasts."),
                Answer(question_id="q5", response="False")
            ]
        )
    ]
    
    # Save submissions
    submissions_path = output_dir / "example_submissions.json"
    SubmissionParser.to_json(submissions, str(submissions_path))
    print(f"✓ Created submissions: {submissions_path}")
    print()
    
    print("Example files created successfully!")
    print()
    print("To grade these examples, run:")
    print(f"  python main.py grade --exam {exam_path} --submissions {submissions_path}")
    print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())