import re
from typing import Dict, Any, Tuple

# Keyword patterns mapping to quick-commerce cohort behaviors
COHORT_PATTERNS = {
    "habitual_buyer": [
        r"\bdaily\b", r"\bevery[\s-]day\b", r"\bregularly\b", r"\brepeatedly\b", 
        r"\broutine\b", r"\bhabit\b", r"\balways\b", r"\bweekly\b", r"\bmonth\b"
    ],
    "exploratory_shopper": [
        r"\btry\b", r"\bexplore\b", r"\bdiscover\b", r"\bnew category\b", r"\bvariety\b",
        r"\borganic\b", r"\bartisanal\b", r"\bfind new\b", r"\boptions\b", r"\bdecor\b", r"\bbeauty\b"
    ],
    "price_sensitive": [
        r"\bexpensive\b", r"\bcharge\b", r"\bprice\b", r"\bcost\b", r"\bfee\b", 
        r"\bdiscount\b", r"\bcoupon\b", r"\bmoney\b", r"\brs\b", r"\brupee\b", r"\bsave\b"
    ],
    "convenience_first": [
        r"\bfast\b", r"\bquick\b", r"\bspeed\b", r"\b10[\s-]min\b", r"\bdoor[\s-]step\b", 
        r"\bconvenient\b", r"\beasy\b", r"\btime\b", r"\bminutes\b"
    ],
    "trust_conscious": [
        r"\bscam\b", r"\bdefective\b", r"\bfake\b", r"\brefund\b", r"\breturn\b", 
        r"\btrust\b", r"\bquality\b", r"\bdoctor\b", r"\bspoilt\b", r"\bconsult\b", r"\bverify\b"
    ],
    "mission_driven": [
        r"\bsearch\b", r"\bfind\b", r"\bneed\b", r"\bitem\b", r"\bbuy\b", 
        r"\bforget\b", r"\badd-on\b", r"\bspecific\b"
    ]
}

class CohortClassifier:
    """Classifies feedback documents into user behavioral segments based on text patterns."""
    def __init__(self, confidence_threshold: float = 0.55):
        self.threshold = confidence_threshold

    def classify_review(self, text: str) -> Tuple[str, float]:
        """
        Classifies a review string into a cohort segment.
        Returns a tuple of (segment_name, confidence_score).
        Falls back to 'Uncategorized' if confidence is below the threshold.
        """
        if not text:
            return "Uncategorized", 0.0
            
        normalized = text.lower()
        scores = {}
        
        # Calculate occurrences for each cohort category
        total_hits = 0
        for cohort, patterns in COHORT_PATTERNS.items():
            hits = 0
            for pattern in patterns:
                hits += len(re.findall(pattern, normalized))
            scores[cohort] = hits
            total_hits += hits
            
        # If no keywords matched, return uncategorized
        if total_hits == 0:
            return "Uncategorized", 0.0
            
        # Normalize to probability distributions
        probabilities = {k: v / total_hits for k, v in scores.items()}
        
        # Find highest cohort match
        best_cohort = max(probabilities, key=probabilities.get)
        confidence = probabilities[best_cohort]
        
        # Guardrail: Filter out classifications below the confidence threshold
        if confidence < self.threshold:
            return "Uncategorized", confidence
            
        return best_cohort, round(confidence, 2)
