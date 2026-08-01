# Edge Case & Corner Case Matrix: AI-Powered Discovery Engine

This document outlines the edge cases, system failure modes, data anomalies, and mitigation strategies for the **AI-Powered User Discovery Engine**. Implementing these safeguards ensures the reliability and consistency of generated insights.

---

## 1. Data Ingestion & Preprocessing Edge Cases

### 1.1 IP Blocks, Captchas, and API Rate Limits
* **Scenario**: Scrapers for Google Play Store, App Store, or Reddit encounter IP bans, Captchas, or HTTP 429 (Too Many Requests) errors, resulting in empty or partial datasets.
* **Impact**: Downstream analysis is starved of data; daily report metrics drop significantly or fail to generate.
* **Mitigation**:
  * Implement exponential backoff retry mechanisms.
  * Use rotated proxy networks for scrapers.
  * Implement fallback logic that falls back to the previous day's database cache and logs warning flags on the dashboard.

### 1.2 "Hinglish" and Multi-lingual Sentiment Translation
* **Scenario**: Reviews containing code-switched text (e.g., *"delivery to quick tha par quality bad nikli"*) are rejected by English-only language filters or produce low-quality vector representations.
* **Impact**: Valuable behavioral insights from the Indian consumer demographic are lost.
* **Mitigation**:
  * Configure the language detector to allow Romanized Hindi ("Hinglish").
  * Use a multilingual embedding model (e.g., `sentence-transformers/LaBSE` or multilingual OpenAI models) that maps Hinglish and English text to a shared vector space.

### 1.3 PII Bypass through Non-Standard Text Formatting
* **Scenario**: Users post personal info using obfuscation (e.g., spelling out numbers: *"call me at nine-eight-seven-six-five..."* or entering spacing *"P h o n e : 9 8 7 6"*).
* **Impact**: Personal Identifiable Information (PII) is stored in the vector database and could be surfaced in LLM reports, causing compliance violations (GDPR/DPDP).
* **Mitigation**:
  * Run advanced Named Entity Recognition (NER) models specifically trained on unstructured Indian addresses and name formats.
  * Enforce secondary pattern matching that checks for spaced numerical sequences and redacts them.

---

## 2. Clustering & Dimensionality Reduction Edge Cases

### 2.1 The "Noise-Only" Clustering Output (Over-filtering)
* **Scenario**: Vector similarity is low across the board, causing HDBSCAN to label $\ge 90\%$ of feedback records as noise (label `-1`).
* **Impact**: No themes are generated, and the dashboard displays an empty report.
* **Mitigation**:
  * Implement dynamic hyperparameter tuning: if the noise ratio is $> 70\%$, automatically lower the `min_cluster_size` and increase UMAP `n_neighbors` to find local densities.
  * Flag the noise ratio on the system health dashboard.

### 2.2 The Mega-Cluster Phenomenon
* **Scenario**: A single massive cluster emerges containing $> 80\%$ of all records (e.g., generic complaints like *"late delivery"* or *"app not working"*), obscuring smaller, high-value exploratory insights.
* **Impact**: Specific discovery barriers are buried under general transactional complaints.
* **Mitigation**:
  * Implement hierarchical clustering. For any cluster exceeding $30\%$ of the corpus size, re-run UMAP + HDBSCAN recursively on that sub-corpus to split it into granular sub-themes.

### 2.3 Theme Drift (Temporal Inconsistency)
* **Scenario**: During daily updates, themes merge or split dynamically (e.g., *"Price Sensitivity"* and *"Coupon Issues"* are separate on Monday, merge on Tuesday, and split on Wednesday).
* **Impact**: Product Managers get confused when tracking the lifecycle of specific opportunities.
* **Mitigation**:
  * Track cluster centroid similarity over time.
  * Map current cluster centroids to historical centroids using cosine similarity. If similarity is $> 0.85$, preserve the historical `Theme ID` and name to ensure tracking consistency.

---

## 3. LLM Generation & Hallucination Guard Edge Cases

### 3.1 Quote Fabrication / Hallucination
* **Scenario**: The LLM synthesizes summary reports and invents realistic-sounding user quotes that do not exist in the raw dataset, or concatenates statements from different users.
* **Impact**: Decreases system credibility. PMs could act on falsified customer claims.
* **Mitigation**:
  * **Verbatim Verification**: Parse LLM quotes and check them using substring search against the raw feedback database.
  * If a quote fails verbatim matching, execute fuzzy string matching (Levenshtein distance). If it falls below a $95\%$ threshold, discard the quote and automatically fetch the record closest to the cluster centroid.

### 3.2 Polarized Clusters (Contradictory Opinions)
* **Scenario**: A cluster contains strongly opposing view points (e.g., 50% of users love a UI change, 50% hate it). The LLM summary glosses over the split and presents a unified consensus.
* **Impact**: Skewed market feedback is delivered to the product team.
* **Mitigation**:
  * Include prompt instructions asking the LLM to explicitly search for and document split opinions: *"If there are opposing viewpoints, create a 'Contradictions' list and present quotes from both sides."*

### 3.3 LLM Context Window Overflow
* **Scenario**: A detected theme contains $10,000$ reviews. Passing all clean reviews directly into the LLM context window exceeds model limits or incurs high token costs.
* **Impact**: Pipeline crashes due to context limit errors, or API costs spike.
* **Mitigation**:
  * Sample the dataset: pass only the top $30$ documents closest to the cluster centroid, alongside a representative sample of outlier comments within the cluster.

---

## 4. Classification & Segmentation Edge Cases

### 4.1 Low-Confidence Segment Classifications
* **Scenario**: A user review is extremely brief or ambiguous (e.g., *"ok app"* or *"nice"*). The zero-shot classifier tags it with very low probability ($< 30\%$) to multiple segments.
* **Impact**: Users are misclassified, leading to incorrect segment proportion reporting.
* **Mitigation**:
  * Establish a classification confidence threshold (e.g., $55\%$). If the classifier's top probability is below this threshold, classify the user segment as *"Uncategorized/General"* to avoid skewing metrics.
