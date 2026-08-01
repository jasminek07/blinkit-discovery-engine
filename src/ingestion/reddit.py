import hashlib
import warnings
from datetime import datetime
from typing import List, Dict, Any
import praw
from src.config import settings

def anonymize_author(author_name: str) -> str:
    """Anonymizes Reddit usernames to protect user privacy."""
    if not author_name:
        return "Anonymized_User"
    return f"RedditUser_{hashlib.md5(author_name.encode('utf-8')).hexdigest()[:8]}"

def fetch_reddit_discussions(subreddits: List[str] = None, query: str = "Blinkit OR Zepto OR Instamart", count: int = 50) -> List[Dict[str, Any]]:
    """
    Scrapes Reddit discussions and posts matching query criteria.
    Gracefully handles default/dummy credentials and errors.
    
    Args:
        subreddits: List of subreddits to search (default: india, bangalore, Delhi, Mumbai).
        query: Keyword query for search.
        count: Maximum posts to fetch.
        
    Returns:
        List of normalized post dictionaries.
    """
    if subreddits is None:
        subreddits = ["india", "bangalore", "Delhi", "Mumbai"]
        
    # Check for dummy credentials
    if settings.reddit_client_id == "dummy_reddit_client_id" or settings.reddit_client_secret == "dummy_reddit_client_secret":
        warnings.warn("Using dummy Reddit credentials. Returning empty discussion list.")
        return []
        
    normalized_posts = []
    try:
        # Initialize PRAW client
        reddit = praw.Reddit(
            client_id=settings.reddit_client_id,
            client_secret=settings.reddit_client_secret,
            user_agent=settings.reddit_user_agent
        )
        
        # We can search either across all combined subreddits or individually
        subreddits_combined = "+".join(subreddits)
        subreddit = reddit.subreddit(subreddits_combined)
        
        # Search posts sorted by relevance/new
        for post in subreddit.search(query, sort="new", limit=count):
            author_name = post.author.name if post.author else "Deleted_User"
            title = post.title or ""
            selftext = post.selftext or ""
            
            # Combine title and body text
            full_text = f"{title}. {selftext}" if selftext else title
            
            # Convert timestamp
            timestamp_str = datetime.fromtimestamp(post.created_utc).isoformat()
            
            normalized_posts.append({
                "source_id": post.id,
                "platform": "reddit",
                "timestamp": timestamp_str,
                "author_anonymized": anonymize_author(author_name),
                "raw_text": full_text,
                "metadata": {
                    "subreddit": post.subreddit.display_name,
                    "score": post.score,
                    "num_comments": post.num_comments,
                    "url": post.url
                }
            })
            
    except Exception as e:
        print(f"Reddit client initialization or retrieval failed: {e}")
        return []
        
    return normalized_posts
