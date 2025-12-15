"""
Configuration settings for the Exam Grading Agent
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()  # 

class Settings:
    """Application settings"""
    
    # API Configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")  # or gpt-4-turbo, gpt-3.5-turbo
    
    # Paths
    BASE_DIR = Path(__file__).parent.parent
    DATA_DIR = BASE_DIR / "data"
    EXAMS_DIR = DATA_DIR / "exams"
    SUBMISSIONS_DIR = DATA_DIR / "submissions"
    RESULTS_DIR = DATA_DIR / "results"
    
    # Grading Defaults
    DEFAULT_STRICTNESS = 0.7
    DEFAULT_PASSING_SCORE = 60.0
    ENABLE_AI_GRADING = True
    
    # Export Settings
    EXPORT_JSON = True
    EXPORT_CSV = True
    EXPORT_INDIVIDUAL_REPORTS = True
    
    # Logging
    LOG_LEVEL = "INFO"
    LOG_FILE = BASE_DIR / "grader.log"
    
    @classmethod
    def ensure_directories(cls):
        """Create necessary directories if they don't exist"""
        cls.DATA_DIR.mkdir(exist_ok=True)
        cls.EXAMS_DIR.mkdir(exist_ok=True)
        cls.SUBMISSIONS_DIR.mkdir(exist_ok=True)
        cls.RESULTS_DIR.mkdir(exist_ok=True)
    
    @classmethod
    def validate(cls):
        """Validate configuration"""
        issues = []
        
        if cls.ENABLE_AI_GRADING and not cls.OPENAI_API_KEY:
            issues.append("AI grading enabled but OPENAI_API_KEY not set")
        
        return issues


# Initialize settings
settings = Settings()
settings.ensure_directories()