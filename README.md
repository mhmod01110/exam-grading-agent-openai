# Exam Grading & Feedback Agent 🎓
## Powered by OpenAI GPT-4

An intelligent, AI-powered exam grading system with a beautiful web interface that automatically grades student submissions, provides detailed feedback, and generates comprehensive analytics.

## ✨ Features

### 🤖 AI-Powered Grading
- **OpenAI GPT-4o Integration**: Uses state-of-the-art language models
- **Semantic Understanding**: Goes beyond keyword matching
- **Detailed Feedback**: Constructive, personalized suggestions
- **Multiple Question Types**: MCQ, Essays, Short Answer, Numerical, True/False, Code

### 🎨 Beautiful Web Interface
- **Create Exams**: Visual exam builder with drag-and-drop
- **Take Exams**: Student-friendly interface for submissions
- **View Results**: Beautiful grade cards and detailed feedback
- **Analytics Dashboard**: Class statistics and performance insights

### 📊 Comprehensive Analytics
- Class statistics (mean, median, std deviation)
- Grade distribution charts
- Question difficulty analysis
- Common mistakes identification
- Top performers leaderboard

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))

### Installation

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set Your OpenAI API Key**
   ```bash
   # Linux/Mac
   export OPENAI_API_KEY="sk-your-api-key-here"

   # Windows (PowerShell)
   $env:OPENAI_API_KEY="sk-your-api-key-here"

   # Windows (CMD)
   set OPENAI_API_KEY=sk-your-api-key-here
   ```

3. **Create Static Folder**
   ```bash
   mkdir static
   ```

4. **Move the HTML file**
   - Save the `index.html` file to the `static/` folder

5. **Start the Server**
   ```bash
   python app.py
   ```

6. **Open Your Browser**
   ```
   http://localhost:5000
   ```

## 🎯 Using the Web Interface

### 1️⃣ Create an Exam

1. Click the **"Create Exam"** tab
2. Fill in exam details (title, description, subject)
3. Click **"+ Add Question"** to add questions
4. For each question:
   - Enter question text
   - Select question type
   - Enter correct answer
   - Set points and topics
5. Click **"Create Exam"** or **"Create Example Exam"** for a demo

### 2️⃣ Take an Exam

1. Click the **"Take Exam"** tab
2. Select an exam from the list
3. Enter your Student ID and Name
4. Answer all questions
5. Click **"Submit Answers"**
6. Wait for AI grading (usually 10-30 seconds)

### 3️⃣ View Results

- Automatically redirected after submission
- See your grade badge (A, B, C, D, F)
- View detailed statistics
- Read overall feedback
- Check question-by-question results with suggestions

### 4️⃣ Check Analytics

1. Click the **"Analytics"** tab
2. Select an exam from dropdown
3. View:
   - Class statistics
   - Grade distribution
   - Question difficulty analysis
   - Top performers

## 🔧 Configuration

### Change OpenAI Model

Edit `config/settings.py`:

```python
OPENAI_MODEL = "gpt-4o"  # Options: gpt-4o, gpt-4-turbo, gpt-3.5-turbo
```

Or set environment variable:
```bash
export OPENAI_MODEL="gpt-4-turbo"
```

### Adjust Grading Strictness

When creating an exam, modify the grading config:

```python
{
  "grading_config": {
    "strictness": 0.8,  # 0.0 (lenient) to 1.0 (strict)
    "enable_partial_credit": true,
    "ai_grading_enabled": true
  }
}
```

## 📁 Project Structure

```
exam-grading-agent/
├── app.py                      # Flask web server
├── static/
│   └── index.html             # Web UI
├── src/
│   ├── models/                # Data models
│   ├── core/                  # Grading logic
│   ├── ai/
│   │   └── openai_client.py  # OpenAI integration
│   ├── analytics/             # Performance analysis
│   └── utils/                 # Helpers
├── config/
│   └── settings.py           # Configuration
└── requirements.txt          # Dependencies
```

## 🌐 API Endpoints

### Exams
- `GET /api/exams` - List all exams
- `POST /api/exams` - Create new exam
- `GET /api/exams/<id>` - Get exam details

### Submissions & Grading
- `POST /api/submissions` - Submit answers
- `POST /api/grade` - Grade submission

### Analytics
- `GET /api/analytics/<exam_id>` - Get exam analytics

### Utility
- `GET /api/health` - Check API status
- `POST /api/examples/create` - Create example exam

## 💡 Example API Usage

### Create Exam

```bash
curl -X POST http://localhost:5000/api/exams \
  -H "Content-Type: application/json" \
  -d '{
    "id": "test_001",
    "title": "Sample Exam",
    "description": "A test exam",
    "questions": [
      {
        "id": "q1",
        "text": "What is 2+2?",
        "type": "numerical",
        "correct_answer": "4",
        "points": 5
      }
    ]
  }'
```

### Grade Submission

```bash
curl -X POST http://localhost:5000/api/grade \
  -H "Content-Type: application/json" \
  -d '{
    "exam_id": "test_001",
    "student_id": "S001",
    "student_name": "John Doe",
    "answers": [
      {
        "question_id": "q1",
        "response": "4"
      }
    ],
    "use_ai": true
  }'
```

## 🎨 UI Features

### Design Highlights
- **Modern Gradient Design**: Purple-themed with smooth animations
- **Responsive Layout**: Works on desktop, tablet, and mobile
- **Real-time Feedback**: Loading indicators and status updates
- **Color-Coded Results**: Green for correct, red for incorrect
- **Grade Badges**: Beautiful circular grade displays with colors:
  - A: Green gradient
  - B: Blue gradient
  - C: Yellow gradient
  - D: Pink gradient
  - F: Red gradient

### Interactive Elements
- Tab navigation
- Collapsible sections
- Hover effects
- Progress indicators
- Smooth transitions

## 🔒 Security Notes

**For Production:**
1. Add authentication (user login)
2. Use HTTPS
3. Implement rate limiting
4. Add CSRF protection
5. Sanitize user inputs
6. Use a proper database (PostgreSQL, MongoDB)
7. Add API key validation
8. Implement session management

## 📊 Grading Features

### Question Types Supported

1. **Multiple Choice**
   - Exact answer matching
   - Instant feedback

2. **True/False**
   - Accepts various formats (true/false, yes/no, 1/0)
   - Case-insensitive

3. **Numerical**
   - Tolerance-based matching
   - Partial credit for close answers

4. **Short Answer**
   - AI semantic matching
   - Fuzzy string matching
   - Partial credit based on quality

5. **Essay**
   - AI-powered evaluation
   - Rubric-based grading
   - Detailed feedback with strengths/weaknesses

6. **Code** (Basic)
   - Syntax checking
   - Can be extended with test cases

### AI Grading Process

1. **Semantic Analysis**: Understands meaning, not just keywords
2. **Rubric Application**: Follows provided grading criteria
3. **Feedback Generation**: Creates constructive, detailed feedback
4. **Suggestion Creation**: Provides specific improvement recommendations
5. **Overall Assessment**: Generates comprehensive exam-level feedback

## 🐛 Troubleshooting

### "API Not Configured"
- Check that `OPENAI_API_KEY` is set correctly
- Verify the API key is valid
- Ensure you have OpenAI API credits

### "CORS Error"
- Make sure Flask-CORS is installed
- Check that the API is running on port 5000

### "Module Not Found"
- Run `pip install -r requirements.txt`
- Verify you're in the correct directory

### Slow Grading
- Essay questions take longer (15-30 seconds)
- Consider using `gpt-3.5-turbo` for faster results
- Check your internet connection

## 💰 Cost Estimation

OpenAI API costs vary by model:

- **GPT-4o**: ~$0.005 per question (recommended)
- **GPT-4-Turbo**: ~$0.01 per question
- **GPT-3.5-Turbo**: ~$0.001 per question (faster, less accurate)

Example: Grading 30 students × 10 questions = 300 questions
- With GPT-4o: ~$1.50
- With GPT-3.5-Turbo: ~$0.30

## 🎓 Best Practices

### For Teachers

1. **Clear Questions**: Write unambiguous questions
2. **Detailed Rubrics**: Provide clear grading criteria for essays
3. **Review AI Feedback**: Always review AI-generated feedback
4. **Set Expectations**: Tell students about AI grading
5. **Use Example Answers**: Include comprehensive correct answers

### For Students

1. **Complete Sentences**: Write in full sentences for short answers
2. **Show Work**: Explain your reasoning
3. **Check Answers**: Review before submitting
4. **Read Feedback**: Learn from detailed suggestions

## 🚀 Advanced Features

### Batch Grading

Use the command-line interface for batch processing:

```bash
python main.py grade \
  --exam exam.json \
  --submissions submissions.json \
  --output results/
```

### Custom Evaluators

Extend grading logic:

```python
from src.core.evaluator import AnswerEvaluator

class CustomEvaluator(AnswerEvaluator):
    def _evaluate_custom_type(self, question, student_answer):
        # Your custom logic
        return points, is_correct, feedback
```

### Export Results

```python
from src.utils.exporters import ResultExporter

ResultExporter.generate_all_reports(results, exam, "output_dir")
```

## 📈 Roadmap

- [ ] User authentication system
- [ ] Database integration (PostgreSQL)
- [ ] Real-time collaborative grading
- [ ] Mobile app
- [ ] LMS integration (Canvas, Moodle)
- [ ] Plagiarism detection
- [ ] Video/audio response grading
- [ ] Advanced analytics dashboard
- [ ] Parent/student portal

## 🤝 Contributing

Contributions welcome! Areas for improvement:
- Additional question types
- Better visualizations
- Performance optimizations
- Testing coverage
- Documentation

## 📄 License

MIT License - feel free to use for education!

## 🙏 Acknowledgments

- Built with OpenAI GPT-4o
- Flask web framework
- Modern CSS design principles

## 📞 Support

Having issues?
1. Check the troubleshooting section
2. Verify your API key is set
3. Check the console for errors
4. Review the example exam workflow

---

**Happy Grading! 🎓✨**

Made with ❤️ for educators and students
