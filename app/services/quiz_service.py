"""
Quiz service integrating existing quiz functionality with progress tracking.
"""
from typing import Dict, Any, List, Optional
import json

from app.services.progress_service import ProgressService
from app.quiz.service import build_context_from_search, generate_mcqs_llm_with_error, validate_mcqs

class QuizService:
    """Service for health fact quizzes."""
    
    def __init__(self, progress_service: ProgressService):
        self.progress_service = progress_service
    
    def generate_quiz_from_claim(self, claim: str, user_id: int) -> Dict[str, Any]:
        """
        Generate a quiz from a health claim using existing quiz infrastructure.
        """
        try:
            # Use existing context building
            contexts = build_context_from_search(claim, top_urls=4, chars=1200)
            
            if not contexts:
                return {
                    "claim": claim,
                    "questions": [],
                    "quiz_id": f"quiz_{user_id}_{hash(claim) % 10000}",
                    "error": "No reliable sources found to generate quiz"
                }
            
            # Use existing LLM quiz generation
            items, error = generate_mcqs_llm_with_error(
                contexts, claim, n=3, difficulty="medium", style="health"
            )
            
            if error:
                return {
                    "claim": claim,
                    "questions": [],
                    "quiz_id": f"quiz_{user_id}_{hash(claim) % 10000}",
                    "error": f"Quiz generation failed: {error}"
                }
            
            # Validate questions
            validated = validate_mcqs(items, contexts)
            
            if not validated:
                return {
                    "claim": claim,
                    "questions": [],
                    "quiz_id": f"quiz_{user_id}_{hash(claim) % 10000}",
                    "error": "No valid questions could be generated"
                }
            
            # Format questions for API response
            formatted_questions = []
            for i, item in enumerate(validated):
                formatted_questions.append({
                    "id": i + 1,
                    "question": item["question"],
                    "options": item["options"],
                    "explanation": item["explanation"],
                    "source_url": item["source_url"]
                })
            
            quiz = {
                "claim": claim,
                "questions": formatted_questions,
                "quiz_id": f"quiz_{user_id}_{hash(claim) % 10000}",
                "contexts": contexts  # Store contexts for grading
            }
            
            # Track progress for quiz generation
            source_url = contexts[0]["url"] if contexts else None
            self.progress_service.add_quiz_fact(
                user_id, 
                claim, 
                source_url=source_url, 
                questions_count=len(formatted_questions)
            )
            
            return quiz
            
        except Exception as e:
            return {
                "claim": claim,
                "questions": [],
                "quiz_id": f"quiz_{user_id}_{hash(claim) % 10000}",
                "error": f"Unexpected error: {str(e)}"
            }
    
    def grade_quiz(self, quiz_id: str, answers: List[str], user_id: int, 
                   quiz_data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Grade a completed quiz using existing validation logic.
        """
        try:
            # For now, we'll use stored correct answers
            # In a real implementation, you'd retrieve the quiz from storage
            if not quiz_data:
                # Mock correct answers - in production, retrieve from storage
                correct_answers = ["A", "B", "C"][:len(answers)]
            else:
                # Extract correct answers from quiz data
                questions = quiz_data.get("questions", [])
                correct_answers = []
                for q in questions:
                    correct_idx = q.get("correct_index", 0)
                    options = q.get("options", [])
                    if correct_idx < len(options):
                        correct_answers.append(options[correct_idx])
                    else:
                        correct_answers.append("Unknown")
            
            # Ensure we have the same number of answers and correct answers
            min_length = min(len(answers), len(correct_answers))
            answers = answers[:min_length]
            correct_answers = correct_answers[:min_length]
            
            # Calculate score
            correct_count = sum(1 for user_ans, correct_ans in zip(answers, correct_answers) 
                               if user_ans == correct_ans)
            total_questions = len(answers)
            score_percentage = (correct_count / total_questions) * 100 if total_questions > 0 else 0
            
            # Create detailed results
            results = []
            for i, (user_ans, correct_ans) in enumerate(zip(answers, correct_answers)):
                results.append({
                    "question_number": i + 1,
                    "user_answer": user_ans,
                    "correct_answer": correct_ans,
                    "is_correct": user_ans == correct_ans
                })
            
            grading_result = {
                "quiz_id": quiz_id,
                "score": correct_count,
                "total_questions": total_questions,
                "score_percentage": score_percentage,
                "passed": score_percentage >= 60,  # 60% passing grade
                "results": results
            }
            
            # Track progress for each answer (as requested by user)
            self.progress_service.add_quiz_answers(user_id, answers, correct_answers)
            
            return grading_result
            
        except Exception as e:
            return {
                "quiz_id": quiz_id,
                "score": 0,
                "total_questions": len(answers),
                "score_percentage": 0.0,
                "passed": False,
                "results": [],
                "error": f"Grading failed: {str(e)}"
            }
    
    def get_quiz_history(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Get user's quiz history."""
        progress = self.progress_service.get_user_progress(user_id)
        if not progress:
            return []
        
        # Get user facts and filter for quiz type
        user = self.progress_service.user_repository.get_by_id(user_id)
        if not user:
            return []
        
        facts = user.facts_as_list
        quiz_facts = [
            fact for fact in facts 
            if fact.get("type") in ["quiz", "quiz_answer"]
        ]
        
        # Sort by learned_at descending and limit
        quiz_facts.sort(key=lambda x: x.get("learned_at", ""), reverse=True)
        return quiz_facts[:limit]
