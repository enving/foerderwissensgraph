from flask import Flask, request, jsonify
from flask_cors import CORS
from pathlib import Path
from src.parser.hybrid_search import HybridSearchEngine
from src.parser.rule_extractor import RuleExtractor
import logging

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Hybrid Search Engine
engine = HybridSearchEngine(
    graph_path=Path("data/knowledge_graph.json"), db_path="data/chroma_db"
)
# Initialize Answer Engine
answer_engine = RuleExtractor()


@app.route("/api/search", methods=["GET"])
def search():
    query = request.args.get("q", "")
    if not query:
        return jsonify([])

    limit = int(request.args.get("limit", 5))

    # Filter parameters
    filters = {
        "ministerium": request.args.get("ministerium"),
        "kuerzel": request.args.get("kuerzel"),
        "stand_after": request.args.get("stand_after"),
    }

    results = engine.search(query, limit=limit)

    # Apply filters to results
    filtered_results = []
    for res in results:
        match = True
        if (
            filters["ministerium"]
            and res.get("ministerium") != filters["ministerium"]
            and res.get("herausgeber") != filters["ministerium"]
        ):
            match = False
        if filters["kuerzel"] and filters["kuerzel"] not in res.get("kuerzel", ""):
            match = False
        if filters["stand_after"] and res.get("stand"):
            res_stand = res.get("stand")
            if res_stand and res_stand < filters["stand_after"]:
                match = False

        if match:
            filtered_results.append(res)

    if filtered_results and len(query.split()) > 2:
        # Prepare context for RAG
        top_results = filtered_results[:3]
        context_chunks = [
            f"Titel: {r.get('doc_title', 'Unbekannt')}\nText: {r.get('text', '')}"
            for r in top_results
        ]

        # Generate Answer
        try:
            answer = answer_engine.generate_answer(query, context_chunks)
        except Exception as e:
            logger.error(f"Answer generation failed: {e}")
            answer = None

        if answer:
            return jsonify({"answer": answer, "results": filtered_results})

    return jsonify(filtered_results)


if __name__ == "__main__":
    app.run(port=5001, debug=True)
