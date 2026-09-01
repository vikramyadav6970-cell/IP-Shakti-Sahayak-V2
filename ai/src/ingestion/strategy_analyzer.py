"""
ai/src/ingestion/strategy_analyzer.py

Phase A: Adaptive per-document chunking strategy analysis.
Analyzes document structure and emits structured splitting configs to prevent
malformed or under-sized duplicate heading chunks (Architecture §4a).
"""

from dataclasses import asdict, dataclass
import json
from pathlib import Path
import re
from typing import Any, Dict, List, Optional


@dataclass
class ChunkingStrategyConfig:
    """Structured configuration defining how a specific document must be chunked."""
    document_id: str
    target_collection: str
    document_type: str
    split_strategy: str          # "SECTION_BY_CLAUSE", "ARTICLE_BY_PARAGRAPH", "MONOGRAPH_BLOCKS", "FORM_FIELDS", "WHOLE_CASE"
    primary_split_pattern: str   # Regex for primary boundaries
    sub_split_pattern: Optional[str] = None
    min_chunk_chars: int = 150
    max_chunk_chars: int = 3500
    overlap_chars: int = 100
    breadcrumb_fields: List[str] = None  # e.g. ["doc_title", "chapter", "section"]
    custom_metadata_extractors: Dict[str, str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class StrategyAnalyzer:
    """Analyzes text structure and determines optimal deterministic chunking strategy."""

    @staticmethod
    def analyze_document(
        document_id: str,
        target_collection: str,
        document_type: str,
        sample_text: str,
    ) -> ChunkingStrategyConfig:
        """
        Produce a tailored chunking strategy configuration based on collection and content patterns.
        """
        # 1. Statutory Acts & Rules (legal_statutory)
        if target_collection == "legal_statutory":
            # Detect section number formatting
            split_pattern = r"(?=(?:^|\n)\s*(?:Section\s+\d+[A-Z]?|\d+\.\s+[A-Z]|CHAPTER\s+[IVXLCDM\d]+))"
            
            return ChunkingStrategyConfig(
                document_id=document_id,
                target_collection=target_collection,
                document_type=document_type,
                split_strategy="SECTION_BY_CLAUSE",
                primary_split_pattern=split_pattern,
                sub_split_pattern=r"(?=(?:^|\n)\s*\(\d+\))",  # Sub-split long sub-sections: (1), (2)
                min_chunk_chars=100,
                max_chunk_chars=3000,
                breadcrumb_fields=["doc_title", "chapter_title", "section_number", "section_title"],
            )

        # 2. Treaties & International Guidance (international_export)
        elif target_collection == "international_export":
            split_pattern = r"(?=(?:^|\n)\s*(?:Article\s+\d+|ARTICLE\s+[IVXLCDM\d]+))"
            return ChunkingStrategyConfig(
                document_id=document_id,
                target_collection=target_collection,
                document_type=document_type,
                split_strategy="ARTICLE_BY_PARAGRAPH",
                primary_split_pattern=split_pattern,
                sub_split_pattern=r"(?=(?:^|\n)\s*\d+\.\s+)",
                min_chunk_chars=100,
                max_chunk_chars=3500,
                breadcrumb_fields=["doc_title", "part_title", "article_number", "article_title"],
            )

        # 3. Pharmacopoeial Monographs (standards_formulations)
        elif target_collection == "standards_formulations":
            split_pattern = r"(?=(?:^|\n)(?:MONOGRAPH|IDENTITY|PURITY|ASSAY|FORMULATION|THERAPEUTIC\s+USE):?)"
            return ChunkingStrategyConfig(
                document_id=document_id,
                target_collection=target_collection,
                document_type=document_type,
                split_strategy="MONOGRAPH_BLOCKS",
                primary_split_pattern=split_pattern,
                sub_split_pattern=None,
                min_chunk_chars=200,
                max_chunk_chars=2500,
                breadcrumb_fields=["doc_title", "botanical_name", "monograph_section"],
            )

        # 4. Procedural & Filing Forms (procedural_forms_checklists)
        elif target_collection == "procedural_forms_checklists":
            split_pattern = r"(?=(?:^|\n)(?:Step\s+\d+|Field\s+\d+|FORM\s+[I|II|III|IV|\d]+|Clause\s+\d+))"
            return ChunkingStrategyConfig(
                document_id=document_id,
                target_collection=target_collection,
                document_type=document_type,
                split_strategy="FORM_FIELDS",
                primary_split_pattern=split_pattern,
                min_chunk_chars=100,
                max_chunk_chars=2500,
                breadcrumb_fields=["doc_title", "form_name", "procedure_step"],
            )

        # 5. Case Law & Biopiracy Prior Art (case_law_prior_art)
        elif target_collection == "case_law_prior_art":
            return ChunkingStrategyConfig(
                document_id=document_id,
                target_collection=target_collection,
                document_type=document_type,
                split_strategy="WHOLE_CASE",
                primary_split_pattern=r"(?=(?:^|\n)(?:CASE\s+RECORD|DECISION|REASONING):?)",
                min_chunk_chars=250,
                max_chunk_chars=4000,
                breadcrumb_fields=["case_name", "patent_number", "jurisdiction", "outcome"],
            )

        # Default fallback
        return ChunkingStrategyConfig(
            document_id=document_id,
            target_collection=target_collection,
            document_type=document_type,
            split_strategy="PARAGRAPH_FALLBACK",
            primary_split_pattern=r"\n\n+",
            min_chunk_chars=150,
            max_chunk_chars=2500,
            breadcrumb_fields=["doc_title"],
        )

    @classmethod
    def analyze_manifest(
        cls,
        manifest_path: Path,
        output_strategies_path: Path,
    ) -> List[ChunkingStrategyConfig]:
        """Reads corpus manifest, generates strategies, and writes chunking_strategies.jsonl."""
        strategies = []
        with open(manifest_path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                doc = json.loads(line)
                strategy = cls.analyze_document(
                    document_id=doc["id"],
                    target_collection=doc["target_collection"],
                    document_type=doc["document_type"],
                    sample_text=doc.get("title", ""),
                )
                strategies.append(strategy)

        output_strategies_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_strategies_path, "w", encoding="utf-8") as out:
            for s in strategies:
                out.write(json.dumps(s.to_dict()) + "\n")

        return strategies
