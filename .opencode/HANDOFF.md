# Handoff Instructions for Next Agent

**Date:** 2026-01-17
**Last Agent:** opencode
**Project Phase:** Phase 1 Graph RAG Complete ✅
**Version:** 2.0.0

---

## ✅ What Was Completed

### Phase 1: State-of-the-Art Graph RAG
- **BM25 Sparse Retrieval** (`src/parser/bm25_index.py`) - SpaCy German tokenization
- **Cross-Encoder Reranking** (`src/parser/reranker.py`) - mmarco-mMiniLM-L12 model
- **RRF Fusion** - Reciprocal Rank Fusion in `HybridSearchEngine`
- **search_v2() method** - Complete pipeline: BM25 → Vector → RRF → Reranking → Graph
- **New API endpoint** `/api/search/advanced` - Feature flags (use_bm25, use_reranking)
- **LLM Provider Abstraction** (`src/llm/`) - IONOS, OpenAI, Anthropic support

### Documentation Updated
- ✅ `PRD.md` - Version 2.0.0, Phase 1 status, server requirements
- ✅ `.opencode/tasks.json` - TASK-010, TASK-011, FEAT-004 added
- ✅ `requirements.txt` - All Graph RAG dependencies added
- ✅ `.opencode/graph_rag_plan.md` - Complete 6-phase roadmap

### Commit
```
843b8fc - feat: Implement State-of-the-Art Graph RAG Phase 1 + LLM Provider Abstraction
```

---

## 🚀 Next Steps (Priority Order)

### CRITICAL - Before Testing
1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   python -m spacy download de_core_news_sm
   ```

2. **Build BM25 Index:**
   ```bash
   python src/parser/bm25_index.py
   ```
   This creates `data/bm25_index.pkl` (~50MB)

3. **Test Advanced Search:**
   ```bash
   # Start API
   python src/api/search_api.py

   # Test endpoint
   curl "http://localhost:5001/api/search/advanced?q=Vergaberecht&use_bm25=true&use_reranking=true"
   ```

### HIGH PRIORITY - Phase 2
Implement **Graph Algorithms** (`src/graph/graph_algorithms.py`):
- Personalized PageRank for subgraph extraction
- Smart k-hop expansion with temporal filtering
- Replace degree-based scoring with PageRank centrality

**Reference:** See `.opencode/graph_rag_plan.md` Phase 2 section

### MEDIUM PRIORITY
- Write unit tests for Phase 1 components
- Create test dataset (100 golden Q&A pairs)
- Benchmark Phase 1 improvements (Hit@k, MRR)

---

## 📋 Important Notes

### Server Requirements
- **Minimum:** 1GB RAM, 2 vCores (Hetzner CX11 ~3€/mo)
- **Recommended:** 2-4GB RAM (Hetzner CX21 ~5€/mo)
- **Peak Memory:** ~650MB (ChromaDB 300MB + Graph 100MB + BM25 50MB + Reranker 120MB)

### LLM Provider
- Configured via `.env` → `LLM_PROVIDER=ionos`
- Supports: ionos, openai, anthropic
- Test provider config: `python src/llm/provider_factory.py --test`

### API Backward Compatibility
- ✅ `/api/search` - Old endpoint unchanged
- 🆕 `/api/search/advanced` - New endpoint with feature flags
- API version: 1.2.0 → 2.0.0

### Known Issues
- BM25 index needs to be built before first use
- Cross-encoder lazy loads (~120MB on first query)
- SpaCy model must be downloaded manually

---

## 📁 Key Files Modified

```
NEW FILES:
  src/parser/bm25_index.py          # BM25 sparse retrieval
  src/parser/reranker.py            # Cross-encoder reranking
  src/llm/*.py                      # LLM provider abstraction
  .opencode/graph_rag_plan.md       # 6-phase roadmap

MODIFIED FILES:
  src/parser/hybrid_search.py       # Added search_v2()
  src/api/search_api.py             # New /api/search/advanced
  src/parser/rule_extractor.py      # Uses LLM abstraction
  requirements.txt                  # Graph RAG dependencies
  PRD.md                            # v2.0.0 status
  .opencode/tasks.json              # TASK-010, FEAT-004
```

---

## 🎯 Task Status

**Completed:**
- [x] TASK-010: Phase 1 Graph RAG (BM25 + RRF + Reranking)
- [x] FEAT-004: State-of-the-Art Graph RAG Phase 1

**Next (Pending):**
- [ ] TASK-011: Phase 2 Graph RAG (Personalized PageRank)
- [ ] TASK-007: Full Crawler Implementation
- [ ] TASK-008: Automated Embedding Sync
- [ ] TASK-009: Resource & Performance Profiling

---

## ❓ Questions for User (If Unclear)

1. Should we proceed with **Phase 2** (Graph Algorithms) or focus on **testing/benchmarking Phase 1** first?
2. Is the server spec (2-4GB RAM) acceptable for deployment?
3. Should we implement unit tests before Phase 2?

---

## 🔗 References

- **Full Plan:** `.opencode/graph_rag_plan.md`
- **Reddit Best Practices:** Legal RAG at scale (custom chunking ✅, hybrid search ✅, graph RAG ✅)
- **Tasks:** `.opencode/tasks.json` - Updated with Phase 1 completion
- **PRD:** `PRD.md` - Version 2.0.0

---

**END OF HANDOFF**
