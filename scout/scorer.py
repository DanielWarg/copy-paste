"""
Scorer - Local heuristic-based scoring for RSS items.

No OpenAI - pure local heuristics.
"""
import re
from datetime import datetime
from typing import Dict, Any


class Scorer:
    """
    Scores RSS items using local heuristics.
    
    Returns score 1-10 based on:
    - Keyword matching (breaking, urgent, etc.)
    - Feed priority
    - Item recency
    """
    
    def __init__(self):
        """Initialize scorer with keyword patterns."""
        # High-priority keywords
        self.priority_keywords = {
            "breaking": 3,
            "urgent": 3,
            "live": 2,
            "uppdatering": 2,
            "nyhet": 1,
        }
        
        # Feed priorities (can be configured per feed)
        self.feed_priorities = {
            "polisen": 2,
            "svt": 1,
        }
    
    def score(self, item: Dict[str, Any], feed_name: str) -> int:
        """
        Score an RSS item.
        
        Args:
            item: RSS item dict with title, description, published, etc.
            feed_name: Name of the feed
            
        Returns:
            Score from 1-10
        """
        score = 5  # Base score
        
        # Keyword matching in title and description
        title = item.get("title", "").lower()
        description = item.get("description", "").lower()
        text = f"{title} {description}"
        
        for keyword, points in self.priority_keywords.items():
            if keyword in text:
                score += points
        
        # Feed priority
        feed_lower = feed_name.lower()
        for feed_key, points in self.feed_priorities.items():
            if feed_key in feed_lower:
                score += points
        
        # Recency bonus (newer = higher score)
        published = item.get("published_parsed")
        if published:
            try:
                pub_time = datetime(*published[:6])
                age_hours = (datetime.utcnow() - pub_time).total_seconds() / 3600
                
                # Items less than 1 hour old get +2, less than 6 hours get +1
                if age_hours < 1:
                    score += 2
                elif age_hours < 6:
                    score += 1
            except:
                pass
        
        # Clamp to 1-10
        return max(1, min(10, score))


# Global instance
scorer = Scorer()

