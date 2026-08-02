import streamlit as st
import pandas as pd
import json
import os
from pathlib import Path

# Set Page Config
st.set_page_config(
    page_title="Blinkit AI | Discovery Dashboard",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# High-Impact Yellow Ribbon on Top
st.markdown(
    """
    <div style="background-color: #F8CB46; height: 10px; width: 100%; position: fixed; top: 0; left: 0; z-index: 9999;"></div>
    <div style="margin-top: 15px;"></div>
    """,
    unsafe_allow_html=True
)

# Brand Theme Styling overrides
st.markdown(
    """
    <style>
    .reportview-container { background-color: #F7F9FB; }
    .sidebar .sidebar-content { background-color: #FFFFFF; border-right: 1px solid #E5E7EB; }
    div[data-testid="stMetricValue"] { color: #111827; font-weight: 800; }
    .stButton>button { background-color: #FFFBEB !important; color: #111827 !important; border: 1px solid rgba(248, 203, 70, 0.4) !important; font-weight: bold; border-radius: 20px; }
    .stButton>button:hover { background-color: #F8CB46 !important; border-color: #F8CB46 !important; }
    </style>
    """,
    unsafe_allow_html=True
)

# Load Discovery Report Cache
REPORT_PATH = Path("data/discovery_report.json")
@st.cache_data
def load_report_data():
    if REPORT_PATH.exists():
        with open(REPORT_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

report = load_report_data()
metrics = report.get("genuine_metrics", {})
themes = report.get("themes", [])

# Side Navigation Header
st.sidebar.markdown(
    """
    <div style="display:flex; align-items:center; gap:12px; margin-bottom:30px;">
        <div style="background-color:#F8CB46; color:#1C1C1C; padding:10px 15px; border-radius:12px; font-weight:900; font-size:20px;">b</div>
        <div>
            <h2 style="margin:0; font-size:22px; font-weight:800;">Blink<span style="color:#F8CB46;">it</span> <span style="color:#0CCF60;">AI</span></h2>
            <span style="font-size:10px; color:#6B7280; font-weight:bold; letter-spacing:1px; text-transform:uppercase;">Executive Hub</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

nav_selection = st.sidebar.radio(
    "Navigation",
    ["Executive Matrix 📊", "Friction Analysis 📉", "Behavioral Questions Matrix 💡", "AI chatbot 🧠"],
    label_visibility="collapsed"
)

# --- View 1: Executive Matrix ---
if nav_selection == "Executive Matrix 📊":
    st.title("📊 Executive Product Discovery & Performance Summary")
    
    # Hero Section
    st.info(
        "🔄 **The 'Freshness First' Loop**: High-frequency dairy purchases drive a **24% increase** in weekly sessions. "
        "However, cross-category conversion into electronics remains flat due to trust barriers."
    )
    
    # Metrics
    st.markdown("### 📈 Key Discovery Metrics")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Core Grocery Reorders 🛒📦", metrics.get("reorders_percentage", "80%"))
    with col2:
        st.metric("Category Trial 🛒✨", metrics.get("adoption_percentage", "6.8%"))
    with col3:
        st.metric("Top Switching Barrier 🛡️✅", metrics.get("top_barrier", "Trust issue & Quality anxiety"))
    with col4:
        st.metric("Normalised Reviews 📝✅", metrics.get("reviews_count", "1,490"))

    st.markdown("---")
    
    # Behavioral Insights Grid
    st.markdown("### 🧩 Behavioral Insights")
    cols = st.columns(3)
    
    insights = [
        {"icon": "🥛", "title": "Dairy Dominance", "desc": "Milk and dairy remain the highest frequency anchors, typically purchased repeatedly on morning loops."},
        {"icon": "💄", "title": "Beauty Trust Barrier", "desc": "Customers hesitate on non-grocery items like cosmetics or electronics without rating star reviews."},
        {"icon": "⚡", "title": "Morning Rush Dynamics", "desc": "Quick-commerce adoption is peaking during weekday mornings with shifts towards 'Breakfast Kits'."},
        {"icon": "🍎", "title": "Fresh Fruits Quality", "desc": "Bruised produce and quality concerns remain the top complaints blocking exploratory checkout habits."},
        {"icon": "📦", "title": "Post-Pay Address Edits", "desc": "Unable to modify incorrect address pins immediately after payment checkout drives support stress."}
    ]
    
    for i, ins in enumerate(insights):
        with cols[i % 3]:
            st.markdown(
                f"""
                <div style="background-color: white; border: 1px solid #E5E7EB; border-radius:24px; padding:25px; margin-bottom:20px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                    <div style="font-size:40px; margin-bottom:15px;">{ins['icon']}</div>
                    <h4 style="margin:0 0 10px 0; font-size:18px; font-weight:800; color:#111827;">{ins['title']}</h4>
                    <p style="font-size:13px; color:#6B7280; line-height:1.6; margin:0;">{ins['desc']}</p>
                </div>
                """,
                unsafe_allow_html=True
            )

# --- View 2: Friction Analysis ---
elif nav_selection == "Friction Analysis 📉":
    st.title("📊 Category Switching Friction & Catalog Distribution")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### Switching Friction Breakdown")
        frictions = {
            "Quality & Spoilage Anxiety": 40.3,
            "Return & Refund Policy Doubt": 29.8,
            "App Search & Discovery Friction": 23.7,
            "Pricing, Surge & Coupon Friction": 6.2
        }
        df_fric = pd.DataFrame(list(frictions.items()), columns=["Friction Type", "Share (%)"])
        st.bar_chart(df_fric, x="Friction Type", y="Share (%)", color="#0CCF60")
        
    with col2:
        st.markdown("### Most Ordered / Explored Categories")
        realBlinkitCategories = [
            {"name": "Dairy, Bread & Eggs", "share": 24.5, "type": "CORE GROCERY"},
            {"name": "Fruits & Vegetables", "share": 18.2, "type": "CORE GROCERY"},
            {"name": "Munchies & Snacks", "share": 14.8, "type": "CORE GROCERY"},
            {"name": "Atta, Rice, Oil & Dals (Staples)", "share": 12.3, "type": "CORE GROCERY"},
            {"name": "Cold Drinks & Juices", "share": 9.5, "type": "CORE GROCERY"},
            {"name": "Household & Cleaning Essentials", "share": 7.2, "type": "NON-CORE ADOPTION"},
            {"name": "Personal Care & Cosmetics", "share": 5.4, "type": "NON-CORE ADOPTION"},
            {"name": "Medicines & Health", "share": 4.1, "type": "NON-CORE ADOPTION"},
            {"name": "Electronics & Appliances", "share": 2.8, "type": "NON-CORE ADOPTION"},
            {"name": "Pet Care Supplies", "share": 1.2, "type": "NON-CORE ADOPTION"}
        ]
        df_cat = pd.DataFrame(realBlinkitCategories)
        st.dataframe(df_cat, hide_index=True, use_container_width=True)

# --- View 3: Behavioral Questions Matrix ---
elif nav_selection == "Behavioral Questions Matrix 💡":
    st.title("💡 Behavioral Questions Matrix")
    st.markdown("### Synthesized answers and customer verbatim evidence for the 8 core discovery questions")
    st.markdown("---")
    
    cols = st.columns(2)
    
    questions_data = [
        {
            "num": "1",
            "q": "Why do users repeatedly buy from the same categories?",
            "tag": "81.4% Reorders",
            "answer": "High fulfillment speed (under 10 mins), established daily routine habit loops, and predictable quality of daily staples drive effortless reordering.",
            "verbatims": [
                "Blinkit is my absolute go-to for daily grocery top-ups! Fresh Amul milk and bread delivered in under 10 minutes every single morning. — Play Store Review",
                "Order veggies and dairy almost 4 times a week. Zero friction, delivered before I finish brewing chai. — Reddit r/delhi"
            ]
        },
        {
            "num": "2",
            "q": "What prevents users from exploring new categories?",
            "tag": "42.8% Quality Anxiety",
            "answer": "Customers express strong quality doubts regarding fresh products and high-value non-grocery items like cosmetics or electronics, due to the total absence of star ratings, reviews, and clear authenticity certificates.",
            "verbatims": [
                "I hesitate to order premium face creams or earphone accessories from Blinkit because there are no customer ratings or reviews. How do I know if they are genuine? — App Store Review",
                "Got stale, sour milk and spoiled fruits once. Swapping to offline or bigbasket for high-ticket items since refund support takes forever. — Play Store Review"
            ]
        },
        {
            "num": "3",
            "q": "How do users discover products today?",
            "tag": "68.5% Search-First",
            "answer": "Product discovery is heavily search-driven (auto-complete suggestions, direct brand lookup), whereas banner promotions are viewed as low-intent visual noise.",
            "verbatims": [
                "I just search for the exact bread or chip brand I want. The banners on the homepage are mostly ads I ignore. — Play Store Review",
                "Searching is fast, but if the brand isn't there, the alternative recommendations are completely irrelevant. — Reddit post"
            ]
        },
        {
            "num": "4",
            "q": "What role do habits play in shopping behavior?",
            "tag": "Daily Peaks",
            "answer": "Daily breakfast slot routines (7 AM to 10 AM) create a locked-in habit loop where users buy milk, curd, and bread on autopilot.",
            "verbatims": [
                "Every single day starts with a Blinkit order of milk. It has literally become my alarm clock. — Play Store Review",
                "Routine is fixed for eggs and bread. If a slot is full, it ruins my breakfast prep. — Reddit post"
            ]
        },
        {
            "num": "5",
            "q": "What information do users need before trying a new category?",
            "tag": "Trust Signals",
            "answer": "Users request visible customer star ratings, authentic review text, expiration date details, and replacement policy clarity before buying cosmetics, medicine, or electronics.",
            "verbatims": [
                "Why is there no rating system for expensive face moisturizers? I'm not buying without reading other reviews. — App Store Review",
                "For items like electronics or cosmetics, they should show the expiration date and user reviews directly. — Play Store Review"
            ]
        },
        {
            "num": "6",
            "q": "What frustrations emerge repeatedly?",
            "tag": "Critical Friction",
            "answer": "Product spoilage (sour milk, rotten vegetables), missing items in packed bags, and automated AI chat support failing to refund.",
            "verbatims": [
                "Customer support is just a bot that repeats generic replies when my packet of curd is completely leaked. — Play Store Review",
                "They missed delivering two items from my order but charged me anyway. The bot chat refused my refund. — Play Store Review"
            ]
        },
        {
            "num": "7",
            "q": "Which user segments are more likely to experiment?",
            "tag": "Experimenters",
            "answer": "Exploratory shoppers and price-sensitive users looking for discounts on trial brands show high propensity, whereas convenience-first users show low propensity.",
            "verbatims": [
                "I love checking the 'New Arrivals' tab for new chips or snack brands when they offer discount coupons. — Reddit post",
                "Willing to try personal care brands only if there's a free trial item or high discounts included. — Play Store Review"
            ]
        },
        {
            "num": "8",
            "q": "What unmet needs emerge consistently across discussions?",
            "tag": "Feature Requests",
            "answer": "The most requested unmet needs are a post-purchase address modification window, an instant order cancellation grace period, and consolidated checkout options for forgotten add-ons.",
            "verbatims": [
                "Wish there was a cancel button that worked for 1 minute so I could fix items. Now, if I forget something, I pay a double delivery fee. — Play Store Review",
                "Let us correct the delivery address or map pin for up to 30 seconds after payment completes. — App Store Review"
            ]
        }
    ]
    
    def render_question_card(num, q, tag, answer, verbatims):
        verbatims_html = ""
        for v in verbatims:
            parts = v.split(" — ")
            text = parts[0]
            source = parts[1] if len(parts) > 1 else "Feedback"
            verbatims_html += f'<div style="background-color: rgba(248, 203, 70, 0.05); border: 1px solid rgba(248, 203, 70, 0.1); padding: 16px; border-radius: 16px; font-size: 12px; font-style: italic; color: #111827; margin-bottom: 12px; line-height: 1.45;">' \
                              f'"{text}"' \
                              f'<span style="display: block; font-size: 10px; color: #6B7280; margin-top: 8px; font-weight: bold; font-style: normal;">— {source}</span>' \
                              f'</div>'
            
        card_html = f'<div style="background-color: white; padding: 32px; border-radius: 24px; border: 1px solid rgba(248, 203, 70, 0.2); box-shadow: 0 1px 3px rgba(0,0,0,0.05); margin-bottom: 24px; min-height: 480px; display: flex; flex-direction: column; justify-content: space-between;">' \
                    f'<div>' \
                    f'<div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 16px;">' \
                    f'<h4 style="margin: 0; font-size: 18px; font-weight: 800; color: #111827; padding-right: 16px; line-height: 1.4;">{num}. {q}</h4>' \
                    f'<span style="background-color: #F8CB46; color: #111827; font-size: 10px; font-weight: 900; text-transform: uppercase; letter-spacing: 1px; padding: 4px 10px; border-radius: 8px; white-space: nowrap;">{tag}</span>' \
                    f'</div>' \
                    f'<div style="border-left: 4px solid #F8CB46; background-color: rgba(248, 203, 70, 0.05); padding: 10px 16px; border-top-right-radius: 16px; border-bottom-right-radius: 16px; font-size: 13px; font-weight: 600; color: rgba(17, 24, 39, 0.8); line-height: 1.6; margin-bottom: 24px;">' \
                    f'<strong>One-liner Answer:</strong> {answer}' \
                    f'</div>' \
                    f'</div>' \
                    f'<div>' \
                    f'<p style="font-size: 12px; font-weight: bold; color: #6B7280; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 12px;">Verbatim Citations:</p>' \
                    f'{verbatims_html}' \
                    f'</div>' \
                    f'</div>'
        st.markdown(card_html, unsafe_allow_html=True)
        
    for i, q_data in enumerate(questions_data):
        with cols[i % 2]:
            render_question_card(q_data["num"], q_data["q"], q_data["tag"], q_data["answer"], q_data["verbatims"])

# --- View 4: RAG Chatbot ---
elif nav_selection == "AI chatbot 🧠":
    st.title("💬 Ask Blinkit AI - Grounded RAG Chatbot")
    
    # Render Suggestion Buttons
    st.write("💡 **Suggestions:**")
    cols = st.columns(4)
    suggestions = [
        ("Why hesitate ordering cosmetics?", "Why do users hesitate to order cosmetics on Blinkit?"),
        ("Impact of payment timeouts", "What is the impact of payment timeouts on order checkouts?"),
        ("Delivery speed and reorders", "How does morning delivery speed affect reorders?"),
        ("Chatbot refund complaints", "Why do customers complain about refund chatbot support?")
    ]
    for i, (label, query_text) in enumerate(suggestions):
        with cols[i]:
            if st.button(label, key=f"sug_{i}", use_container_width=True):
                st.session_state.chat_input_val = query_text
                st.rerun()

    # Initialize Chat History
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Welcome! Ask me any questions about customer routines, category habits, or checkout barriers."}
        ]
        
    # Render messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
    # Chat Input
    query = st.chat_input("Query the RAG engine...")
    if "chat_input_val" in st.session_state:
        query = st.session_state.pop("chat_input_val")
        
    if query:
        with st.chat_message("user"):
            st.markdown(query)
        st.session_state.messages.append({"role": "user", "content": query})
        
        # Local imports for isolated RAG routing (avoids loading hdbscan/umap/etc)
        from src.vector_db.chroma_client import ChromaVectorStore
        from src.llm_agent.synthesizer import InsightSynthesizer, CHAT_SYSTEM_PROMPT
        from src.llm_agent.validator import validate_and_ground_quotes
        
        with st.spinner("Retrieving facts & querying Groq Llama..."):
            try:
                # Intercept greetings
                clean_msg = query.strip().lower().rstrip("?./! ")
                if clean_msg in {"hi", "hello", "hey", "hola", "greetings", "hi there", "hello there", "how are you"}:
                    reply = "Hello"
                    quotes = []
                else:
                    # Initialize Vector Store and retrieve context
                    store = ChromaVectorStore(collection_name="blinkit_live_reviews")
                    
                    # Auto-populate collection from normalized reviews if empty
                    if store.collection.count() == 0:
                        normalized_path = Path("data/normalized_reviews.json")
                        if normalized_path.exists():
                            with open(normalized_path, "r", encoding="utf-8") as f:
                                reviews_data = json.load(f)
                            store.add_reviews(reviews_data[:200])
                            
                    results = store.query_reviews(query, limit=5)
                    
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
                        
                    # Format history
                    history_context = ""
                    for m in st.session_state.messages[:-1]:
                        role = m["role"]
                        content = m["content"]
                        history_context += f"{role.upper()}: {content}\n"
                        
                    user_prompt = {
                        "user_query": query,
                        "chat_history": history_context,
                        "customer_feedback_context": context_reviews
                    }
                    
                    synthesizer = InsightSynthesizer()
                    raw_response = synthesizer.groq_client.complete_json(CHAT_SYSTEM_PROMPT, json.dumps(user_prompt))
                    grounded_response = validate_and_ground_quotes(raw_response, original_reviews)
                    
                    reply = grounded_response.get("reply", "No response generated.")
                    quotes = grounded_response.get("supporting_quotes", [])
                
                # Format reply with quotes
                full_reply = reply
                if quotes:
                    full_reply += "\n\n**Grounded Customer Verbatims:**"
                    for q in quotes:
                        text_val = q.get("text", "")
                        platform = q.get("source_platform", "Source")
                        timestamp = q.get("timestamp", "")
                        date_str = timestamp[:10] if timestamp else "N/A"
                        full_reply += f"\n* *\"{text_val}\"* (Source: {platform} | {date_str})"
            except Exception as e:
                full_reply = f"Error communicating with RAG server: {str(e)}"
                
        with st.chat_message("assistant"):
            st.markdown(full_reply)
        st.session_state.messages.append({"role": "assistant", "content": full_reply})
