"""
OpenAI API client for AI-powered grading
"""
import os
import json
from typing import Dict, Any, Optional
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()  


class OpenAIGradingClient:
    """Client for interacting with OpenAI API for exam grading"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        """Initialize OpenAI client"""
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY must be set")
        
        self.client = OpenAI(api_key=self.api_key)
        self.model = model  # Can use gpt-4o, gpt-4-turbo, gpt-3.5-turbo
    
    def grade_answer(
        self,
        question_text: str,
        correct_answer: Any,
        student_answer: Any,
        question_type: str,
        points_possible: float,
        rubric: Optional[Dict[str, Any]] = None,
        strictness: float = 0.7
    ) -> Dict[str, Any]:
        """
        Grade a student answer using OpenAI
        
        Returns:
            Dict with keys: points_earned, feedback, is_correct, analysis
        """
        prompt = self._build_grading_prompt(
            question_text, correct_answer, student_answer,
            question_type, points_possible, rubric, strictness
        )
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert exam grader. Provide fair, constructive feedback."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            result_text = response.choices[0].message.content
            return self._parse_grading_response(result_text)
        
        except Exception as e:
            return {
                "points_earned": 0,
                "feedback": f"Error during grading: {str(e)}",
                "is_correct": False,
                "analysis": {}
            }
    
    def _build_grading_prompt(
        self,
        question_text: str,
        correct_answer: Any,
        student_answer: Any,
        question_type: str,
        points_possible: float,
        rubric: Optional[Dict[str, Any]],
        strictness: float
    ) -> str:
        """Build grading prompt for OpenAI"""
        
        strictness_desc = "very strict" if strictness > 0.8 else \
                         "strict" if strictness > 0.6 else \
                         "moderate" if strictness > 0.4 else "lenient"
        
        prompt = f"""You are an expert exam grader. Grade the following student answer.

QUESTION:
{question_text}

QUESTION TYPE: {question_type}
POINTS POSSIBLE: {points_possible}

CORRECT ANSWER:
{correct_answer}

STUDENT ANSWER:
{student_answer}

GRADING STRICTNESS: {strictness_desc} ({strictness}/1.0)
"""
        
        if rubric:
            prompt += f"\n\nGRADING RUBRIC:\n{json.dumps(rubric, indent=2)}"
        
        prompt += """

Provide your grading in JSON format with these exact keys:
{
  "points_earned": <number between 0 and points_possible>,
  "is_correct": <true/false>,
  "feedback": "<detailed constructive feedback for the student>",
  "analysis": {
    "strengths": ["<what the student did well>"],
    "weaknesses": ["<what needs improvement>"],
    "misconceptions": ["<any misconceptions identified>"]
  },
  "suggestions": ["<specific suggestions for improvement>"]
}

IMPORTANT GRADING GUIDELINES:
1. For short answers, check for semantic equivalence, not just exact matching
2. Award partial credit when appropriate based on the strictness level
3. Be constructive and encouraging in feedback
4. Identify specific areas for improvement
5. Consider spelling/grammar errors based on strictness
6. For essays, evaluate content, organization, and clarity
7. Return ONLY valid JSON
"""
        
        return prompt
    
    def _parse_grading_response(self, response_text: str) -> Dict[str, Any]:
        """Parse OpenAI's response into structured format"""
        try:
            result = json.loads(response_text.strip())
            
            # Validate required fields
            required_fields = ["points_earned", "is_correct", "feedback"]
            for field in required_fields:
                if field not in result:
                    raise ValueError(f"Missing required field: {field}")
            
            return result
        
        except json.JSONDecodeError as e:
            return {
                "points_earned": 0,
                "feedback": f"Could not parse grading response: {str(e)}",
                "is_correct": False,
                "analysis": {}
            }
    
    def generate_overall_feedback(
        self,
        exam_title: str,
        total_score: float,
        max_score: float,
        question_results: list
    ) -> str:
        """Generate overall exam feedback"""
        
        prompt = f"""Generate encouraging and constructive overall feedback for a student who completed an exam.

EXAM: {exam_title}
SCORE: {total_score}/{max_score} ({(total_score/max_score)*100:.1f}%)

QUESTION-BY-QUESTION RESULTS:
{json.dumps(question_results, indent=2)}

Provide:
1. Overall performance summary
2. Key strengths demonstrated
3. Main areas for improvement
4. Specific study recommendations
5. Encouraging conclusion

Keep feedback constructive, specific, and actionable. Limit to 2-3 paragraphs.
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an encouraging educator providing constructive feedback."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=500
            )
            
            return response.choices[0].message.content
        
        except Exception as e:
            return f"Overall score: {total_score}/{max_score}. Keep studying and improving!"