"""
ai/src/ingestion/chunker.py

Phase B: Deterministic chunk execution & canonical payload assembly.
Applies the logged ChunkingStrategyConfig to produce fully structured,
breadcrumb-prefixed chunks matching ARCHITECTURE.md §4b.
"""

from dataclasses import asdict, dataclass
import json
from pathlib import Path
import re
from typing import Any, Dict, List, Optional

from src.ingestion.strategy_analyzer import ChunkingStrategyConfig


@dataclass
class CanonicalChunk:
    """Canonical chunk representation matching Qdrant payload schema (Architecture §4b)."""
    id: str
    content: str
    target_collection: str
    jurisdiction: str
    document_id: str
    parent_document: str
    source_url: str
    verification_status: str
    chunk_index: int
    payload: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class Chunker:
    """Deterministic chunk executor."""

    @staticmethod
    def chunk_document(
        doc_metadata: Dict[str, Any],
        raw_text: str,
        strategy: ChunkingStrategyConfig,
    ) -> List[CanonicalChunk]:
        """
        Splits document text per the approved strategy and constructs canonical payload records.
        """
        doc_id = doc_metadata.get("id", "doc_unknown")
        doc_title = doc_metadata.get("title", "")
        jurisdiction = doc_metadata.get("jurisdiction", "INDIA")
        source_url = doc_metadata.get("source_url", "")
        verification_status = doc_metadata.get("verification_status", "VERIFIED_OFFICIAL_GAZETTE")
        target_collection = strategy.target_collection

        # Split using regex primary pattern
        pattern = strategy.primary_split_pattern
        raw_splits = re.split(pattern, raw_text, flags=re.MULTILINE)
        splits = [s.strip() for s in raw_splits if s and len(s.strip()) > 0]

        chunks: List[CanonicalChunk] = []
        chunk_idx = 0

        for segment in splits:
            if len(segment) < strategy.min_chunk_chars:
                # Merge small fragments with previous if possible or skip empty headers
                if chunks and len(chunks[-1].content) + len(segment) < strategy.max_chunk_chars:
                    prev = chunks[-1]
                    prev.content += "\n" + segment
                    prev.payload["content"] = prev.content
                    continue

            # Extract section / article / monograph identifiers from segment header
            section_ref = ""
            article_ref = ""
            chapter_ref = ""

            sec_match = re.search(r"(?:Section\s+(\d+[A-Z]?)|§\s*(\d+[A-Z]?))", segment, re.IGNORECASE)
            if sec_match:
                section_ref = f"Section {sec_match.group(1) or sec_match.group(2)}"

            art_match = re.search(r"(?:Article\s+(\d+[A-Z]?))", segment, re.IGNORECASE)
            if art_match:
                article_ref = f"Article {art_match.group(1)}"

            # Assemble breadcrumb prefix to make chunk self-describing
            breadcrumb_parts = [doc_title]
            if section_ref:
                breadcrumb_parts.append(section_ref)
            elif article_ref:
                breadcrumb_parts.append(article_ref)
            
            breadcrumb_header = " › ".join(breadcrumb_parts)
            chunk_content = f"[{breadcrumb_header}]\n{segment}"

            chunk_id = f"{doc_id}_c{chunk_idx}"
            if section_ref:
                sec_clean = section_ref.lower().replace(" ", "_").replace("(", "").replace(")", "")
                chunk_id = f"{doc_id}_{sec_clean}_{chunk_idx}"
            elif article_ref:
                art_clean = article_ref.lower().replace(" ", "_")
                chunk_id = f"{doc_id}_{art_clean}_{chunk_idx}"

            payload: Dict[str, Any] = {
                "document_id": doc_id,
                "doc_title": doc_title,
                "jurisdiction": jurisdiction.lower(),
                "document_type": strategy.document_type,
                "section_ref": section_ref or None,
                "article_ref": article_ref or None,
                "chapter_ref": chapter_ref or None,
                "source_url": source_url,
                "verification_status": verification_status,
                "chunk_index": chunk_idx,
                "parent_document": doc_id,
                "target_collection": target_collection,
                "content": chunk_content,
            }

            # Collection-specific payload fields
            if target_collection == "legal_statutory":
                payload["ip_domain"] = "patents_and_ayurveda"
            elif target_collection == "case_law_prior_art":
                payload["case_title"] = doc_title
            elif target_collection == "standards_formulations":
                payload["monograph_name"] = doc_title
            elif target_collection == "procedural_forms_checklists":
                payload["form_name"] = doc_title

            canonical_chunk = CanonicalChunk(
                id=chunk_id,
                content=chunk_content,
                target_collection=target_collection,
                jurisdiction=jurisdiction,
                document_id=doc_id,
                parent_document=doc_id,
                source_url=source_url,
                verification_status=verification_status,
                chunk_index=chunk_idx,
                payload=payload,
            )

            chunks.append(canonical_chunk)
            chunk_idx += 1

        return chunks
