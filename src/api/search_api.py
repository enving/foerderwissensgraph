from flask import Flask, request, jsonify
from flask_cors import CORS
from pathlib import Path
from src.parser.hybrid_search import HybridSearchEngine
import logging

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Hybrid Search Engine
engine = HybridSearchEngine(
    graph_path=Path("data/knowledge_graph.json"), db_path="data/chroma_db"
)


@app.route("/api/search", methods=["GET"])
def search():
    query = request.args.get("q", "")
    if not query:
        return jsonify([])

    limit = int(request.args.get("limit", 5))
    results = engine.search(query, limit=limit)
    return jsonify(results)


if __name__ == "__main__":
    app.run(port=5001, debug=True)
