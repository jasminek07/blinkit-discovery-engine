# Deployment Plan: Deploying Blinkit Discovery Engine to Streamlit

This document outlines the deployment plan to port the FastAPI/HTML dashboard of the **Blinkit AI User Discovery Engine** into a unified, pure-Python **Streamlit** application and deploy it to **Streamlit Community Cloud**.

---

## 1. Streamlit Application Blueprint (`app.py`)

Create a new file `app.py` in the root of the project to serve as the unified Streamlit frontend & backend:

```python
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

# Brand Theme Styling overrides
st.markdown(
    """
    <style>
    .reportview-container { background-color: #F7F9FB; }
    .sidebar .sidebar-content { background-color: #FFFFFF; border-right: 1px solid #E5E7EB; }
    div[data-testid="stMetricValue"] { color: #111827; font-weight: 800; }
    .stButton>button { background-color: #0CCF60 !important; color: white !important; font-weight: bold; border-radius: 20px; }
    .stButton>button:hover { border-color: #F8CB46 !important; }
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
    ["Executive Matrix 📊", "Friction Analysis 📉", "AI chatbot 🧠"],
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

# --- View 3: RAG Chatbot ---
elif nav_selection == "AI chatbot 🧠":
    st.title("💬 Ask Blinkit AI - Grounded RAG Chatbot")
    
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
    if query:
        with st.chat_message("user"):
            st.markdown(query)
        st.session_state.messages.append({"role": "user", "content": query})
        
        # Local imports for RAG routing
        from src.api.main import chat_endpoint, ChatRequest
        
        with st.spinner("Retrieving facts & querying Groq Llama..."):
            try:
                # Format conversational history
                formatted_history = []
                for m in st.session_state.messages[:-1]:
                    formatted_history.append({
                        "role": "user" if m["role"] == "user" else "assistant",
                        "content": m["content"]
                    })
                
                result = chat_endpoint(ChatRequest(message=query, history=formatted_history))
                reply = result.get("reply", "No response generated.")
                quotes = result.get("supporting_quotes", [])
                
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
```

---

## 2. Requirements Specifications (`requirements.txt`)

Ensure your `requirements.txt` contains the necessary packages for both backend execution and Streamlit:

```text
streamlit>=1.30.0
fastapi>=0.100.0
uvicorn>=0.20.0
chromadb>=0.4.0
sentence-transformers>=2.2.0
groq>=0.3.0
pandas>=2.0.0
scikit-learn>=1.2.0
umap-learn>=0.5.0
hdbscan>=0.8.0
```

---

## 3. Local Run Configuration

Run the app locally to test correctness before deploying to the cloud:

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Launch Streamlit
streamlit run app.py
```

---

## 4. Deploying to Streamlit Community Cloud

Follow these steps to host your application for free on Streamlit Cloud:

1.  **Commit Code to GitHub**:
    *   Create a public or private GitHub repository.
    *   Commit the project files including `app.py`, `src/`, `data/discovery_report.json`, and `requirements.txt`.
2.  **Sign in to Streamlit Cloud**:
    *   Go to [share.streamlit.io](https://share.streamlit.io) and authenticate with your GitHub account.
3.  **New App Deployment**:
    *   Click the **"Create App"** button.
    *   Select your Repository, Branch (`main` or `master`), and specify the Main file path as `app.py`.
4.  **Configure API Secrets**:
    *   Under the **"Advanced Settings"** menu before deploying, locate the **"Secrets"** input box.
    *   Add your Groq API key:
        ```toml
        GROQ_API_KEY = "your-actual-groq-api-key-here"
        ```
    *   Click **"Save"**.
5.  **Launch**:
    *   Click **"Deploy!"**. Streamlit will provision a container, install your requirements, and make the app live at a public subdomain URL.
