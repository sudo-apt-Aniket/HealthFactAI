"""
Progress tracking service with business logic.
"""
from typing import Dict, Any, Optional, List
from datetime import datetime, date, timedelta
import json

from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.health_categories import HealthCategory, classify_health_claim

class ProgressService:
    """Service for user progress tracking."""
    
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository
    
    def get_user_progress(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get comprehensive user progress data."""
        user = self.user_repository.get_by_id(user_id)
        if not user:
            return None
        
        # Get category breakdown
        categories = user.get_category_breakdown()
        
        # Calculate facts this week
        facts_this_week = self._count_facts_this_week(user.facts_as_list)
        
        return {
            "total_facts": user.total_facts_count,
            "current_streak": user.current_streak,
            "longest_streak": user.longest_streak,
            "categories": categories,
            "last_activity": user.last_activity_date,
            "facts_this_week": facts_this_week
        }
    
    def add_search_fact(self, user_id: int, claim: str, source_url: Optional[str] = None) -> bool:
        """Add a fact from search activity."""
        user = self.user_repository.get_by_id(user_id)
        if not user:
            return False
        
        # Classify the claim
        category = classify_health_claim(claim)
        
        # Add the fact
        user.add_fact(
            content=claim,
            category=category.value,
            source_url=source_url,
            fact_type="search"
        )
        
        # Update streak
        self._update_streak(user)
        
        # Save to database
        return self._save_user_progress(user)
    
    def add_quiz_fact(self, user_id: int, claim: str, source_url: Optional[str] = None, 
                     questions_count: int = 0) -> bool:
        """Add a fact from quiz generation."""
        user = self.user_repository.get_by_id(user_id)
        if not user:
            return False
        
        # Classify the claim
        category = classify_health_claim(claim)
        
        # Add the fact
        user.add_fact(
            content=claim,
            category=category.value,
            source_url=source_url,
            fact_type="quiz",
            questions=questions_count
        )
        
        # Update streak
        self._update_streak(user)
        
        # Save to database
        return self._save_user_progress(user)
    
    def add_quiz_answers(self, user_id: int, answers: List[str], correct_answers: List[str]) -> bool:
        """Add facts for each quiz answer."""
        user = self.user_repository.get_by_id(user_id)
        if not user:
            return False
        
        # Add fact for each answer
        for i, (user_answer, correct_answer) in enumerate(zip(answers, correct_answers)):
            is_correct = user_answer == correct_answer
            user.add_fact(
                content=f"Quiz Question {i+1}: {'Correct' if is_correct else 'Incorrect'} ({user_answer} vs {correct_answer})",
                category="Quiz",
                source_url=None,
                fact_type="quiz_answer",
                question_number=i + 1,
                user_answer=user_answer,
                correct_answer=correct_answer,
                is_correct=is_correct
            )
        
        # Update streak (only once per quiz session)
        self._update_streak(user)
        
        # Save to database
        return self._save_user_progress(user)
    
    def _update_streak(self, user: User) -> None:
        """Update user's daily streak."""
        from datetime import datetime, date, timedelta
        
        today = date.today()
        yesterday = today - timedelta(days=1)
        
        current_streak = user.current_streak or 0
        longest_streak = user.longest_streak or 0
        
        # Parse last activity date
        last_activity = None
        if user.last_activity_date:
            try:
                last_activity = datetime.strptime(user.last_activity_date, "%Y-%m-%d").date()
            except ValueError:
                pass
        
        if last_activity is None:
            # First time activity
            new_current = 1
        elif last_activity == today:
            # Activity already today, maintain streak
            new_current = current_streak or 1
        elif last_activity == yesterday:
            # Activity yesterday, increment streak
            new_current = current_streak + 1
        else:
            # Gap in activity, reset streak
            new_current = 1
        
        new_longest = max(longest_streak, new_current)
        new_last_activity = today.strftime("%Y-%m-%d")
        
        user.current_streak = new_current
        user.longest_streak = new_longest
        user.last_activity_date = new_last_activity
    
    def _save_user_progress(self, user: User) -> bool:
        """Save user progress to database."""
        try:
            return self.user_repository.update_progress(
                user.id,
                user.facts_learned,
                user.total_facts_count,
                user.current_streak,
                user.longest_streak,
                user.last_activity_date
            )
        except Exception as e:
            print(f"Error saving user progress: {e}")
            return False
    
    def _count_facts_this_week(self, facts: List[Dict[str, Any]]) -> int:
        """Count facts learned in the past week."""
        today = date.today()
        week_ago = today - timedelta(days=6)
        count = 0
        
        for fact in facts:
            learned_at = fact.get("learned_at")
            if not learned_at:
                continue
            
            try:
                fact_date = datetime.strptime(learned_at, "%Y-%m-%dT%H:%M:%SZ").date()
                if week_ago <= fact_date <= today:
                    count += 1
            except (ValueError, TypeError):
                continue
        
        return count
