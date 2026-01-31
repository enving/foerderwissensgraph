from typing import List, Dict, Any, Optional
from pathlib import Path
import uuid
import logging
import json
import os
import networkx as nx
import re
from src.models.schemas import (
    ExpandContextRequest,
    ExpandContextResponse,
    MappedRegulation,
    MappedRule,
)
from src.parser.citation_extractor import CitationExtractor
from src.discovery.law_crawler import LawCrawler
from src.graph.graph_builder import GraphBuilder

logger = logging.getLogger(__name__)


class ComplianceMapper:
    """
    Handles the expansion of context (guidelines) into a structured compliance map
    using the Knowledge Graph.
    """

    def __init__(
        self,
        graph_path: Path,
        vector_store: Optional[Any] = None,
        on_demand_enabled: bool = True,
        config_path: Optional[Path] = None,
    ):
        self.graph_path = graph_path
        self.extractor = CitationExtractor()
        self.graph = nx.MultiDiGraph()
        self.vector_store = vector_store
        self.on_demand_enabled = on_demand_enabled
        self.failed_crawls = set()  # Cache for 404s
        self.newly_crawled_ids = set()  # Track for current session

        # Load external concepts
        self.config_path = config_path or Path("config/compliance_concepts.json")
        self.concept_map = self._load_concepts()

        self._load_graph()
        logger.info(
            f"ComplianceMapper initialized with graph at {graph_path} (On-Demand: {on_demand_enabled})"
        )

    def _load_concepts(self) -> Dict[str, str]:
        """Loads concept mappings from external JSON."""
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("concepts", {})
            except Exception as e:
                logger.error(f"Failed to load concepts from {self.config_path}: {e}")
        return {}

    def _on_demand_import(self, target: str) -> Optional[str]:
        """
        Attempts to crawl and import a law if missing from the graph.
        """
        if not self.on_demand_enabled:
            return None

        # Clean target (e.g. "§ 44 BHO" -> "BHO")
        abbr = target.upper().strip()
        # Heuristic: only try short strings that look like abbreviations
        if not (2 <= len(abbr) <= 10 and abbr.isalpha()):
            # Allow some common symbols like /
            if not re.match(r"^[A-Z0-9/]{2,10}$", abbr):
                return None

        if abbr in self.failed_crawls:
            return None

        logger.info(f"⚡ ON-DEMAND: Triggering crawl for missing law '{abbr}'")

        try:
            crawler = LawCrawler()
            norms = crawler.crawl_law_hybrid(abbr.lower())

            if not norms:
                logger.warning(f"On-demand crawl failed for {abbr}")
                self.failed_crawls.add(abbr)
                return None

            logger.info(f"Crawl successful. Imported {len(norms)} sections for {abbr}")

            # Use GraphBuilder to update persistent graph
            builder = GraphBuilder()
            if self.graph_path.exists():
                builder.load_graph(self.graph_path)

            law_id = f"law_{abbr}"
            builder.add_law(
                law_id,
                {
                    "title": f"Gesetz: {abbr}",
                    "kuerzel": abbr,
                    "category": "Gesetz",
                    "source": "On-demand Crawl",
                },
            )

            for i, norm in enumerate(norms):
                p_clean = (
                    norm["paragraph"]
                    .replace(" ", "_")
                    .replace("§", "S")
                    .replace("(", "")
                    .replace(")", "")
                )
                chunk_id = f"{law_id}_{p_clean}"
                if not norm["paragraph"]:
                    chunk_id = f"{law_id}_chunk_{i}"

                builder.add_chunk(
                    law_id,
                    chunk_id,
                    {
                        "text": norm["content"],
                        "paragraph": norm["paragraph"],
                        "title": f"{abbr} {norm['paragraph']} {norm['title']}",
                        "section_type": "law_section",
                        "type": "chunk",
                    },
                )

            builder.create_reference_edges()
            builder.save_graph(self.graph_path)

            # Update vector store if available
            if self.vector_store:
                logger.info("Updating vector store with new nodes...")
                try:
                    self.vector_store.add_chunks_from_graph(self.graph_path)
                except Exception as ve:
                    logger.error(f"Failed to update vector store: {ve}")

            # Reload local graph
            self._load_graph()
            return law_id

        except Exception as e:
            logger.error(f"Error during on-demand import of {abbr}: {e}")
            self.failed_crawls.add(abbr)
            return None

    def _load_graph(self):
        if self.graph_path.exists():
            try:
                with open(self.graph_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # Try standard loading, handle NetworkX version naming divergence
                    try:
                        self.graph = nx.node_link_graph(data)
                    except Exception:
                        self.graph = nx.node_link_graph(data, edges="edges")
                logger.info(f"Loaded {len(self.graph.nodes)} nodes from graph.")
            except Exception as e:
                logger.error(f"Failed to load graph: {e}")
        else:
            logger.warning(f"Graph file NOT found: {self.graph_path}")

    def _find_document_by_kuerzel(self, kuerzel: str) -> Optional[str]:
        """
        Finds a document node ID by its kuerzel or title using a scoring system.
        Priority: Exact Match > Law/Regulation Type > Partial Match
        """
        kuerzel_clean = kuerzel.lower().strip()
        best_match_id = None
        best_score = 0

        for node_id, data in self.graph.nodes(data=True):
            score = 0

            # Extract candidates
            candidates = []
            candidates.append(str(node_id).lower())
            if data.get("kuerzel"):
                candidates.append(str(data.get("kuerzel")).lower())
            if data.get("title"):
                candidates.append(str(data.get("title")).lower())
            if data.get("doc_title"):
                candidates.append(str(data.get("doc_title")).lower())

            # Scoring Logic
            for cand in candidates:
                if cand == kuerzel_clean:
                    score += 100  # Exact match bonus
                elif (
                    " " not in kuerzel_clean and kuerzel_clean in cand
                ):  # Partial match only for abbreviations
                    # Penalize if candidate is much longer than query (prevents "BHO" matching "Some long doc mentioning BHO")
                    length_diff = len(cand) - len(kuerzel_clean)
                    if length_diff < 5:
                        score += 50
                    elif length_diff < 20:
                        score += 20
                    else:
                        score += 5  # Weak match

            # Extra boost for exact Kürzel match if the node has a 'kuerzel' attribute
            if (
                data.get("kuerzel")
                and str(data.get("kuerzel")).lower() == kuerzel_clean
            ):
                score += 50

            if score > 0:
                # Type Boost
                n_type = data.get("node_type", data.get("type", ""))
                if n_type in ["law", "regulation", "document"]:
                    score += 10
                elif n_type == "chunk":
                    score -= 50  # Disfavor chunks if a document exists

            if score > best_score:
                best_score = score
                best_match_id = node_id

        if best_match_id:
            # If best match is a chunk, resolve to parent
            n_type = self.graph.nodes[best_match_id].get("node_type", "")
            if n_type == "chunk" or "_chunk_" in str(best_match_id):
                # Using general edges view to satisfy LSP and handle both DiGraph/MultiDiGraph
                for u, v, attr in self.graph.edges(best_match_id, data=True):
                    if v == best_match_id and attr.get("relation") == "HAS_CHUNK":
                        return u
                if isinstance(best_match_id, str) and "_" in best_match_id:
                    return best_match_id.split("_")[0]

            return best_match_id

        return None

    def _find_latest_version(self, doc_id: str) -> str:
        """Follows SUPERSEDES edges in reverse to find the latest version in the family."""
        current = doc_id
        visited = {current}
        while True:
            # Look for a node that supersedes the current one
            # Edge: X (newer) --SUPERSEDES--> current (older)
            found_newer = False
            if self.graph.has_node(current):
                for u, v, attr in self.graph.edges(current, data=True):
                    if (
                        v == current
                        and attr.get("relation") == "SUPERSEDES"
                        and u not in visited
                    ):
                        current = u
                        visited.add(current)
                        found_newer = True
                        break
            if not found_newer:
                break
        return current

    def _get_family_set(self, doc_id: str) -> set:
        """Finds all document IDs belonging to the same version family."""
        family = {doc_id}
        # Follow SUPERSEDES in both directions to find the whole chain
        queue = [doc_id]
        while queue:
            curr = queue.pop(0)
            if not self.graph.has_node(curr):
                continue
            for u, v, attr in self.graph.edges(curr, data=True):
                # Newer versions (incoming)
                if (
                    v == curr
                    and attr.get("relation") == "SUPERSEDES"
                    and u not in family
                ):
                    family.add(u)
                    queue.append(u)
                # Older versions (outgoing)
                if (
                    u == curr
                    and attr.get("relation") == "SUPERSEDES"
                    and v not in family
                ):
                    family.add(v)
                    queue.append(v)
        return family

    def _get_rules_for_document(self, doc_id: str) -> List[MappedRule]:
        """Finds all rule chunks attached to a document."""
        rules = []
        chunk_nodes = []

        if self.graph.has_node(doc_id):
            for target in self.graph.successors(doc_id):
                edge_data = self.graph.get_edge_data(doc_id, target)
                for key in edge_data:
                    if edge_data[key].get("relation") == "HAS_CHUNK":
                        chunk_nodes.append((target, self.graph.nodes[target]))

        if not chunk_nodes:
            for node_id, data in self.graph.nodes(data=True):
                if str(node_id).startswith(f"{doc_id}_chunk_"):
                    chunk_nodes.append((node_id, data))

        for chunk_id, chunk_node in chunk_nodes:
            if "rules" in chunk_node and chunk_node["rules"]:
                for r in chunk_node["rules"]:
                    rules.append(
                        MappedRule(
                            rule_id=f"rule_{chunk_id}_{len(rules)}",
                            content=r.get("rule", chunk_node.get("text", "")[:200]),
                            relevance_reason=f"Gefunden in Dokument '{doc_id}'",
                        )
                    )
            elif len(chunk_node.get("text", "")) > 100:
                text = chunk_node.get("text", "")
                if any(
                    kw in text.lower()
                    for kw in ["euro", "§", "frist", "nachweis", "pflicht"]
                ):
                    rules.append(
                        MappedRule(
                            rule_id=f"chunk_{chunk_id}",
                            content=text[:300] + ("..." if len(text) > 300 else ""),
                            relevance_reason=f"Referenzierte Textpassage aus '{doc_id}'",
                        )
                    )

        return rules[:50]

    def expand_context(self, request: ExpandContextRequest) -> ExpandContextResponse:
        """
        Main entry point for Context-Aware Compliance Mapping.
        Implements server-side deduplication and score aggregation across text chunks.
        """
        logger.info(
            f"Expanding context for: {request.context_label} with {len(request.text_chunks)} chunks"
        )

        context_id = f"ctx_{uuid.uuid4().hex[:8]}"

        # Aggregation Registry
        # Key: source_doc_title -> values
        aggregated_regs = {}
        # Track explicitly finding families to block implicit matches
        explicit_families = set()
        excluded_families = set()

        def register_match(
            doc_id: str, target_name: str, category: str, chunk_idx: int
        ):
            if not self.graph.has_node(doc_id):
                return

            # BLOCKING: If family is explicitly excluded, do not register match
            family = self._get_family_set(doc_id)
            if any(f_id in excluded_families for f_id in family):
                return

            doc_data = self.graph.nodes[doc_id]
            doc_title = doc_data.get("doc_title", doc_data.get("title", target_name))

            # Initialize if new
            if doc_title not in aggregated_regs:
                aggregated_regs[doc_title] = {
                    "doc_id": doc_id,
                    "target_name": target_name,
                    "category": category,
                    "priority": 10 if "Explizit" in category else 1,
                    "hit_count": 0,
                    "found_in_chunks": set(),
                    "rules": {},
                }

            entry = aggregated_regs[doc_title]

            # Update params
            entry["hit_count"] += 1
            entry["found_in_chunks"].add(chunk_idx)

            # Prioritize category (Explicit > Implicit)
            current_priority = 10 if "Explizit" in category else 1
            if current_priority > entry["priority"]:
                entry["category"] = category
                entry["priority"] = current_priority

        # Step A: Hard Citation Matching (Priority 1)
        for i, chunk in enumerate(request.text_chunks):
            citations = self.extractor.extract(chunk)
            for cit in citations:
                target = cit["target"]
                is_excluded = cit.get("is_excluded", False)

                doc_node_id = self._find_document_by_kuerzel(target)

                if not doc_node_id and self.on_demand_enabled:
                    doc_node_id = self._on_demand_import(target)

                if doc_node_id:
                    family = self._get_family_set(doc_node_id)

                    if is_excluded:
                        logger.info(
                            f"Explicitly EXCLUDING family: {target} ({doc_node_id})"
                        )
                        excluded_families.update(family)
                        # Remove from aggregated if already there (unlikely but possible)
                        # However, we'll just let register_match handle it via blocked family check
                        continue

                    # Mark family as explicitly found
                    explicit_families.update(family)

                    # TASK-029: Smart Version Resolution
                    # If the citation was generic (no year), upgrade to latest version.
                    # Heuristic: If target ends with 4 digits, assume specific version requested.
                    has_year = re.search(r"\d{4}$|98$", target.strip())
                    final_doc_id = doc_node_id

                    if not has_year:
                        latest = self._find_latest_version(doc_node_id)
                        if latest != doc_node_id:
                            logger.info(
                                f"Upgrading generic citation '{target}' from {doc_node_id} to latest {latest}"
                            )
                            final_doc_id = latest

                    register_match(
                        doc_id=final_doc_id,
                        target_name=target,
                        category="Explizite Bestimmungen (Zitiert)",
                        chunk_idx=i,
                    )

        # Step B: Implicit Expansion (Fallback)
        for i, chunk in enumerate(request.text_chunks):
            chunk_lower = chunk.lower()
            for keyword, target_doc_name in self.concept_map.items():
                if keyword in chunk_lower or f": {keyword}" in chunk_lower:
                    doc_node_id = self._find_document_by_kuerzel(target_doc_name)
                    if not doc_node_id:
                        continue

                    family = self._get_family_set(doc_node_id)

                    # BLOCKING: If family already explicitly cited, skip implicit
                    if any(f_id in explicit_families for f_id in family):
                        continue

                    # Find LATEST version for implicit expansion
                    latest_id = self._find_latest_version(doc_node_id)

                    register_match(
                        doc_id=latest_id,
                        target_name=target_doc_name,
                        category="Implizite Erweiterung (Expertise)",
                        chunk_idx=i,
                    )

        # Finalize and fetch rules
        mapped_regs = []

        for doc_title, entry in aggregated_regs.items():
            doc_id = entry["doc_id"]

            # Get rules (deduplicated by definition of _get_rules_for_document)
            # We fetch rules once per document
            raw_rules = self._get_rules_for_document(doc_id)

            # Apply Boosting / Annotations
            final_rules = []
            if not raw_rules:
                final_rules.append(
                    MappedRule(
                        rule_id=f"ref_{doc_id}",
                        content=f"Regelwerk {doc_title} ist relevant.",
                        relevance_reason=entry["category"],
                    )
                )
            else:
                # Add context info to relevance reason if found in multiple chunks
                chunk_count = len(entry["found_in_chunks"])
                suffix = ""
                if chunk_count > 1:
                    suffix = f" (Gefunden in {chunk_count} Textsegmenten)"

                for r in raw_rules:
                    # Cloning rule to modify relevance reason without affecting cache if we had one
                    final_rules.append(
                        MappedRule(
                            rule_id=r.rule_id,
                            content=r.content,
                            relevance_reason=r.relevance_reason + suffix,
                        )
                    )

            mapped_regs.append(
                MappedRegulation(
                    category=entry["category"],
                    source_doc=doc_title,
                    doc_id=doc_id,
                    rules=final_rules,
                    is_newly_crawled=doc_id in self.newly_crawled_ids,
                )
            )

        # Fallback if empty
        if not mapped_regs:
            mapped_regs.append(
                MappedRegulation(
                    category="System Information",
                    source_doc="Compliance Mapper",
                    rules=[
                        MappedRule(
                            rule_id="info_no_match",
                            content="No explicit or implicit rules found.",
                            relevance_reason="Analysis result",
                        )
                    ],
                )
            )

        return ExpandContextResponse(
            compliance_context_id=context_id, mapped_regulations=mapped_regs
        )
