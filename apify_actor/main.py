import os
import sys
import asyncio
from pathlib import Path

# Add the parent directory to sys.path so we can import 'src'
sys.path.append(str(Path(__file__).parent.parent))

from apify import Actor
from src.parser.hybrid_search import HybridSearchEngine
from src.graph.compliance_mapper import ComplianceMapper
from src.models.schemas import ExpandContextRequest
from src.parser.rule_extractor import RuleExtractor
from src.config_loader import settings


async def main():
    async with Actor:
        # Get input
        actor_input = await Actor.get_input() or {}
        mode = actor_input.get("mode", "search")

        # Initialize engines
        search_engine = HybridSearchEngine(
            db_path=settings.get("paths.chroma_db", "data/chroma_db"),
        )
        compliance_mapper = ComplianceMapper(
            graph_path=Path(
                settings.get("paths.knowledge_graph", "data/knowledge_graph.json")
            ),
            vector_store=search_engine.vector_store,
        )
        answer_engine = RuleExtractor()

        if mode == "search":
            query = actor_input.get("query")
            if not query:
                await Actor.fail(message="Missing 'query' for search mode.")
                return

            generate_answer = actor_input.get("generate_answer", True)

            # Using advanced search logic (search_v2)
            results = search_engine.search_v2(
                query=query,
                limit=actor_input.get("limit", 5),
            )

            output = {"results": results}

            if generate_answer and results:
                context_chunks = [
                    f"Titel: {r.get('doc_title')}\nText: {r.get('text')}"
                    for r in results[:3]
                ]
                try:
                    answer = answer_engine.generate_answer(query, context_chunks)
                    output["answer"] = answer
                except Exception as e:
                    Actor.log.error(f"Answer generation failed: {e}")

            await Actor.push_data(output)

        elif mode == "expand":
            context_label = actor_input.get("context_label", "Apify_Context")
            text_chunks = actor_input.get("text_chunks", [])

            if not text_chunks:
                await Actor.fail(message="Missing 'text_chunks' for expand mode.")
                return

            request = ExpandContextRequest(
                context_label=context_label,
                text_chunks=text_chunks,
                metadata=actor_input.get("metadata", {}),
            )

            response = compliance_mapper.expand_context(request)
            await Actor.push_data(response.dict())

        else:
            await Actor.fail(message=f"Invalid mode: {mode}")


if __name__ == "__main__":
    asyncio.run(main())
