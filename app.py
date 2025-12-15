"""
Flask Web API for Exam Grading Agent with JSON File Persistence
"""
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import json
import os
import dataclasses
from datetime import datetime
from pathlib import Path
from enum import Enum

# Import your project modules
from src.core.grader import ExamGrader
from src.analytics.analyzer import ExamAnalytics
from src.models.exam import Exam
from src.models.question import Question, QuestionType, DifficultyLevel, GradingConfig
from src.models.submission import StudentSubmission, Answer
from config.settings import settings

app = Flask(__name__, static_folder='static')
CORS(app)

# ==========================================
# 1. SETUP DATA DIRECTORIES
# ==========================================
BASE_DIR = Path('data')
EXAMS_DIR = BASE_DIR / 'exams'
SUBMISSIONS_DIR = BASE_DIR / 'submissions'
RESULTS_DIR = BASE_DIR / 'results'

# Ensure directories exist
for directory in [EXAMS_DIR, SUBMISSIONS_DIR, RESULTS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# ==========================================
# 2. CUSTOM JSON ENCODER
# ==========================================
class EnhancedJSONEncoder(json.JSONEncoder):
    """Encodes Dataclasses, Datetimes, and Enums for JSON storage"""
    def default(self, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        if isinstance(o, datetime):
            return o.isoformat()
        if isinstance(o, Enum):
            return o.value
        return super().default(o)

# ==========================================
# 3. PERSISTENCE HELPER FUNCTIONS
# ==========================================
def save_json(directory: Path, filename: str, data_object):
    """Saves a dataclass object to a JSON file"""
    path = directory / f"{filename}.json"
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data_object, f, cls=EnhancedJSONEncoder, indent=2, ensure_ascii=False)
        print(f"✓ Saved: {path}")
    except Exception as e:
        print(f"✗ Error saving {path}: {e}")

def load_all_exams():
    """Loads all exam JSON files into memory as Exam objects"""
    exams = {}
    if not EXAMS_DIR.exists(): return exams
    
    print("Loading exams from disk...")
    for filepath in EXAMS_DIR.glob('*.json'):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Reconstruct Question objects (Handle Enums)
            questions = []
            for q in data['questions']:
                # Ensure Enums are correctly typed
                q['question_type'] = QuestionType(q['question_type'])
                q['difficulty'] = DifficultyLevel(q['difficulty'])
                questions.append(Question(**q))
            
            # Reconstruct GradingConfig
            if 'grading_config' in data:
                data['grading_config'] = GradingConfig(**data['grading_config'])
                
            data['questions'] = questions
            
            # Convert string date back to datetime
            if 'created_at' in data and isinstance(data['created_at'], str):
                data['created_at'] = datetime.fromisoformat(data['created_at'])

            exam = Exam(**data)
            exams[exam.id] = exam
            print(f"  - Loaded: {exam.title}")
        except Exception as e:
            print(f"  ✗ Error loading exam {filepath.name}: {e}")
    return exams

def load_all_results_for_exam(exam_id):
    """Loads all results specific to an exam for analytics"""
    results = []
    if not RESULTS_DIR.exists(): return results

    for filepath in RESULTS_DIR.glob('*.json'):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if data.get('exam_id') == exam_id:
                results.append(data) 
        except:
            continue
    return results

# Initialize Cache from Disk
exams_storage = load_all_exams()
submissions_storage = {} 
results_storage = {}     

# ==========================================
# 4. API ROUTES
# ==========================================

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'storage': 'json_file_system',
        'data_dir': str(BASE_DIR),
        'api_configured': bool(settings.OPENAI_API_KEY),
        'model': settings.OPENAI_MODEL
    })

@app.route('/api/exams', methods=['GET'])
def get_exams():
    global exams_storage
    # Refresh from disk to ensure sync
    exams_storage = load_all_exams()
    
    exams_list = [
        {
            'id': exam.id,
            'title': exam.title,
            'description': exam.description,
            'question_count': exam.question_count,
            'total_points': exam.total_points,
            'created_at': exam.created_at.isoformat() if isinstance(exam.created_at, datetime) else exam.created_at
        }
        for exam in exams_storage.values()
    ]
    return jsonify(exams_list)

@app.route('/api/exams', methods=['POST'])
def create_exam():
    global exams_storage
    try:
        data = request.json
        
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
                metadata=q_data.get('metadata', {})
            )
            questions.append(question)
        
        # Parse grading config
        config_data = data.get('grading_config', {})
        grading_config = GradingConfig(
            strictness=config_data.get('strictness', 0.7),
            enable_partial_credit=config_data.get('enable_partial_credit', True),
            ai_grading_enabled=config_data.get('ai_grading_enabled', True)
        )
        
        # Create exam
        exam = Exam(
            id=data['id'],
            title=data['title'],
            description=data['description'],
            questions=questions,
            grading_config=grading_config,
            subject=data.get('subject'),
            passing_score=data.get('passing_score', 60.0)
        )
        
        # Validate
        errors = exam.validate()
        if errors:
            return jsonify({'error': 'Validation failed', 'details': errors}), 400
        
        # 1. Update In-Memory Cache
        exams_storage[exam.id] = exam
        
        # 2. SAVE TO DISK
        save_json(EXAMS_DIR, exam.id, exam)
        
        return jsonify({
            'message': 'Exam created and saved successfully',
            'exam_id': exam.id,
            'question_count': exam.question_count,
            'total_points': exam.total_points
        }), 201
    
    except Exception as e:
        print(f"Error creating exam: {e}")
        return jsonify({'error': str(e)}), 400

@app.route('/api/exams/<exam_id>', methods=['GET'])
def get_exam(exam_id):
    global exams_storage  # <--- FIXED HERE
    
    if exam_id not in exams_storage:
        exams_storage = load_all_exams()

    if exam_id not in exams_storage:
        return jsonify({'error': 'Exam not found'}), 404
    
    exam = exams_storage[exam_id]
    
    return jsonify({
        'id': exam.id,
        'title': exam.title,
        'description': exam.description,
        'subject': exam.subject,
        'question_count': exam.question_count,
        'total_points': exam.total_points,
        'passing_score': exam.passing_score,
        'questions': [
            {
                'id': q.id,
                'text': q.text,
                'type': q.question_type.value,
                'points': q.points,
                'options': q.options,
                'topics': q.topics
            }
            for q in exam.questions
        ]
    })

@app.route('/api/submissions', methods=['POST'])
def submit_answers():
    try:
        data = request.json
        
        answers = [
            Answer(
                question_id=ans['question_id'],
                response=ans['response']
            )
            for ans in data['answers']
        ]
        
        submission = StudentSubmission(
            student_id=data['student_id'],
            student_name=data['student_name'],
            exam_id=data['exam_id'],
            answers=answers
        )
        
        # Create a unique ID for the submission
        submission_id = f"{submission.student_id}_{submission.exam_id}_{int(datetime.now().timestamp())}"
        
        # 1. Update Memory
        submissions_storage[submission_id] = submission
        
        # 2. SAVE TO DISK
        save_json(SUBMISSIONS_DIR, submission_id, submission)
        
        return jsonify({
            'message': 'Submission received and saved',
            'submission_id': submission_id
        }), 201
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/grade', methods=['POST'])
def grade_submission():
    global exams_storage
    try:
        data = request.json
        exam_id = data['exam_id']
        submission_id = data.get('submission_id')
        
        # Ensure exam is loaded
        if exam_id not in exams_storage:
            exams_storage = load_all_exams()
        
        if exam_id not in exams_storage:
            return jsonify({'error': 'Exam not found'}), 404
        
        exam = exams_storage[exam_id]
        
        # Construct Submission Object
        answers = [
            Answer(question_id=ans['question_id'], response=ans['response'])
            for ans in data['answers']
        ]
        
        submission = StudentSubmission(
            student_id=data['student_id'],
            student_name=data['student_name'],
            exam_id=exam_id,
            answers=answers
        )
        
        # If no ID provided, generate one and save
        if not submission_id:
            submission_id = f"{submission.student_id}_{submission.exam_id}_{int(datetime.now().timestamp())}"
            save_json(SUBMISSIONS_DIR, submission_id, submission)

        # Initialize Grader
        api_key = settings.OPENAI_API_KEY
        use_ai = data.get('use_ai', True) and bool(api_key)
        
        grader = ExamGrader(exam, api_key=api_key)
        result = grader.grade_submission(submission, use_ai=use_ai)
        
        # 1. Update Memory
        result_id = f"result_{submission_id}"
        results_storage[result_id] = result
        
        # 2. SAVE TO DISK
        save_json(RESULTS_DIR, result_id, result)
        
        return jsonify({
            'result_id': result_id,
            'student_name': result.student_name,
            'total_score': result.total_points_earned,
            'max_score': result.total_points_possible,
            'percentage': result.percentage_score,
            'grade': result.grade_letter,
            'overall_feedback': result.overall_feedback,
            'question_results': [
                {
                    'question_id': qr.question_id,
                    'points_earned': qr.points_earned,
                    'points_possible': qr.points_possible,
                    'is_correct': qr.is_correct,
                    'feedback': qr.feedback,
                    'suggestions': qr.suggestions
                }
                for qr in result.question_results
            ],
            'analytics': result.analytics
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/<exam_id>', methods=['GET'])
def get_analytics(exam_id):
    global exams_storage
    try:
        # Load exam
        if exam_id not in exams_storage:
             exams_storage = load_all_exams()

        if exam_id not in exams_storage:
            return jsonify({'error': 'Exam not found'}), 404
        
        exam = exams_storage[exam_id]
        
        # Load results from disk
        raw_results = load_all_results_for_exam(exam_id)
        
        if not raw_results:
            return jsonify({'message': 'No results yet'}), 200
        
        # Rehydrate result objects (simplified for analytics)
        # Note: In a production app, use a proper method Result.from_dict()
        # Here we mock the minimal necessary structure if ExamAnalytics needs objects
        from src.models.submission import ExamResult, GradingResult
        
        exam_results_objs = []
        for r_data in raw_results:
            # Reconstruct Question Results
            q_results = [GradingResult(**qr) for qr in r_data.get('question_results', [])]
            
            # Reconstruct Exam Result
            # Clean up dict to match dataclass fields
            clean_data = {k: v for k, v in r_data.items() if k in ExamResult.__annotations__}
            clean_data['question_results'] = q_results
            if 'graded_at' in clean_data:
                clean_data['graded_at'] = datetime.fromisoformat(clean_data['graded_at'])
                
            exam_results_objs.append(ExamResult(**clean_data))

        # Generate analytics
        analytics = ExamAnalytics(exam, exam_results_objs)
        
        return jsonify({
            'class_statistics': analytics.get_class_statistics(),
            'grade_distribution': analytics.get_grade_distribution(),
            'question_statistics': analytics.get_question_statistics()[:10],
            'common_mistakes': analytics.get_common_mistakes(),
            'top_performers': analytics.get_top_performers(),
            'performance_by_topic': analytics.get_performance_by_topic()
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/examples/create', methods=['POST'])
def create_example_exam():
    """Create an example exam with sample data and save it"""
    global exams_storage
    try:
        questions = [
            Question(
                id="q1",
                text="What is the capital of France?",
                question_type=QuestionType.SHORT_ANSWER,
                points=5.0,
                correct_answer="Paris",
                difficulty=DifficultyLevel.EASY,
                topics=["Geography"]
            ),
            Question(
                id="q2",
                text="What is 15 + 27?",
                question_type=QuestionType.NUMERICAL,
                points=3.0,
                correct_answer="42",
                difficulty=DifficultyLevel.EASY,
                topics=["Mathematics"]
            ),
            Question(
                id="q3",
                text="Which programming language is this?",
                question_type=QuestionType.MULTIPLE_CHOICE,
                points=5.0,
                correct_answer="C",
                options=["A) HTML", "B) CSS", "C) Python", "D) JSON"],
                difficulty=DifficultyLevel.MEDIUM,
                topics=["Programming"]
            ),
            Question(
                id="q4",
                text="Explain photosynthesis briefly.",
                question_type=QuestionType.ESSAY,
                points=15.0,
                correct_answer="Photosynthesis is how plants convert light energy into chemical energy using CO2 and water, producing glucose and oxygen.",
                difficulty=DifficultyLevel.HARD,
                topics=["Biology"]
            )
        ]
        
        exam = Exam(
            id="example_exam_001",
            title="Example General Knowledge Exam",
            description="A sample exam for demonstration",
            questions=questions,
            subject="General Knowledge",
            passing_score=70.0
        )
        
        # 1. Store in memory
        exams_storage[exam.id] = exam
        
        # 2. SAVE TO DISK
        save_json(EXAMS_DIR, exam.id, exam)
        
        return jsonify({
            'message': 'Example exam created and saved',
            'exam_id': exam.id,
            'exam': {
                'id': exam.id,
                'title': exam.title,
                'question_count': exam.question_count,
                'total_points': exam.total_points
            }
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    # Ensure directories exist
    settings.ensure_directories()
    
    print("=" * 80)
    print("EXAM GRADING & FEEDBACK AGENT - WEB API")
    print(f"Data Storage: {BASE_DIR.absolute()}")
    print(f"OpenAI API Configured: {bool(settings.OPENAI_API_KEY)}")
    print("=" * 80)
    
    app.run(debug=True, host='0.0.0.0', port=5000)