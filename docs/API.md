# Bund-ZuwendungsGraph API Documentation

## Overview

The Bund-ZuwendungsGraph API provides access to the knowledge graph of German funding regulations. It supports hybrid search (vector + graph), sparse retrieval (BM25), semantic reranking, and LLM-based answer generation.

**Base URL:** `https://foerderwissensgraph.digitalalchemisten.de/api`

---

## Endpoints

### 0. API Index
`GET /api/`

Returns a JSON index of available endpoints and documentation links.

### 1. Advanced Search
`GET /api/search/advanced`

PHASE 1 GRAPH RAG: Advanced Hybrid Search with BM25 + RRF + Reranking.

#### Pipeline Steps:
1. **Multi-Retrieval**: BM25 (sparse) + Vector (dense).
2. **RRF Fusion**: Reciprocal Rank Fusion of retrieval results.
3. **Cross-Encoder Reranking**: Semantic reranking using a model optimized for German legal text.
4. **Graph Expansion**: Multi-hop context retrieval (following `REFERENCES`, `SUPERSEDES` edges).
5. **Answer Generation**: LLM-based answer generation with provenance tracking.

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `q` | string | **Required** | The search query in natural language. |
| `limit` | integer | `5` | Maximum number of results to return. |
| `ministerium` | string | - | Filter results by ministry name. |
| `kuerzel` | string | - | Filter results by program abbreviation. |
| `stand_after` | string | - | Filter results by date (ISO format, YYYY-MM-DD). |
| `use_bm25` | boolean | `true` | Enable sparse retrieval using BM25. |
| `use_reranking`| boolean | `true` | Enable semantic reranking using a Cross-Encoder. |
| `multi_hop` | boolean | `true` | Enable graph traversal for additional context. |
| `generate_answer`| boolean | `true` | Generate an LLM-based answer using retrieved context. |

#### Response Format

```json
{
  "answer": "Generated answer string...",
  "results": [
    {
      "id": "chunk_id",
      "text": "Chunk text content...",
      "score": 0.85,
      "doc_title": "Document Title",
      "neighbor_context": [
        {
          "id": "neighbor_id",
          "text": "Neighbor text...",
          "type": "REFERENCES"
        }
      ]
    }
  ],
  "metadata": {
    "retrieval_strategy": "bm25+vector+reranking",
    "num_results": 1,
    "features_enabled": {
      "bm25": true,
      "reranking": true,
      "multi_hop": true,
      "answer_generation": true
    },
    "api_version": "2.0.0",
    "phase": "1"
  }
}
```

---

### 2. Basic Search (Legacy)
`GET /api/search`

Legacy endpoint for backward compatibility. Uses a simpler search pipeline.

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `q` | string | **Required** | The search query. |
| `limit` | integer | `5` | Maximum number of results. |
| `ministerium` | string | - | Filter by ministry. |
| `kuerzel` | string | - | Filter by kuerzel. |
| `stand_after` | string | - | Filter by date. |

---

### 4. API Documentation
*   **Swagger UI:** `GET /api/docs`
*   **ReDoc:** `GET /api/redoc`
*   **OpenAPI Spec:** `GET /api/openapi.json`
