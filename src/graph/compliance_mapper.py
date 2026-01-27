from typing import List, Dict, Any, Optional
from pathlib import Path
import uuid
import logging
import json
import os
import networkx as nx
import re
from src.models.schemas import ExpandContextRequest, ExpandContextResponse, MappedRegulation, MappedRule
from src.parser.citation_extractor import CitationExtractor

logger = logging.getLogger(__name__)

class ComplianceMapper:
    """
    Handles the expansion of context (guidelines) into a structured compliance map
    using the Knowledge Graph.
    """
    
    # Expert Knowledge Mapping (Step B & C)
    # Maps keywords to "Regulation Families" or "Base Keywords" for search
    CONCEPT_MAP = {
        "reisekosten": "Bundesreisekostengesetz",
        "hotel": "Bundesreisekostengesetz",
        "brkg": "Bundesreisekostengesetz",
        "personalkosten": "TVöD",
        "entgelt": "TVöD",
        "tvöd": "TVöD",
        "besserstellung": "Besserstellungsverbot",
        "vergabe": "UVgO",
        "vob": "VOB",
        "uvgo": "UVgO",
        "haushalt": "BHO",
        "bho": "BHO",
        "verwaltungsverfahren": "VwVfG",
        "vwvfg": "VwVfG",
        "anteilsfinanzierung": "VV Nr. 2.4", 
        "eigenmittel": "VV Nr. 2.4",
        "zinssatz": "Verzugszinsen",
    }

    def __init__(self, graph_path: Path):
        self.graph_path = graph_path
        self.extractor = CitationExtractor()
        self.graph = nx.MultiDiGraph()
        self._load_graph()
        logger.info(f"ComplianceMapper initialized with graph at {graph_path}")

    def _load_graph(self):
        if self.graph_path.exists():
            try:
                with open(self.graph_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.graph = nx.node_link_graph(data)
                logger.info(f"Loaded {len(self.graph.nodes)} nodes from graph.")
            except Exception as e:
                logger.error(f"Failed to load graph: {e}")
        else:
            logger.warning(f"Graph file NOT found: {self.graph_path}")

    def _find_document_by_kuerzel(self, kuerzel: str) -> Optional[str]:
        """Finds a document node ID by its kuerzel or by searching title."""
        kuerzel_clean = kuerzel.lower().strip()
        
        for node_id, data in self.graph.nodes(data=True):
            node_kuerzel = data.get("kuerzel")
            title = data.get("doc_title") or data.get("title") or ""
            
            match = False
            if node_kuerzel and kuerzel_clean in str(node_kuerzel).lower():
                match = True
            elif title and kuerzel_clean in str(title).lower():
                match = True
                
            if match:
                n_type = data.get("node_type", data.get("type", ""))
                if n_type == "chunk":
                    for source, target, key, attr in self.graph.in_edges(node_id, data=True, keys=True):
                        if attr.get("relation") == "HAS_CHUNK":
                            return source
                    if isinstance(node_id, str) and "_" in node_id:
                        return node_id.split("_")[0]
                elif n_type in ["document", "external", "law"]:
                    return node_id
                return node_id # General fallback
        return None

    def _find_latest_version(self, doc_id: str) -> str:
        """Follows SUPERSEDES edges in reverse to find the latest version in the family."""
        current = doc_id
        visited = {current}
        while True:
            # Look for a node that supersedes the current one
            # Edge: X (newer) --SUPERSEDES--> current (older)
            # So we look for incoming SUPERSEDES edges
            found_newer = False
            if self.graph.has_node(current):
                for src, dst, key, attr in self.graph.in_edges(current, keys=True, data=True):
                    if attr.get("relation") == "SUPERSEDES" and src not in visited:
                        current = src
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
            # Newer versions (incoming)
            for src, dst, key, attr in self.graph.in_edges(curr, keys=True, data=True):
                if attr.get("relation") == "SUPERSEDES" and src not in family:
                    family.add(src)
                    queue.append(src)
            # Older versions (outgoing)
            for src, dst, key, attr in self.graph.out_edges(curr, keys=True, data=True):
                if attr.get("relation") == "SUPERSEDES" and dst not in family:
                    family.add(dst)
                    queue.append(dst)
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
                    rules.append(MappedRule(
                        rule_id=f"rule_{chunk_id}_{len(rules)}",
                        content=r.get("rule", chunk_node.get("text", "")[:200]),
                        relevance_reason=f"Gefunden in Dokument '{doc_id}'"
                    ))
            elif len(chunk_node.get("text", "")) > 100:
                text = chunk_node.get("text", "")
                if any(kw in text.lower() for kw in ["euro", "§", "frist", "nachweis", "pflicht"]):
                    rules.append(MappedRule(
                        rule_id=f"chunk_{chunk_id}",
                        content=text[:300] + ("..." if len(text) > 300 else ""),
                        relevance_reason=f"Referenzierte Textpassage aus '{doc_id}'"
                    ))
                    
        return rules[:50]

    def expand_context(self, request: ExpandContextRequest) -> ExpandContextResponse:
        """
        Main entry point for Context-Aware Compliance Mapping.
        """
        logger.info(f"Expanding context for: {request.context_label}")
        
        context_id = f"ctx_{uuid.uuid4().hex[:8]}"
        mapped_regs = []
        seen_docs = set()
        locked_families = set() # Families where a specific version was cited

        # Step A: Hard Citation Matching (Priority 1)
        for chunk in request.text_chunks:
            citations = self.extractor.extract(chunk)
            for cit in citations:
                target = cit["target"]
                doc_node_id = self._find_document_by_kuerzel(target)
                
                if doc_node_id and doc_node_id not in seen_docs:
                    seen_docs.add(doc_node_id)
                    locked_families.update(self._get_family_set(doc_node_id))
                    
                    doc_data = self.graph.nodes[doc_node_id]
                    doc_rules = self._get_rules_for_document(doc_node_id)
                    
                    if not doc_rules:
                        doc_rules = [MappedRule(
                            rule_id=f"cite_{doc_node_id}",
                            content=f"Regelwerk {doc_data.get('title', target)} wurde explizit im Text referenziert.",
                            relevance_reason="Explizite Zitation"
                        )]

                    mapped_regs.append(MappedRegulation(
                        category="Explizite Bestimmungen (Zitiert)",
                        source_doc=doc_data.get("doc_title", doc_data.get("title", target)),
                        rules=doc_rules
                    ))

        # Step B & C: Concept & Implicit Expansion (Fallback to Latest)
        for chunk in request.text_chunks:
            chunk_lower = chunk.lower()
            for keyword, target_doc_name in self.CONCEPT_MAP.items():
                if keyword in chunk_lower or f": {keyword}" in chunk_lower: # Support "Art: Anteilsfinanzierung"
                    doc_node_id = self._find_document_by_kuerzel(target_doc_name)
                    if not doc_node_id:
                        continue
                        
                    family = self._get_family_set(doc_node_id)
                    
                    # BLOCKING LOGIC: If any version of this family is already cited or added, skip
                    if any(f_id in seen_docs for f_id in family):
                        continue
                    
                    # Find LATEST version for the keyword expansion
                    latest_id = self._find_latest_version(doc_node_id)
                    
                    if latest_id not in seen_docs:
                        seen_docs.add(latest_id)
                        doc_data = self.graph.nodes[latest_id]
                        doc_rules = self._get_rules_for_document(latest_id)
                        
                        if not doc_rules:
                            doc_rules = [MappedRule(
                                rule_id=f"ref_{latest_id}",
                                content=f"Regelwerk {doc_data.get('title', target_doc_name)} ist für den Kontext '{keyword}' relevant.",
                                relevance_reason="Expertise-basierte Ergänzung"
                            )]

                        mapped_regs.append(MappedRegulation(
                            category="Implizite Erweiterung (Expertise)",
                            source_doc=doc_data.get("doc_title", doc_data.get("title", target_doc_name)),
                            rules=doc_rules
                        ))

        if not mapped_regs:
             mapped_regs.append(
                MappedRegulation(
                    category="System Information",
                    source_doc="Compliance Mapper",
                    rules=[MappedRule(rule_id="info_no_match", content="No explicit or implicit rules found.", relevance_reason="Analysis result")]
                )
             )

        return ExpandContextResponse(
            compliance_context_id=context_id,
            mapped_regulations=mapped_regs
        )

