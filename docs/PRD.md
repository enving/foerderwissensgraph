# Product Requirements Document (PRD): Federal-KG-Crawler

**Project Name:** Federal-KG-Crawler (Internal: Sovereign Knowledge Source)
**Status:** PRD Final (Graph-RAG & Cloud-Hybrid Architecture)
**Vision:** A standalone, open-source tool that crawls the German "Bundes-Formularschrank" (Easy-Online), extracts guidelines using Docling, and builds a versioned Knowledge Graph (NetworkX) + Vector Store (RAG) to provide AI-driven policy compliance.

---

## 🎯 1. Executive Summary
Federal-KG-Crawler solves the "Knowledge Fragmentation" problem in federal funding. It automatically fetches, parses, and networks guidelines so that validation systems (like FAPS) always work against the latest "Source of Truth", with full traceability to the original federal documents.

## 🏗️ 2. Core Architecture

### 2.1 Web Scraping & Discovery (Playwright)
- **Target:** [foerderportal.bund.de](https://foerderportal.bund.de/easy/easy_index.php)
- **Deduplication:** Hash-based check. Only changed PDFs are downloaded.
- **Source-of-Truth:** Every node stores its permanent `source_url` (Direct PDF Link).

### 2.2 Extraction Engine (Docling + Cloud LLM)
- **Local Parsing:** Docling (ThinkPad-friendly sequential mode) extracts structured Markdown.
- **Cloud Extraction:** Uses IONOS/Mistral API to extract structured rules (`RequirementRules`) from MD chunks. 
- **Focus Refinement:** Extraction focuses on **Compliance Rules** (Procurement thresholds, reporting duties, eligibility) and **Data Structures** (Required form fields) found in the "Formularschrank", rather than funding rates (which are usually in call-specific guidelines).

### 2.3 Knowledge Graph & Versioning (NetworkX)
- **Temporal Graph:** Nodes have `valid_from`/`valid_to`.
- **Versioning:** Edges like `SUPERSEDES` link document history.
- **Traceability:** Every node carries the `source_url` from the manifest for direct link preservation.

---

## 🧠 3. Phase D: Graph-RAG Integration

This phase connects the structural knowledge (Graph) with semantic search (RAG).

### 3.1 The Linkage
```python
class RequirementRule(BaseModel):
    id: str
    vector_id: str  # ID in the Vector Database (ChromaDB)
    description: str
    logic_hint: str 
    source_url: HttpUrl
    page_number: int
    context_hierarchy: List[str] # ["BMWK", "ZIM", "Antragsrichtlinie"]
```

### 3.2 Hybrid Retrieval Logic
1.  **Graph Filter:** Identify the relevant sub-graph (e.g., "All active rules for Ministerium X").
2.  **Vector Search:** Perform semantic search via Cloud Embeddings (Mistral/IONOS) *only* within the filtered IDs.
3.  **Graph Expansion:** Include neighbor nodes (Parent headers, related attachments) into the LLM context to prevent "lost-in-chunk" issues.

---

## 🖥️ 4. Resource & Hosting (ThinkPad T450s Optimized)

| Operation | Mode | Resource Footprint |
| :--- | :--- | :--- |
| **Crawling** | Local (Playwright) | Low-Medium (1 Browser Instance) |
| **Parsing** | Local (Docling) | Medium (Sequential: ~4GB RAM) |
| **Embeddings**| **Cloud (Mistral/IONOS)** | **Zero Local CPU** |
| **Hosting** | Local (FastAPI) | Very Low (~2GB RAM) |

---

## 🛠️ 5. Implementation Roadmap

### Phase A: Navigation (Weeks 1-2)
- [ ] Playwright scraper for Easy-Online hierarchy.
- [ ] Versioned PDF archive with hash-deduplication.

### Phase B: Extraction (Weeks 3-4)
- [ ] Docling integration for hierarchical MD.
- [ ] Cloud-based Rule Extraction (Mistral/IONOS).

### Phase C: Knowledge Graph (Weeks 5-6)
- [ ] NetworkX assembly with temporal versioning.
- [ ] Basic API for graph traversal.

### Phase D: Graph-RAG (Weeks 7-8)
- [ ] Vector Database (ChromaDB) indexing via Cloud Embeddings.
- [ ] Hybrid "Graph-first" search implementation.
- [ ] FAPS-Link: API endpoint for "Source-Aware" compliance checking.
