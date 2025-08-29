"""
Search service integrating existing search functionality with progress tracking.
"""
from typing import Dict, Any, Optional, List
import json

from app.core.config import settings
from app.services.progress_service import ProgressService
from app.search import verified_search
from app.extract import fetch_main_text
from app.retrieve import chunk, bm25_rank, embed_rerank
from app.utils import build_query

class SearchService:
    """Service for health fact search and verification."""
    
    def __init__(self, progress_service: ProgressService):
        self.progress_service = progress_service
    
    def search_verified_claim(self, claim: str, user_id: int) -> Dict[str, Any]:
        """
        Search and verify a health claim using existing search infrastructure.
        """
        # Use existing search functionality
        query = build_query(claim, settings.allowed_domains)
        search_results = verified_search(query, top=6)
        
        if not search_results:
            result = {
                "claim": claim,
                "is_verified": False,
                "explanation": "No reliable sources found to verify this claim.",
                "sources": [],
                "confidence": 0.0
            }
        else:
            # Fetch and analyze content from search results
            contexts = []
            for item in search_results[:4]:  # Limit to top 4 results
                page = fetch_main_text(item["url"])
                if page and page.get("text"):
                    contexts.append({
                        "title": page["title"],
                        "url": page["url"],
                        "snippet": page["text"][:500]  # First 500 chars
                    })
            
            if contexts:
                # Use existing retrieval logic to find relevant passages
                all_passages = []
                for ctx in contexts:
                    chunks = chunk(ctx["snippet"], size=200, overlap=50)
                    all_passages.extend(chunks)
                
                # Rank passages by relevance
                if settings.use_embed_rerank:
                    ranked = embed_rerank(claim, all_passages, top_k=3)
                else:
                    ranked = bm25_rank(claim, all_passages, k=3)
                
                # Generate explanation based on ranked passages
                explanation = self._generate_explanation(claim, ranked, contexts)
                
                result = {
                    "claim": claim,
                    "is_verified": True,
                    "explanation": explanation,
                    "sources": [
                        {
                            "title": ctx["title"],
                            "url": ctx["url"],
                            "snippet": ctx["snippet"][:200] + "..."
                        } for ctx in contexts
                    ],
                    "confidence": 0.75  # Could be improved with ML scoring
                }
            else:
                result = {
                    "claim": claim,
                    "is_verified": False,
                    "explanation": "Unable to extract meaningful content from available sources.",
                    "sources": [{"title": item["title"], "url": item["url"], "snippet": ""} for item in search_results],
                    "confidence": 0.2
                }
        
        # Track progress
        source_url = result["sources"][0]["url"] if result["sources"] else None
        self.progress_service.add_search_fact(user_id, claim, source_url)
        
        return result
    
    def _generate_explanation(self, claim: str, ranked_passages: List[tuple], contexts: List[Dict]) -> str:
        """Generate explanation based on ranked passages."""
        if not ranked_passages:
            return f"The claim '{claim}' could not be verified from the available sources."
        
        # Use top-ranked passage for explanation
        top_passage = ranked_passages[0][1] if ranked_passages else ""
        
        if top_passage:
            return f"Based on scientific evidence, {top_passage.strip()}"
        else:
            return f"The claim '{claim}' has been searched in reliable health sources."
    
    def get_search_history(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Get user's search history."""
        progress = self.progress_service.get_user_progress(user_id)
        if not progress:
            return []
        
        # Get user facts and filter for search type
        user = self.progress_service.user_repository.get_by_id(user_id)
        if not user:
            return []
        
        facts = user.facts_as_list
        search_facts = [
            fact for fact in facts 
            if fact.get("type") == "search"
        ]
        
        # Sort by learned_at descending and limit
        search_facts.sort(key=lambda x: x.get("learned_at", ""), reverse=True)
        return search_facts[:limit]
