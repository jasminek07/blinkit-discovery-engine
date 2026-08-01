# Implementation Plan: AI-Powered User Discovery Engine

This implementation plan outlines the phase-wise development roadmap for building, testing, and deploying the **AI-Powered User Discovery Engine**. Each phase specifies clear tasks, technical components, and verification steps.

---

## 1. Project Implementation Roadmap

```mermaid
gantt
    title Implementation Roadmap
    dateFormat  YYYY-MM-DD
    section Setup & Pipeline
    Phase 1: Project Setup           :active, p1, 2026-08-01, 4d
    Phase 2: Data Ingestion Pipeline : p2, after p1, 7d
    section Machine Learning & AI
    Phase 3: Vector Storage & DB     : p3, after p2, 5d
    Phase 4: Clustering & Topic Modeling: p4, after p3, 6d
    Phase 5: LLM Engine & Validation : p5, after p4, 7d
    section Features & Interface
    Phase 6: User Segmentation Engine: p6, after p5, 5d
    Phase 7: API & Web Dashboard UI : p7, after p6, 8d
```

---

## 2. Phase-by-Phase Execution Plan

### Phase 1: Project Initialization & Environment Setup (4 Days)
* **Goal**: Establish the repository layout, package dependency files, configuration managers, and test runner configurations.
* **Tasks**:
  1. Set up the directory structure:
     ```bash
     ├── config/             # Config files, env loaders
     ├── src/
     │   ├── ingestion/      # Scraping & cleaning scripts
     │   ├── vector_db/      # Embeddings, vector storage connection
     │   ├── modeling/       # UMAP + HDBSCAN clustering
     │   ├── llm_agent/      # LLM inference, prompting, validation
     │   ├── classification/ # User segmentation logic
     │   ├── api/            # FastAPI controllers
     │   └── ui/             # Dashboard source files
     ├── tests/              # Pytest files (unit/integration)
     └── requirements.txt
     ```
  2. Create configuration loader `src/config.py` using `python-dotenv` or `Pydantic-settings` to manage API keys (OpenAI, Reddit PRAW, database credentials).
  3. Initialize base dependencies in `requirements.txt` (including `pytest`, `pandas`, `pydantic`, `fastapi`, `chromadb`, `numpy`, `umap-learn`, `hdbscan`, `openai`).
* **Verification**: Run `pytest tests/` to confirm that the test framework is properly configured and that environment variables are loaded successfully.

---

### Phase 2: Ingestion & Normalization Layer (7 Days)
* **Goal**: Build modular collector to scrape Google Play Store reviews for the past three months and implement a text normalization queue.
* **Tasks**:
  1. Implement scraping modules:
     * **Play Store Scraper**: Connect using `google-play-scraper` and fetch reviews in paginated batches, stopping once a review's timestamp is older than the 3-month cutoff date.
     * **Source Scope**: Stick exclusively to Google Play Store reviews to improve data quality and relevancy.
  2. Build the cleaning filter pipeline:
     * Remove HTML tags, markdown noise, links, and duplicate entries using MinHash.
     * Apply language filtering (`langdetect`) to isolate English and Hinglish content.
     * Implement Regex/NER rules to scrub PII data (phone numbers, addresses, account/UPI details).
* **Verification**: Create mock test suites checking that raw posts containing PII are correctly anonymized and that duplicate/short comments are successfully discarded.

---

### Phase 3: Vector Storage & Database Indexing (5 Days)
* **Goal**: Set up vector storage to generate and save text embeddings and associate metadata records.
* **Tasks**:
  1. Implement the embedding client wrapper using the local `BAAI/bge-small-en-v1.5` SentenceTransformers model to run local, fast, and highly performant vector generation.
  2. Configure `ChromaDB` (or `Qdrant`) as the primary data store.
  3. Define the metadata collection schema to save alongside vectors:
     ```json
     {
       "source_id": "string",
       "platform": "string",
       "timestamp": "ISO-8601",
       "cleaned_text": "string",
       "author_anonymized": "string"
     }
     ```
  4. Write utility scripts to query the database using cosine similarity.
* **Verification**: Ingest 100 sample documents, search for a semantic concept (e.g., *"slow delivery"*), and verify that relevant entries are returned based on cosine distance.

---

### Phase 4: Clustering & Topic Modeling Engine (6 Days)
* **Goal**: Group semantic vectors into unsupervised topics representing core behavioral patterns using UMAP and HDBSCAN.
* **Tasks**:
  1. Implement the dimensionality reduction pipeline using `umap-learn` to project embeddings down to 5 dimensions. Ensure UMAP parameters adjust dynamically: `n_neighbors = min(15, total_records - 1)` to prevent system crashes on small run slices.
  2. Run density-based clustering using `hdbscan` on the reduced vector space.
  3. Tune hyperparameters: Configure HDBSCAN to scale dynamically based on dataset size ($N$):
     * If $N < 100$: use `min_cluster_size = 3` and `min_samples = 1`.
     * If $100 \le N < 1000$: use `min_cluster_size = 10` and `min_samples = 3`.
     * If $N \ge 1000$: use `min_cluster_size = 15` and `min_samples = 5`.
  4. Identify noise records (labeled as `-1` by HDBSCAN) and isolate them. Extract centroids and identify nearest representative text points.
* **Verification**: Log clustering details showing cluster distribution, number of clusters detected, and percentage of noise data. Verify that documents in a test cluster share top keywords.

---

### Phase 5: LLM-Based Insight Extraction & Grounding (7 Days)
* **Goal**: Process clustered feedback documents using LLMs to extract themes and opportunities, while validating the quotes against source files. Enforce optimization strategies for Groq's `llama-3.3-70b-versatile` API limits (30 RPM, 1K RPD, 12K TPM, 100K TPD).
* **Tasks**:
  1. Integrate Groq client API configured with the `llama-3.3-70b-versatile` model.
  2. Implement **API Rate Limiter & Token Budgeting** wrapper:
     * Restrict requests to $< 30$ RPM using sleep delays or token buckets.
     * Capping the context inputs (e.g., maximum 20 representative reviews per cluster) to stay safely within the 12K TPM and 100K daily token budget limits.
  3. Design LLM prompt templates instructing the model to summarize a cluster's text records into a structured JSON schema (Theme Name, motivations, pain points, ranked opportunities).
  4. Configure structured JSON outputs from the LLM.
  5. Implement the Quote Verification Engine:
     * Parse quotes generated by the LLM.
     * Perform string checks against original source documents to prevent hallucinations.
  6. Implement the Confidence Score calculation algorithm using cluster size, platform diversity, and vector density.
* **Verification**: Run integration tests checking that if an LLM generates a hallucinated quote, the validation pipeline flags the issue and swaps it with verbatim document text. Also verify that batch LLM query runs throttles requests below 30 RPM.

---

### Phase 6: User Segmentation & Opportunity Detection (5 Days)
* **Goal**: Classify customers into behavioral groups and build the opportunity matrix to identify critical gaps.
* **Tasks**:
  1. Implement zero-shot classifiers (e.g., using Hugging Face pipeline) or LLM routing functions to tag texts with behavioral markers (e.g., *habitual repeat buyer*, *exploratory shopper*, *price-sensitive*).
  2. Calculate segment proportions within each theme to identify which segments dominate specific pain points.
  3. Build the Opportunity Scoring script to rank opportunities based on pain severity and reach metrics.
* **Verification**: Run tests against annotated customer records to confirm that the classification engine categorizes users with $\ge 85\%$ accuracy.

---

### Phase 7: Backend Service & Interactive Dashboard UI (8 Days)
* **Goal**: Build the FastAPI server layer and construct the web-based reporting UI.
* **Tasks**:
  1. Implement FastAPI API endpoints:
     * `/api/report`: Returns the compiled Product Discovery Report JSON payload.
     * `/api/themes`: Returns lists of themes, cluster sizes, and details.
     * `/api/drilldown?theme_id=x`: Returns raw feedback records and metadata for a specific theme.
  2. Build a minimal, modern web dashboard UI (using HTML/JS/CSS or React) containing:
     * Visual charts showing segment distribution and theme sizes.
     * An expandable list of major behavioral themes.
     * High-confidence user quote cards.
     * Priority rankings for product opportunities.
* **Verification**: Run integration tests on API endpoints to verify $\le 200\text{ms}$ response times and validate layout responsiveness in standard web browsers.

---

### Phase 8: Conversational RAG Chatbot Integration (5 Days)
* **Goal**: Build conversational search query endpoints and split the UI dashboard to support a multi-turn chat widget with preset questions.
* **Tasks**:
  1. Implement `/api/chat` POST endpoint accepting custom queries and conversational history.
  2. Perform context review lookup in ChromaDB (capping at top 5 items for token budgeting) and construct conversation prompts.
  3. Query Groq client returning structured answer payloads and ground quotes verbatim using verification guards.
  4. Design Tabbed panels on the UI frontend (Discovered Themes vs. Conversational Chatbot).
  5. Add suggestion lists for the 8 core preset research questions.
* **Verification**: Run integration tests using TestClient verifying chat endpoints, conversation thread preservation, and verbatim evidence quote matching.

---

## 3. Maintenance & Continuous Monitoring
Following implementation, the system will support:
1. **Incremental Updates**: Running new batches of ingestion daily to keep the vector database updated.
2. **Cluster Drift Logging**: Alerting product managers if new clusters or themes emerge that do not align with existing categories.
