import json
from typing import List, Dict, Any
from src.llm_agent.groq_client import GroqClient

SYSTEM_PROMPT = """You are a Principal Product Discovery Expert and UX Researcher.
Your job is to analyze a cluster of customer reviews and synthesize a single, coherent user behavioral theme.

You must return a JSON object with the following schema:
{
  "theme_name": "Short, clear title summarizing the customer behavior or pain point",
  "summary": "Detailed summary describing the customer motivations, patterns, and insights in the cluster",
  "user_motivations": ["List of core customer motivations"],
  "pain_points": ["List of core friction points or frustrations"],
  "product_opportunities": ["List of actionable product feature or growth opportunities"],
  "supporting_quotes": [
    {
      "text": "Verbatim customer quote from the inputs showing this behavior",
      "source_platform": "play_store/app_store/reddit",
      "timestamp": "ISO-timestamp"
    }
  ]
}

CRITICAL RULES:
1. Every quote in 'supporting_quotes' MUST be copied exactly verbatim from the input reviews list. Do not modify even a single character.
2. Limit your summary to 3 concise sentences.
3. Highlight actual opportunities rather than generic software features.
"""

def prepare_cluster_prompt(cluster_id: str, reviews: List[Dict[str, Any]]) -> str:
    """Formats cluster details and limits input size (token budgeting) to 20 records."""
    # Apply token budgeting: Capping to top 20 reviews to fit limits
    reviews_to_send = reviews[:20]
    
    formatted_reviews = []
    for r in reviews_to_send:
        formatted_reviews.append({
            "text": r.get("cleaned_text", ""),
            "platform": r.get("platform", ""),
            "timestamp": r.get("timestamp", "")
        })
        
    user_prompt = {
        "cluster_id": cluster_id,
        "total_reviews_in_cluster": len(reviews),
        "sampled_reviews": formatted_reviews
    }
    
    return json.dumps(user_prompt, indent=2)

class InsightSynthesizer:
    """Orchestrates structured LLM summarization of clustering outputs."""
    def __init__(self):
        self.groq_client = GroqClient()

    def synthesize_theme_insight(self, cluster_id: str, reviews: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Runs LLM summarization for a feedback cluster, ensuring token budget is maintained."""
        if not reviews:
            return {}
            
        user_prompt = prepare_cluster_prompt(cluster_id, reviews)
        
        # Complete JSON completion via Groq
        raw_json_insight = self.groq_client.complete_json(SYSTEM_PROMPT, user_prompt)
        return raw_json_insight
