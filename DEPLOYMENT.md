# Deployment Guide: Bund-ZuwendungsGraph

This document describes how to host the complete system, including the crawler, knowledge graph, API, and interactive dashboard.

## System Components

1.  **Crawler (Discovery):** Playwright-based script to fetch PDFs from the Federal Form Cabinet.
2.  **Extraction Pipeline (Parser):** Docling and LLM-based tools to process PDFs into a Knowledge Graph.
3.  **Vector Store:** ChromaDB instance storing semantic embeddings of document chunks.
4.  **Knowledge Graph:** NetworkX graph (exported as JSON) representing relationships between programs and rules.
5.  **Search API:** Flask-based REST API that provides Graph-RAG capabilities.
6.  **Dashboard:** D3.js interactive frontend for visualization.

## Prerequisites

- Linux Server (Ubuntu 22.04+ recommended)
- Python 3.10+
- Node.js (for frontend serving, optional)
- IONOS or Mistral API Key (for embeddings and extraction)

## Installation

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/your-repo/Bund-ZuwendungsGraph.git
    cd Bund-ZuwendungsGraph
    ```

2.  **Setup Virtual Environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    playwright install chromium
    ```

3.  **Environment Variables:**
    Create a `.env` file in the root directory:
    ```env
    IONOS_API_KEY=your_key
    IONOS_EMBEDDING_API_URL=https://openai.inference.de-txl.ionos.com/v1/embeddings
    IONOS_EMBEDDING_MODEL=BAAI/bge-m3
    MISTRAL_API_KEY=your_fallback_key
    ```

## Data Initialization (Optional if pre-built)

If you need to rebuild the data:
1.  **Crawl:** `python src/discovery/easy_crawler.py`
2.  **Process:** `python src/main_pipeline.py`
3.  **Vectorize:** `python src/parser/vector_store.py`

## Running the API

The API provides the search backend for the dashboard.

```bash
export PYTHONPATH=$PYTHONPATH:$(pwd)
venv/bin/python src/api/search_api.py
```

For production, use a WSGI server:
```bash
pip install gunicorn
gunicorn --bind 0.0.0.0:5001 src.api.search_api:app
```

## Hosting the Dashboard

The dashboard is a static HTML file located at `docs/dashboard.html`.

### Option A: Simple Python Server
```bash
python -m http.server 8080 --directory .
```
Access via `http://your-server-ip:8080/docs/dashboard.html`.

### Option B: Nginx (Recommended)
Add a server block to your Nginx configuration:
```nginx
server {
    listen 80;
    server_name zuwendungsgraph.local;

    location / {
        root /path/to/Bund-ZuwendungsGraph;
        index docs/dashboard.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:5001/;
    }
}
```

## Security Recommendations

- Use a Reverse Proxy (Nginx) with SSL (Let's Encrypt).
- Restrict API access to known IP addresses if possible.
- Ensure your `.env` file is never publicly accessible.
