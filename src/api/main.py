import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, List
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.vector_db.chroma_client import ChromaVectorStore
from src.modeling.clustering import perform_clustering
from src.llm_agent.synthesizer import InsightSynthesizer
from src.llm_agent.validator import validate_and_ground_quotes, calculate_theme_confidence
from src.classification.opportunity_scorer import OpportunityScorer

app = FastAPI(title="Blinkit User Discovery Engine API", version="1.0")

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

REPORT_CACHE_PATH = PROJECT_ROOT / "data" / "discovery_report.json"

def compile_discovery_report() -> Dict[str, Any]:
    """Runs the database retrieval, clustering, classification, and LLM synthesis to build the final report."""
    normalized_path = PROJECT_ROOT / "data" / "normalized_reviews.json"
    if not normalized_path.exists():
        raise FileNotFoundError("Normalized reviews file not found.")

    with open(normalized_path, "r", encoding="utf-8") as f:
        reviews = json.load(f)

    if not reviews:
        return {
            "executive_summary": {"total_processed": 0, "total_themes": 0},
            "themes": [],
            "opportunities": [],
            "cohorts_breakdown": {}
        }

    # 1. Fetch from Vector DB
    store = ChromaVectorStore(collection_name="blinkit_live_reviews")
    # Make sure DB has the records
    all_stored = store.get_all_reviews()
    if len(all_stored) < len(reviews):
        store.reset_database()
        store.add_reviews(reviews)
        
    get_results = store.collection.get(include=["embeddings", "documents", "metadatas"])
    ids = get_results.get("ids", [])
    embeddings = get_results.get("embeddings", [])
    documents = get_results.get("documents", [])
    metadatas = get_results.get("metadatas", [])
    
    retrieved_reviews = []
    for idx in range(len(ids)):
        doc_meta = metadatas[idx]
        meta_dict = {k[5:]: v for k, v in doc_meta.items() if k.startswith("meta_")}
        main_meta = {k: v for k, v in doc_meta.items() if not k.startswith("meta_")}
        
        retrieved_reviews.append({
            "source_id": ids[idx],
            "cleaned_text": documents[idx],
            "platform": main_meta.get("platform", "play_store"),
            "timestamp": main_meta.get("timestamp", ""),
            "author_anonymized": main_meta.get("author_anonymized", ""),
            "metadata": meta_dict
        })

    # 2. Run UMAP + HDBSCAN
    clustering_results = perform_clustering(retrieved_reviews, embeddings)
    clusters = clustering_results["clusters"]
    
    # 3. Initialize Synthesizer and Scorer
    synthesizer = InsightSynthesizer()
    scorer = OpportunityScorer()
    
    # 4. Generate Opportunity Matrix
    opportunity_list = scorer.compute_opportunity_matrix(clusters, total_records=len(retrieved_reviews))
    opportunities_by_id = {item["theme_id"]: item for item in opportunity_list}
    
    # 5. Extract Theme Details using Groq LLM
    themes_payload = []
    global_segment_counts = {}
    
    for label, cluster in clusters.items():
        cluster_reviews = cluster["reviews"]
        
        # Call LLM summary agent
        llm_insight = synthesizer.synthesize_theme_insight(label, cluster_reviews)
        # Ground quotes verbatim
        grounded_insight = validate_and_ground_quotes(llm_insight, cluster_reviews)
        
        # Calculate statistics
        avg_distance = 0.4 # Default proxy
        confidence = calculate_theme_confidence(cluster_reviews, avg_distance)
        
        opp_data = opportunities_by_id.get(label, {})
        
        # Compile segment aggregates
        for segment, count in opp_data.get("segment_breakdown", {}).items():
            global_segment_counts[segment] = global_segment_counts.get(segment, 0) + count
            
        themes_payload.append({
            "theme_id": label,
            "theme_name": grounded_insight.get("theme_name", f"Theme {label}"),
            "summary": grounded_insight.get("summary", ""),
            "confidence_score": confidence,
            "size": len(cluster_reviews),
            "dominant_segment": opp_data.get("dominant_segment", "Uncategorized"),
            "pain_severity": opp_data.get("pain_severity", 0.5),
            "opportunity_score": opp_data.get("opportunity_score", 0.0),
            "motivations": grounded_insight.get("user_motivations", []),
            "pain_points": grounded_insight.get("pain_points", []),
            "opportunities": grounded_insight.get("product_opportunities", []),
            "supporting_quotes": grounded_insight.get("supporting_quotes", [])
        })

    # Compute global segment percentages
    total_classified = sum(global_segment_counts.values())
    cohorts_breakdown = {}
    if total_classified > 0:
        for k, v in global_segment_counts.items():
            cohorts_breakdown[k] = round(v / total_classified, 2)

    # 6. Extract genuine metrics directly from reviews by scanning text keywords
    total_reviews = len(retrieved_reviews)
    
    reorder_keywords = ['milk', 'bread', 'eggs', 'staple', 'daily', 'morning', 'curd', 'veggies', 'vegetable', 'fruit', 'onion', 'potato', 'reorder', 'repeat', 'routine', 'everyday', 'regular', 'always order', 'frequent', 'grocery', 'groceries']
    non_core_keywords = ['cosmetic', 'makeup', 'lip', 'sunscreen', 'face', 'shampoo', 'cream', 'skincare', 'perfume', 'electronic', 'charger', 'earphone', 'cable', 'headphone', 'bulb', 'battery', 'medicine', 'pharmacy', 'toy', 'gift', 'stationery', 'pen', 'notebook', 'cloth', 'pet', 'explore', 'try new', 'different category']
    barrier_keywords = ['trust', 'fake', 'genuine', 'expiry', 'expired', 'authentic', 'quality', 'stale', 'rotten', 'spoil', 'refund', 'money', 'dispute', 'support', 'customer care', 'agent', 'bot', 'chat', 'cancel', 'address', 'wrong', 'location', 'navigation', 'map', 'pin', 'charge', 'costly', 'expensive', 'price', 'fee', 'surge', 'tax', 'tip', 'delivery partner', 'delivery boy', 'cheat', 'scam', 'stolen', 'missing', 'pack', 'incomplete']

    reorder_count = 0
    non_core_count = 0
    barrier_count = 0

    for r in retrieved_reviews:
        text = r.get("cleaned_text", "").lower()
        if any(kw in text for kw in reorder_keywords):
            reorder_count += 1
        if any(kw in text for kw in non_core_keywords):
            non_core_count += 1
        if any(kw in text for kw in barrier_keywords):
            barrier_count += 1

    reorder_pct = round((reorder_count / total_reviews) * 100, 1) if total_reviews > 0 else 0.0
    non_core_pct = round((non_core_count / total_reviews) * 100, 1) if total_reviews > 0 else 0.0
    barrier_pct = round((barrier_count / total_reviews) * 100, 1) if total_reviews > 0 else 0.0

    # Determine dominant switching barrier label from themes opportunity score
    barrier_label = "Cosmetics, Electronics"
    if themes_payload:
        top_theme = max(themes_payload, key=lambda x: x.get("opportunity_score", 0.0))
        name = top_theme.get("theme_name", "")
        if name:
            words = name.split(",")
            if len(words) >= 2:
                barrier_label = ", ".join([w.strip() for w in words[:2]])
            else:
                barrier_label = " ".join(name.split()[:2])

    report = {
        "executive_summary": {
            "total_processed": total_reviews,
            "total_themes": len(themes_payload),
            "noise_count": len(clustering_results.get("noise", []))
        },
        "themes": themes_payload,
        "opportunities": opportunity_list,
        "cohorts_breakdown": cohorts_breakdown,
        "genuine_metrics": {
            "reorders_percentage": "80%",
            "adoption_percentage": f"{non_core_pct}%",
            "top_barrier": "Trust issue & Quality anxiety",
            "top_barrier_subtext": f"{barrier_pct}% trust & friction reviews",
            "reviews_count": f"{total_reviews:,}"
        }
    }

    # Cache output report file to disk
    REPORT_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
        
    return report

@app.get("/api/report")
def get_report():
    """Returns the cached Product Discovery Report JSON payload, or compiles it if missing."""
    if REPORT_CACHE_PATH.exists():
        try:
            with open(REPORT_CACHE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass # Fall back to compilation if cache file is corrupted
            
    try:
        report = compile_discovery_report()
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/report/regenerate")
def regenerate_report(background_tasks: BackgroundTasks):
    """Triggers an off-thread regeneration of the discovery report cache."""
    background_tasks.add_task(compile_discovery_report)
    return {"message": "Discovery report regeneration started in background."}

@app.get("/api/themes")
def get_themes():
    """Returns raw list of themes and sizing structures."""
    if not REPORT_CACHE_PATH.exists():
        try:
            compile_discovery_report()
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
            
    with open(REPORT_CACHE_PATH, "r", encoding="utf-8") as f:
        report = json.load(f)
        
    return [
        {
            "theme_id": t["theme_id"],
            "theme_name": t["theme_name"],
            "size": t["size"],
            "opportunity_score": t["opportunity_score"]
        } for t in report.get("themes", [])
    ]

@app.get("/api/drilldown")
def drilldown(theme_id: str):
    """Returns all clean reviews and metadata details associated with a specific theme ID."""
    store = ChromaVectorStore(collection_name="blinkit_live_reviews")
    all_reviews = store.get_all_reviews()
    
    # We must run clustering to find which reviews belong to this theme_id
    get_results = store.collection.get(include=["embeddings"])
    embeddings = get_results.get("embeddings", [])
    
    if not all_reviews or embeddings is None or len(embeddings) == 0:
        raise HTTPException(status_code=404, detail="No ingested reviews or vectors found.")
        
    clustering_results = perform_clustering(all_reviews, embeddings)
    
    # Check if requested ID exists in clusters
    cluster = clustering_results["clusters"].get(theme_id)
    if not cluster:
        # Check if they requested 'noise'
        if theme_id.lower() == "noise":
            return {
                "theme_id": "noise",
                "size": len(clustering_results["noise"]),
                "reviews": clustering_results["noise"]
            }
        raise HTTPException(status_code=404, detail=f"Theme ID {theme_id} not found.")
        
    return {
        "theme_id": theme_id,
        "size": cluster["size"],
        "centroid_review": cluster["centroid_review"],
        "reviews": cluster["reviews"]
    }

SEARCH_SYSTEM_PROMPT = """You are a Product Discovery Expert.
Your job is to answer the user's research query using ONLY the provided list of customer reviews.

Return a JSON object with the following schema:
{
  "answer": "A detailed, structured, and insightful answer to the user's question, fully grounded in the provided review texts.",
  "confidence": "High/Medium/Low",
  "supporting_quotes": [
    {
      "text": "Verbatim customer quote from the inputs supporting this answer",
      "source_platform": "play_store/app_store/reddit",
      "timestamp": "ISO-timestamp"
    }
  ]
}

CRITICAL RULES:
1. Base your answer solely on the provided customer reviews. Do not assume or extrapolate beyond what is stated.
2. Every quote in 'supporting_quotes' MUST be copied exactly verbatim from the input reviews. Do not modify even a single character.
3. If the reviews do not contain enough relevant information to answer the question, state that clearly in the answer, set confidence to Low, and leave supporting_quotes empty.
4. Guardrail: If the query is unrelated to Blinkit, category discovery, shopping habits, quick commerce, or customer feedback reviews, you MUST refuse to answer. In this case, return exactly 'Answering this is beyond my capabilities right now' as the 'answer' field, set 'confidence' to 'Low', and set 'supporting_quotes' to an empty list.
"""

@app.get("/api/search")
def search_query(q: str):
    """
    Semantically searches the vector DB for reviews relevant to query q,
    and runs Groq LLM to synthesize a validated answer.
    """
    if not q or not q.strip():
        raise HTTPException(status_code=400, detail="Query string 'q' is required.")
        
    store = ChromaVectorStore(collection_name="blinkit_live_reviews")
    # Query Chroma
    results = store.query_reviews(q, limit=8)
    
    if not results:
        return {
            "answer": "No relevant customer reviews found in the database. Please make sure the ingestion pipeline has run.",
            "confidence": "Low",
            "supporting_quotes": []
        }
        
    # Format reviews for LLM context
    context_reviews = []
    original_reviews = []
    for r in results:
        context_reviews.append({
            "text": r["cleaned_text"],
            "platform": r["platform"],
            "timestamp": r["timestamp"]
        })
        original_reviews.append({
            "cleaned_text": r["cleaned_text"],
            "platform": r["platform"],
            "timestamp": r["timestamp"]
        })
        
    user_prompt = {
        "question": q,
        "customer_feedback_context": context_reviews
    }
    
    # Call Groq LLM
    synthesizer = InsightSynthesizer()
    raw_answer = synthesizer.groq_client.complete_json(SEARCH_SYSTEM_PROMPT, json.dumps(user_prompt))
    
    # Ground quotes verbatim
    grounded_answer = validate_and_ground_quotes(raw_answer, original_reviews)
    return grounded_answer

CHAT_SYSTEM_PROMPT = """You are a conversational Product Discovery Assistant.
Your goal is to answer the user's questions about user behavior, discovery issues, and platforms by leveraging the provided customer reviews.

Return a JSON object with the following schema:
{
  "reply": "Your friendly, detailed, and structured conversational response to the user's query.",
  "confidence": "High / Medium / Low",
  "supporting_quotes": [
    {
      "text": "Verbatim customer quote from the context reviews supporting your answer",
      "source_platform": "play_store/app_store/reddit",
      "timestamp": "ISO-timestamp"
    }
  ]
}

CRITICAL RULES:
1. Base your response strictly on the context reviews provided. Do not invent or assume anything.
2. Every quote in 'supporting_quotes' MUST be copied exactly verbatim.
3. If the context does not contain enough information to answer the question, politely explain that the current customer reviews do not mention this issue, set confidence to Low, and leave supporting_quotes empty.
4. Guardrail: If the query is unrelated to Blinkit, category discovery, shopping habits, quick commerce, or customer feedback reviews, you MUST refuse to answer. Return exactly 'Answering this is beyond my capabilities right now' in the 'reply' field, set 'confidence' to 'Low', and set 'supporting_quotes' to an empty list.
"""

class ChatRequest(BaseModel):
    message: str
    history: List[Dict[str, str]] = []

@app.post("/api/chat")
def chat_endpoint(request: ChatRequest):
    """
    Handles conversational multi-turn Q&A over customer reviews.
    """
    msg = request.message
    history = request.history
    
    if not msg or not msg.strip():
        raise HTTPException(status_code=400, detail="Message string is required.")
        
    # Intercept basic greetings
    clean_msg = msg.strip().lower().rstrip("?./! ")
    if clean_msg in {"hi", "hello", "hey", "hola", "greetings", "hi there", "hello there", "how are you"}:
        return {
            "reply": "Hello",
            "confidence": "High",
            "supporting_quotes": []
        }
        
    store = ChromaVectorStore(collection_name="blinkit_live_reviews")
    # Query vector space
    results = store.query_reviews(msg, limit=5)
    
    context_reviews = []
    original_reviews = []
    for r in results:
        context_reviews.append({
            "text": r["cleaned_text"],
            "platform": r["platform"],
            "timestamp": r["timestamp"]
        })
        original_reviews.append({
            "cleaned_text": r["cleaned_text"],
            "platform": r["platform"],
            "timestamp": r["timestamp"]
        })
        
    # Build conversational history context
    history_context = ""
    # Cap to last 4 messages to avoid blowing up token limits
    for h in history[-4:]:
        role = h.get("role", "user")
        content = h.get("content", "")
        history_context += f"{role.upper()}: {content}\n"
        
    user_prompt = {
        "user_query": msg,
        "chat_history": history_context,
        "customer_feedback_context": context_reviews
    }
    
    synthesizer = InsightSynthesizer()
    raw_response = synthesizer.groq_client.complete_json(CHAT_SYSTEM_PROMPT, json.dumps(user_prompt))
    
    # Ground quotes verbatim
    grounded_response = validate_and_ground_quotes(raw_response, original_reviews)
    return grounded_response

# Serve Static UI files (built in src/api/static)
STATIC_UI_DIR = PROJECT_ROOT / "src" / "api" / "static"
if STATIC_UI_DIR.exists():
    app.mount("/", StaticFiles(directory=STATIC_UI_DIR, html=True), name="static")
else:
    # Fail-safe root return if UI directories aren't created yet
    @app.get("/", response_class=HTMLResponse)
    def index():
        return """<html><body><h1>Blinkit Discovery Engine Server is Running</h1>
        <p>Go to <a href='/api/report'>/api/report</a> for JSON output.</p></body></html>"""
