# Resource & Performance Profiling Report

**Date:** 2026-01-18
**Version:** 2.2.2
**Task:** TASK-009
**Environment:** 4GB RAM VPS (Target), Simulated via Python 3.14 Environment

## 1. Memory Footprint (RAM)

| Component | Usage (Approx) | Notes |
|-----------|----------------|-------|
| **Base Process** | ~80 MB | Python Interpreter + FastAPI Overhead |
| **NetworkX Graph** | ~90 MB | 11,490 Nodes, 107,212 Edges |
| **BM25 Index** | ~20 MB | Sparse Index (11k Chunks) |
| **Reranker (BERT)** | ~500 MB | *Simulated* (mmarco-mMiniLM-L12) |
| **VectorStore** | ~50 MB | REST Client (Data in external Container) |
| **Search Overhead** | ~20-50 MB | Temporary during query execution |
| **Total Peak** | **~750 - 800 MB** | **Safe for 4GB VPS** |

### Scaling Projections
- **2 Workers:** ~1.6 GB RAM
- **4 Workers:** ~3.2 GB RAM (Risk of OOM on 4GB Node with OS overhead)
- **Recommendation:** Start with **2 Gunicorn Workers** on a 4GB Node.

## 2. Latency Analysis

| Operation | Time (Approx) | Status |
|-----------|---------------|--------|
| **Graph Loading** | 0.7s | ✅ Fast |
| **BM25 Search** | 0.2s | ✅ Fast |
| **Vector Search** | <0.1s | ✅ Fast (via ChromaDB) |
| **Reranking** | 0.5s - 1.0s | (Est. for CPU) |
| **Query Enhancement** | **~9.0s** | ❌ **CRITICAL BOTTLENECK** |

### Bottleneck: HyDE (Hypothetical Document Embeddings)
The LLM API call for HyDE generation took 9 seconds and ultimately failed with a validation error (`Input should be a valid string`).

**Action Items:**
1. **Disable HyDE by default** or make it async/optional.
2. **Fix Validation Error:** The LLM provider (IONOS/Mistral) returned `None` or an empty string, causing Pydantic to fail.
3. **Caching:** PageRank computation is fast enough (0.8s) but could be cached.

## 3. Optimization Recommendations

### A. Infrastructure
- **Docker:** Limit container memory for ChromaDB to 1GB.
- **Swap:** Ensure 2GB Swap is active on VPS to handle spikes.

### B. Application
- **Lazy Loading:** Reranker is already lazy-loaded. Good.
- **HyDE:** Switch to a smaller/faster model or use simple synonym expansion instead of full LLM generation for standard queries.
- **Graph:** NetworkX is efficient enough. No need to migrate to Neo4j yet.

## 4. Conclusion
The system is **Cloud Ready** for a 4GB instance. The primary concern is **Latency**, not Memory. Future work should focus on optimizing the Query Enhancement pipeline.
