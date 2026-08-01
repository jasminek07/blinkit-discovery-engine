from typing import List, Dict, Any
from src.classification.cohort_classifier import CohortClassifier

class OpportunityScorer:
    """Ranks product opportunities based on segment proportions and severity indices."""
    def __init__(self, confidence_threshold: float = 0.55):
        self.classifier = CohortClassifier(confidence_threshold=confidence_threshold)

    def analyze_cluster_segments(self, cluster_reviews: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculates user cohort proportions within a single theme cluster."""
        segment_counts = {}
        total = len(cluster_reviews)
        
        for review in cluster_reviews:
            text = review.get("cleaned_text", "")
            segment, _ = self.classifier.classify_review(text)
            segment_counts[segment] = segment_counts.get(segment, 0) + 1
            
        proportions = {}
        for segment, count in segment_counts.items():
            proportions[segment] = round(count / total, 2)
            
        return {
            "counts": segment_counts,
            "proportions": proportions
        }

    def compute_opportunity_matrix(self, clusters: Dict[str, Any], total_records: int) -> List[Dict[str, Any]]:
        """
        Computes opportunity scores for all clusters.
        Opportunity Score = Pain Severity (via rating distance) * Segment Reach (frequency)
        """
        opportunities = []
        
        for label, cluster in clusters.items():
            reviews = cluster.get("reviews", [])
            size = len(reviews)
            
            if size == 0 or total_records == 0:
                continue
                
            # 1. Segment Reach: ratio of this cluster's size to total records
            reach = size / total_records
            
            # 2. Pain Severity: calculated using review scores/ratings if available
            # Lower score = higher pain severity. Scale to 0.0 - 1.0.
            scores = []
            for r in reviews:
                # Play Store score
                score = r.get("metadata", {}).get("score")
                if score is None:
                    # App Store rating
                    score = r.get("metadata", {}).get("rating")
                if score is not None:
                    scores.append(float(score))
                    
            if scores:
                avg_score = sum(scores) / len(scores)
                # If avg_score is 1.0 (worst), pain severity is 1.0
                # If avg_score is 5.0 (best), pain severity is 0.1
                severity = (5.0 - avg_score) / 4.0
                severity = max(0.1, min(1.0, severity))
            else:
                # Default severity if rating metadata is missing
                severity = 0.6
                
            # 3. Opportunity Score calculation
            opp_score = round(severity * reach, 3)
            
            # 4. Cohort analysis
            cohort_data = self.analyze_cluster_segments(reviews)
            
            # Find the dominant user segment in this cluster
            if cohort_data["proportions"]:
                dominant_segment = max(cohort_data["proportions"], key=cohort_data["proportions"].get)
            else:
                dominant_segment = "Uncategorized"
                
            opportunities.append({
                "theme_id": label,
                "opportunity_score": opp_score,
                "reach": round(reach, 2),
                "pain_severity": round(severity, 2),
                "dominant_segment": dominant_segment,
                "segment_breakdown": cohort_data["proportions"],
                "centroid_review": cluster.get("centroid_review", {})
            })
            
        # Sort opportunities by score in descending order (highest score represents highest priority)
        opportunities.sort(key=lambda x: x["opportunity_score"], reverse=True)
        return opportunities
