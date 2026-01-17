# State-of-the-Art Graph RAG Implementation Plan
**Version:** 2.0.0
**Project:** Bund-ZuwendungsGraph
**Date:** 2026-01-17
**Scope:** Complete 6-Phase Implementation

---

## Executive Summary

Transform the current multi-hop retrieval system into a **State-of-the-Art Graph RAG** with:
- **Hybrid Retrieval:** BM25 (sparse) + BGE-M3 (dense) + Reciprocal Rank Fusion
- **Advanced Reranking:** Cross-encoder for German legal text
- **Graph Intelligence:** Personalized PageRank, k-hop expansion, temporal reasoning
- **Query Enhancement:** Multi-query generation, HyDE, decomposition
- **Self-Reflective RAG:** Iterative refinement with confidence scoring
- **Full Explainability:** Provenance tracking, graph path visualization, attribution scores

**Target Improvements:**
- Hit@10: 75% → **90%**
- MRR: 0.55 → **0.70**
- Answer Quality: +30% (measured by ROUGE-L)
- Memory Budget: <800MB (within 4GB VPS limit)

---

## Current Architecture Analysis

### Existing Components
- **Vector Store:** ChromaDB with BAAI/bge-m3 embeddings (IONOS API)
- **Graph:** NetworkX MultiDiGraph (107k HAS_CHUNK, 129 REFERENCES, 14 SUPERSEDES, 8 EQUIVALENT_TO edges)
- **Retrieval:** Simple hybrid (0.7 semantic + 0.3 degree-based graph score)
- **Multi-Hop:** 1-hop neighbor traversal for REFERENCES edges
- **LLM:** IONOS mistral-large-latest via API

### Pain Points
1. **Low recall** for keyword-heavy queries (missing BM25)
2. **No reranking** - semantic search misranks German legal terminology
3. **Simple graph scoring** - degree-based instead of PageRank
4. **No query understanding** - users must formulate perfect queries
5. **Limited explainability** - no provenance or graph path visualization
6. **Temporal issues** - sometimes returns superseded documents

---

## Implementation Phases

### Phase 1: Hybrid Retrieval Foundation (Week 1) 🎯 HIGH IMPACT

#### Deliverables
1. **BM25 Sparse Retrieval**
   - Library: `rank-bm25==0.2.2`
   - German tokenization with SpaCy (`de_core_news_sm`)
   - Persistent index (pickle): `data/bm25_index.pkl`
   - Memory: +50MB, Latency: <100ms

2. **Reciprocal Rank Fusion (RRF)**
   - Combine BM25 + Vector results
   - Formula: `score(d) = sum(1 / (k + rank_i(d)))` where k=60
   - Top 20 from each retriever → Top 20 fused

3. **Cross-Encoder Reranking**
   - Model: `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1` (multilingual, German-optimized)
   - Lazy loading: only initialize on first use
   - Top 20 fused → Top 10 reranked
   - Memory: +120MB (lazy), Latency: ~150ms

#### Files
**New:**
- `src/parser/bm25_index.py` - BM25 index builder and search
- `src/parser/reranker.py` - Cross-encoder reranking

**Modified:**
- `src/parser/hybrid_search.py` - Integrate BM25 + RRF + reranking
- `requirements.txt` - Add dependencies

#### Code Structure
```python
class HybridSearchEngine:
    def search(self, query: str, limit: int = 5):
        # Step 1: Multi-retrieval
        vector_results = self.vector_store.query(query, n_results=20)
        bm25_results = self.bm25_index.search(query, k=20)

        # Step 2: RRF Fusion
        fused = self._reciprocal_rank_fusion([vector_results, bm25_results])

        # Step 3: Cross-Encoder Reranking
        reranked = self.reranker.rerank(query, fused, top_k=10)

        # Step 4: Graph expansion (existing multi-hop logic)
        # ...
```

#### Success Metrics
- Hit@10: 75% → **82%**
- MRR: 0.55 → **0.63**
- Recall improvement: +25% for keyword queries

---

### Phase 2: Graph Intelligence (Week 2) 🎯 HIGH IMPACT

#### Deliverables
1. **Personalized PageRank (PPR)**
   - Subgraph extraction starting from query-relevant chunks
   - Top-k nodes by PPR score (default k=50, threshold=0.0001)
   - Cache global PageRank for 1 hour
   - Time: ~200-500ms for 100k node graph

2. **Smart k-Hop Expansion**
   - Filter by edge type (REFERENCES, SUPERSEDES)
   - Temporal ordering: always follow SUPERSEDES to newest version
   - Max node limit to prevent explosion (default 100 nodes)

3. **Centrality-Based Scoring**
   - Replace degree-based scoring with combined:
     - 70% PageRank (global importance)
     - 30% Degree centrality (local connectivity)

4. **Temporal Reasoning**
   - Auto-detect superseded documents
   - Follow SUPERSEDES chain to newest version
   - Version warning in results

#### Files
**New:**
- `src/graph/graph_algorithms.py` - PPR, k-hop, centrality, temporal filtering

**Modified:**
- `src/parser/hybrid_search.py` - Use graph algorithms for expansion

#### Code Structure
```python
class GraphAlgorithms:
    def personalized_pagerank(self, seed_nodes: List[str]) -> Dict[str, float]:
        """PPR starting from query-relevant chunks"""

    def extract_ppr_subgraph(self, seed_nodes: List[str], top_k: int = 50) -> nx.DiGraph:
        """Extract most relevant subgraph by PPR score"""

    def smart_k_hop_expansion(self, seed_nodes: List[str], k: int = 2) -> Set[str]:
        """Intelligent k-hop with edge filtering and temporal ordering"""

    def apply_temporal_filter(self, node_ids: List[str]) -> List[str]:
        """Remove superseded docs, return only newest versions"""
```

#### Success Metrics
- Answer completeness: +20%
- Temporal correctness: 100% (no superseded docs in top results)
- Graph coverage: 30% of relevant nodes explored

---

### Phase 3: Query Enhancement (Week 3) 🟡 MEDIUM IMPACT

#### Deliverables
1. **Multi-Query Generation**
   - LLM generates 2-3 query variations
   - Synonyms, formality levels, broader/narrower terms
   - RRF fusion across all query results
   - Trigger: queries with >3 words

2. **HyDE (Hypothetical Document Embeddings)**
   - Generate hypothetical answer in legal language
   - Search for documents similar to hypothetical answer
   - Better for specific legal terminology
   - Trigger: queries containing law abbreviations (BHO, VwVfG, etc.)

3. **Query Decomposition**
   - Break complex questions into sub-queries
   - Answer each sub-query independently
   - Combine results
   - Trigger: multi-part questions (detected by LLM)

#### Files
**New:**
- `src/parser/query_enhancer.py` - Multi-query, HyDE, decomposition

**Modified:**
- `src/parser/hybrid_search.py` - Conditional query enhancement

#### Code Structure
```python
class QueryEnhancer:
    def generate_multi_queries(self, query: str, num_queries: int = 3) -> List[str]:
        """Generate query variations using LLM"""

    def generate_hyde_document(self, query: str) -> str:
        """Generate hypothetical legal text answering the query"""

    def decompose_query(self, query: str) -> List[str]:
        """Break complex questions into sub-queries"""
```

#### Success Metrics
- Complex query accuracy: +15%
- Recall for legal terminology: +10%
- Latency: +500-1000ms (acceptable for quality gain)

---

### Phase 4: Self-Reflective & Corrective RAG (Week 4-5) 🟡 MEDIUM IMPACT

#### Deliverables
1. **Self-Reflective RAG**
   - LLM evaluates if retrieved context is sufficient
   - If insufficient: generate follow-up query, expand graph, retry
   - Max 3 iterations
   - Trigger: confidence score <0.7 or user-requested detailed answer

2. **CRAG (Corrective RAG)**
   - LLM evaluates retrieval quality before answering
   - If low relevance: switch strategy (BM25-heavy, k-hop expansion, HyDE)
   - Diagnosis: too_broad, too_narrow, wrong_domain
   - Automatic correction

3. **Confidence Scoring**
   - 0.0-1.0 score based on:
     - Retrieval quality
     - Context sufficiency
     - LLM certainty
   - Expose in API response

#### Files
**New:**
- `src/parser/reflective_rag.py` - Self-reflection, CRAG, confidence scoring

**Modified:**
- `src/api/search_api.py` - New `/api/search/advanced` endpoint with reflection

#### Code Structure
```python
class ReflectiveRAG:
    def answer_with_reflection(self, query: str, max_iterations: int = 3) -> Dict:
        """Iterative retrieval with self-reflection"""
        for iteration in range(max_iterations):
            results = self.engine.search(...)
            answer = self.llm.generate_answer(query, results)
            reflection = self._reflect_on_answer(query, answer, results)

            if reflection['is_complete']:
                return {"answer": answer, "confidence": reflection['confidence']}
            # else: expand context and retry

    def answer_with_correction(self, query: str) -> Dict:
        """CRAG: Evaluate and correct retrieval before answering"""
```

#### Success Metrics
- Ambiguous query accuracy: +15%
- Confidence calibration: 90% accuracy (high confidence → correct answer)
- Latency: +1-3s for flagged queries only

---

### Phase 5: Explainability & Provenance (Week 6) 🎯 HIGH VALUE

#### Deliverables
1. **Graph Path Visualization**
   - Show retrieval path: `Query → Chunk[AZA] --REFERENCES--> Law[BHO] --HAS_CHUNK--> Chunk[§44]`
   - Display edge types and hop distance
   - Frontend visualization (D3.js compatible format)

2. **Attribution Scores**
   - Per-chunk contribution to final answer
   - SHAP-like scoring: which chunks influenced answer most
   - Display top 3 sources with scores

3. **Version Warnings**
   - Detect if any referenced document is superseded
   - Show: "This document was replaced by [Newer Version] on [Date]"
   - Auto-link to newest version

4. **Provenance Metadata**
   - Graph exploration stats (nodes explored, edges traversed)
   - Retrieval strategy used (PPR, k-hop, community)
   - Iteration count (if reflective RAG used)

#### Files
**New:**
- `src/parser/provenance_tracker.py` - Attribution scores, path tracing

**Modified:**
- `src/parser/hybrid_search.py` - Add provenance to results
- `src/api/search_api.py` - Return provenance in response

#### API Response Format
```json
{
  "answer": "Der Schwellenwert für Vergaben beträgt 1000 Euro (§5 AZA).",
  "results": [...],
  "provenance": {
    "primary_sources": [
      {
        "chunk_id": "0027_chunk_45",
        "title": "AZA §5.1 Vergaberecht",
        "contribution_score": 0.85,
        "path_from_query": "Query → Vector Match → Chunk"
      },
      {
        "chunk_id": "law_BHO_chunk_3",
        "title": "BHO §44",
        "contribution_score": 0.52,
        "path_from_query": "Query → AZA → REFERENCES → BHO → Chunk"
      }
    ],
    "graph_exploration": {
      "nodes_explored": 127,
      "edges_traversed": 45,
      "max_hop_depth": 2,
      "strategies_used": ["ppr", "temporal_filter"]
    },
    "version_info": {
      "superseded_documents": [],
      "current_versions": ["AZA_2023", "BHO_2024"]
    }
  },
  "metadata": {
    "confidence": 0.87,
    "retrieval_strategy": "ppr",
    "reflection_iterations": 1,
    "latency_ms": 1834
  }
}
```

#### Success Metrics
- User trust: measurable via feedback
- Debugging efficiency: 50% faster to identify retrieval issues
- Citation rate: 95% of answers cite specific sources

---

### Phase 6: Evaluation Framework (Week 7) 🎯 CRITICAL

#### Deliverables
1. **Test Dataset Creation**
   - 100 golden Q&A pairs for German funding domain
   - Format: `{"query": "...", "ground_truth_answer": "...", "relevant_chunks": [...]}`
   - Mix of: factual, ambiguous, multi-hop, temporal queries

2. **Automated Metrics**
   - **Retrieval:** Hit@5, Hit@10, MRR, NDCG
   - **Graph:** Avg path length, temporal correctness, coverage
   - **Answer:** ROUGE-L, citation rate, hallucination rate
   - **Performance:** Latency p50/p95, memory peak

3. **Benchmark Suite**
   - Automated daily runs
   - Regression detection
   - A/B comparison (baseline vs. new system)

4. **Ablation Studies**
   - Measure impact of each component:
     - BM25 alone: +X%
     - Reranking alone: +Y%
     - PPR alone: +Z%
     - Combined: +W%

#### Files
**New:**
- `src/evaluation/graph_rag_metrics.py` - All metrics implementation
- `data/test_dataset.json` - Golden Q&A pairs
- `scripts/benchmark.py` - Automated benchmark runner
- `scripts/ablation_study.py` - Component-wise evaluation

#### Code Structure
```python
class GraphRAGEvaluator:
    def evaluate_retrieval(self, engine: HybridSearchEngine) -> Dict[str, float]:
        """Hit@k, MRR, NDCG"""

    def evaluate_temporal_correctness(self, engine: HybridSearchEngine) -> float:
        """% of results using newest version"""

    def evaluate_answer_quality(self, llm: RuleExtractor) -> Dict[str, float]:
        """ROUGE, citation rate, hallucination rate"""
```

#### Success Metrics
- Test dataset quality: validated by domain expert
- Benchmark runtime: <10 minutes for full suite
- Regression detection: 100% (no degradation goes unnoticed)

---

## Complete Retrieval Pipeline

```
┌─────────────────────────────────────────────────────────────────────┐
│                        USER QUERY                                   │
│                     "Was ist der Schwellenwert                      │
│                   für Vergaben bei BMBF-Projekten?"                 │
└─────────────────────────────────────────────────────────────────────┘
                                │
                    ┌───────────▼───────────┐
                    │  Query Enhancement    │
                    │                       │
                    │  • Detect complexity  │
                    │  • Multi-Query (3x)   │
                    │  • HyDE (legal terms) │
                    │  • Decomposition      │
                    └───────────┬───────────┘
                                │
                    ┌───────────▼───────────┐
                    │  Multi-Retrieval      │
                    │                       │
                    │  BM25 (SpaCy)  Top 20 │
                    │  Vector (BGE)  Top 20 │
                    │  [HyDE Vector] Top 20 │
                    └───────────┬───────────┘
                                │
                    ┌───────────▼───────────┐
                    │  RRF Fusion           │
                    │  k=60                 │
                    │  → Top 20 candidates  │
                    └───────────┬───────────┘
                                │
                    ┌───────────▼───────────┐
                    │  Cross-Encoder        │
                    │  Reranking            │
                    │  (mmarco-mMiniLM)     │
                    │  → Top 10             │
                    └───────────┬───────────┘
                                │
                    ┌───────────▼───────────┐
                    │  Graph Expansion      │
                    │                       │
                    │  PPR Subgraph (k=50)  │
                    │  OR k-Hop (k=2)       │
                    │  + Temporal Filter    │
                    │  → ~50 nodes          │
                    └───────────┬───────────┘
                                │
                    ┌───────────▼───────────┐
                    │  Context Assembly     │
                    │  • Graph paths        │
                    │  • Version warnings   │
                    │  • Centrality scores  │
                    └───────────┬───────────┘
                                │
                    ┌───────────▼───────────┐
                    │  Answer Generation    │
                    │  (LLM with context)   │
                    └───────────┬───────────┘
                                │
                    ┌───────────▼───────────┐
                    │  Self-Reflection?     │
                    │  Confidence < 0.7?    │
                    └───┬──────────────┬────┘
                        │ Yes          │ No
                        │              │
                   ┌────▼────┐         │
                   │ Expand  │         │
                   │ Context │         │
                   │ (Iter 2)│         │
                   └────┬────┘         │
                        │              │
                    ┌───▼──────────────▼────┐
                    │  Provenance Tracking  │
                    │  • Attribution scores │
                    │  • Graph paths        │
                    │  • Exploration stats  │
                    └───────────┬───────────┘
                                │
                    ┌───────────▼───────────┐
                    │  FINAL RESPONSE       │
                    │  • Answer + Confidence│
                    │  • Sources + Scores   │
                    │  • Graph visualization│
                    │  • Version warnings   │
                    └───────────────────────┘
```

---

## Memory Budget (4GB VPS)

| Component | Current | After Phase 1 | After Phase 2 | After Phase 6 |
|-----------|---------|---------------|---------------|---------------|
| ChromaDB | 300 MB | 300 MB | 300 MB | 300 MB |
| NetworkX Graph | 100 MB | 100 MB | 100 MB | 100 MB |
| Python Runtime | 50 MB | 50 MB | 50 MB | 50 MB |
| FastAPI | 30 MB | 30 MB | 30 MB | 30 MB |
| **BM25 Index** | - | **+50 MB** | +50 MB | +50 MB |
| **SpaCy Model** | - | **+100 MB** | +100 MB | +100 MB |
| **Cross-Encoder** | - | **+120 MB** (lazy) | +120 MB | +120 MB |
| **PageRank Cache** | - | - | **+5 MB** | +5 MB |
| **Community Detection** | - | - | **+10 MB** | +10 MB |
| **TOTAL** | **480 MB** | **650 MB** | **665 MB** | **665 MB** |
| **Free** | 3.52 GB | 3.35 GB | 3.34 GB | 3.34 GB |

**Optimization Strategies:**
- Lazy loading: Cross-encoder only loaded when needed
- LRU cache: PageRank evicted after 1 hour
- Streaming: BM25 results not materialized all at once
- Sparse matrices: Use `scipy.sparse` for large matrices

**Safety Margin:** 3.3 GB free = **comfortable** ✅

---

## Library Requirements

### New Dependencies
```txt
# Sparse Retrieval
rank-bm25>=0.2.2

# Reranking
sentence-transformers>=2.2.0

# German NLP
spacy>=3.5.0

# Graph Algorithms
python-louvain>=0.16

# Scientific Computing
scipy>=1.10.0
numpy>=1.24.0

# Evaluation
scikit-learn>=1.3.0
rouge-score>=0.1.2
```

### Post-Install Commands
```bash
# Download German language model
python -m spacy download de_core_news_sm

# Pre-download cross-encoder (optional - can lazy load)
python -c "from sentence_transformers import CrossEncoder; CrossEncoder('cross-encoder/mmarco-mMiniLMv2-L12-H384-v1')"
```

**Total Additional Disk Space:** ~400 MB
**Total Additional Memory (peak):** ~270 MB

---

## API Changes

### New Endpoint: `/api/search/advanced`

**Request:**
```json
{
  "query": "Was ist der Schwellenwert für Vergaben?",
  "strategy": "ppr",  // "ppr", "k-hop", "auto"
  "enable_reflection": true,
  "enable_query_expansion": true,
  "limit": 5
}
```

**Response:** (See Phase 5 API Response Format)

### Backward Compatibility
- **Keep:** Existing `/api/search` endpoint unchanged
- **Add:** New `/api/search/advanced` for power users
- **Default:** `/api/search` uses basic pipeline (BM25 + RRF + Reranking, no reflection)

---

## Testing Strategy

### Unit Tests (100+ tests)
```python
# tests/test_bm25_index.py
def test_bm25_retrieval()
def test_bm25_german_tokenization()
def test_bm25_index_persistence()

# tests/test_reranker.py
def test_cross_encoder_reranking()
def test_lazy_loading()

# tests/test_graph_algorithms.py
def test_personalized_pagerank()
def test_ppr_subgraph_extraction()
def test_k_hop_expansion()
def test_temporal_filtering()

# tests/test_query_enhancer.py
def test_multi_query_generation()
def test_hyde_generation()
def test_query_decomposition()

# tests/test_reflective_rag.py
def test_self_reflection()
def test_crag_correction()
def test_confidence_scoring()

# tests/test_provenance.py
def test_attribution_scoring()
def test_graph_path_visualization()
```

### Integration Tests (20+ scenarios)
```python
# tests/integration/test_end_to_end.py
def test_simple_query_pipeline()
def test_complex_query_with_reflection()
def test_multi_hop_with_ppr()
def test_temporal_query_newest_version()
def test_api_advanced_endpoint()
```

### Benchmark Suite
```python
# scripts/benchmark.py
def benchmark_retrieval_speed()      # Avg latency for 100 queries
def benchmark_memory_usage()         # Peak memory profiling
def benchmark_accuracy()             # Hit@k, MRR vs. golden dataset
def benchmark_component_impact()     # Ablation study
```

---

## Success Criteria

### Quantitative Metrics
| Metric | Baseline | Target | Stretch Goal |
|--------|----------|--------|--------------|
| Hit@5 | 60% | 80% | 85% |
| Hit@10 | 75% | 90% | 95% |
| MRR | 0.55 | 0.70 | 0.75 |
| ROUGE-L F1 | - | 0.60 | 0.70 |
| Temporal Correctness | ~90% | 100% | 100% |
| Citation Rate | ~70% | 90% | 95% |
| Latency p95 (simple) | 800ms | <2s | <1.5s |
| Latency p95 (complex) | - | <5s | <4s |
| Memory Peak | 480 MB | <700 MB | <650 MB |

### Qualitative Criteria
- ✅ Users report higher answer quality in feedback
- ✅ Graph paths are intuitive and helpful for debugging
- ✅ Version warnings prevent outdated information
- ✅ Confidence scores are well-calibrated (high confidence → correct answer)
- ✅ System handles ambiguous queries gracefully with reflection
- ✅ German legal terminology is correctly handled (BM25 + SpaCy)

---

## Implementation Timeline

| Phase | Week | Focus | Key Deliverables |
|-------|------|-------|------------------|
| **Phase 1** | Week 1 | Hybrid Retrieval | BM25 + RRF + Reranking |
| **Phase 2** | Week 2 | Graph Intelligence | PPR + k-hop + Temporal Filter |
| **Phase 3** | Week 3 | Query Enhancement | Multi-Query + HyDE + Decomposition |
| **Phase 4** | Week 4-5 | Reflective RAG | Self-Reflection + CRAG |
| **Phase 5** | Week 6 | Explainability | Provenance + Graph Paths |
| **Phase 6** | Week 7 | Evaluation | Test Dataset + Benchmarks |
| **Polish** | Week 8 | Optimization | Performance tuning + Documentation |

**Total:** 8 weeks to production-ready State-of-the-Art Graph RAG

---

## Risk Mitigation

### Risk 1: Memory Overflow on 4GB VPS
**Mitigation:**
- Lazy loading for cross-encoder (only load when needed)
- LRU cache with 1-hour TTL for PageRank
- Monitor memory with `psutil` in production
- Fallback: Disable cross-encoder if memory critical

**Probability:** Low
**Impact:** Medium
**Status:** Mitigated ✅

### Risk 2: Latency Too High for User Experience
**Mitigation:**
- Conditional features: reflection only for low confidence (<0.7)
- Query complexity detection: skip multi-query for simple questions
- Async processing: offload heavy tasks to background
- Caching: cache frequent queries (Redis optional)

**Probability:** Medium
**Impact:** Medium
**Status:** Mitigated ✅

### Risk 3: LLM API Costs (Multi-Query + Reflection)
**Mitigation:**
- Budget tracking: log all LLM calls with cost estimation
- Smart triggers: only use expensive features when necessary
- Model selection: use cheaper models for query enhancement (mistral-small)
- User controls: allow disabling reflection in UI

**Probability:** Medium
**Impact:** Low
**Status:** Mitigated ✅

### Risk 4: Evaluation Dataset Quality
**Mitigation:**
- Domain expert review (manual validation)
- Iterative refinement (update dataset with edge cases)
- Diversity: mix factual, ambiguous, multi-hop queries
- Version control: track changes to test dataset

**Probability:** Low
**Impact:** High
**Status:** Mitigated ✅

---

## Post-Implementation Roadmap

### Short-Term (Months 1-3)
- [ ] **Monitor production metrics** (latency, accuracy, user feedback)
- [ ] **Iterate on test dataset** (add edge cases from production)
- [ ] **Fine-tune hyperparameters** (k, alpha, thresholds)
- [ ] **Add caching layer** (Redis for frequent queries)

### Mid-Term (Months 4-6)
- [ ] **Fine-tune cross-encoder** on German legal text (custom dataset)
- [ ] **Experiment with GraphRAG papers** (2025/2026 research)
- [ ] **Add entity extraction** for better citation linking
- [ ] **Multi-turn conversations** (context carry-over)

### Long-Term (Months 7-12)
- [ ] **Migrate to vector DB** with native graph support (e.g., Weaviate)
- [ ] **Real-time graph updates** (webhook-based document ingestion)
- [ ] **Multi-modal RAG** (images, tables from PDFs)
- [ ] **Federated search** (cross-domain knowledge graphs)

---

## Critical Files for Implementation

### Top 5 Critical Files
1. **`src/parser/hybrid_search.py`** (CORE) - Main retrieval orchestrator
2. **`src/graph/graph_algorithms.py`** (NEW) - Graph intelligence brain
3. **`src/parser/bm25_index.py`** (NEW) - Sparse retrieval component
4. **`src/api/search_api.py`** (API) - Expose new features
5. **`src/parser/reranker.py`** (NEW) - Cross-encoder reranking

### Supporting Files (10+)
6. `src/parser/query_enhancer.py` (NEW) - Multi-query, HyDE
7. `src/parser/reflective_rag.py` (NEW) - Self-reflection, CRAG
8. `src/parser/provenance_tracker.py` (NEW) - Attribution, paths
9. `src/evaluation/graph_rag_metrics.py` (NEW) - Metrics
10. `requirements.txt` (MODIFIED) - Dependencies
11. `data/test_dataset.json` (NEW) - Golden Q&A pairs
12. `scripts/benchmark.py` (NEW) - Automated benchmarks
13. `tests/test_*.py` (NEW) - 100+ unit/integration tests

**Total:** ~13 new files, ~5 modified files

---

## Appendix: Literature & References

### Key Papers
1. **HyDE** - "Precise Zero-Shot Dense Retrieval without Relevance Labels" (2022)
2. **Self-RAG** - "Learning to Retrieve, Generate, and Critique" (2023)
3. **CRAG** - "Corrective Retrieval Augmented Generation" (2024)
4. **GraphRAG (Microsoft)** - "From Local to Global Graph RAG" (2024)
5. **Personalized PageRank** - "Topic-Sensitive PageRank" (2002)

### Tools & Libraries
- **rank-bm25:** https://github.com/dorianbrown/rank_bm25
- **sentence-transformers:** https://www.sbert.net/
- **SpaCy:** https://spacy.io/models/de
- **NetworkX:** https://networkx.org/
- **python-louvain:** https://github.com/taynaud/python-louvain

---

## Conclusion

This plan transforms Bund-ZuwendungsGraph into a **State-of-the-Art Graph RAG** system with:
- ✅ **30% accuracy improvement** (Hit@10: 75% → 90%)
- ✅ **Full explainability** (provenance, graph paths, attribution)
- ✅ **Memory efficient** (<700 MB peak on 4GB VPS)
- ✅ **Production-ready** (comprehensive testing, benchmarks, monitoring)

**Next Step:** Begin Phase 1 implementation (BM25 + RRF + Reranking).
