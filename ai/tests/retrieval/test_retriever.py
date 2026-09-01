"""
ai/tests/retrieval/test_retriever.py

Unit tests for in-memory Qdrant indexing, sparse term matching, and hybrid retrieval.
"""

from src.embeddings.embedding_provider import MockEmbeddingProvider
from src.embeddings.sparse_provider import BM25SparseProvider
from src.ingestion.chunker import Chunker
from src.ingestion.indexer import DocumentIndexer
from src.ingestion.strategy_analyzer import StrategyAnalyzer
from src.retrieval.qdrant_manager import QdrantManager
from src.retrieval.retriever import HybridRetriever


def test_indexing_and_hybrid_retrieval_flow():
    # 1. Setup in-memory Qdrant, mock dense provider, and sparse provider
    qdrant = QdrantManager(in_memory=True)
    dense_provider = MockEmbeddingProvider()
    sparse_provider = BM25SparseProvider()

    indexer = DocumentIndexer(qdrant, dense_provider, sparse_provider)
    retriever = HybridRetriever(qdrant, dense_provider, sparse_provider)

    # 2. Prepare statutory and treaty documents
    doc_india = {
        "id": "doc_in_patents_act_1970",
        "title": "The Patents Act, 1970",
        "jurisdiction": "INDIA",
        "document_type": "STATUTE",
        "source_url": "https://wipolex.wipo.int/en/legislation/details/2143",
        "verification_status": "VERIFIED_OFFICIAL_GAZETTE",
    }
    text_india = """
    Section 3. What are not inventions.
    (p) an invention which in effect is traditional knowledge or which is an aggregation or duplication of known properties of traditionally known component or components.
    Section 3(d) the mere discovery of a new form of a known substance which does not result in the enhancement of the known efficacy of that substance.
    """

    doc_intl = {
        "id": "doc_intl_trips",
        "title": "TRIPS Agreement",
        "jurisdiction": "INTERNATIONAL",
        "document_type": "TREATY",
        "source_url": "https://wipolex.wipo.int/en/treaties/details/231",
        "verification_status": "VERIFIED_OFFICIAL_TREATY",
    }
    text_intl = """
    Article 27: Patentable Subject Matter
    1. Patents shall be available for any inventions, whether products or processes, in all fields of technology.
    """

    # 3. Chunk and index
    strat_in = StrategyAnalyzer.analyze_document(doc_india["id"], "legal_statutory", "STATUTE", text_india)
    chunks_in = Chunker.chunk_document(doc_india, text_india, strat_in)

    strat_intl = StrategyAnalyzer.analyze_document(doc_intl["id"], "international_export", "TREATY", text_intl)
    chunks_intl = Chunker.chunk_document(doc_intl, text_intl, strat_intl)

    index_result = indexer.index_chunks(chunks_in + chunks_intl)
    assert index_result.get("legal_statutory", 0) >= 1
    assert index_result.get("international_export", 0) >= 1

    # 4. Query India Law
    results_in = retriever.retrieve(
        query="Is traditional Ayurvedic knowledge patentable under Section 3(p)?",
        jurisdiction="INDIA",
        intent="PATENT",
        top_k=3,
    )

    assert len(results_in) >= 1
    top_hit = results_in[0]
    assert "Patents Act" in top_hit.doc_title
    assert top_hit.jurisdiction == "INDIA"
    assert top_hit.verification_status == "VERIFIED_OFFICIAL_GAZETTE"

    # 5. Query International Law
    results_intl = retriever.retrieve(
        query="TRIPS Article 27 patentable subject matter",
        jurisdiction="INTERNATIONAL",
        intent="EXPORT",
        top_k=3,
    )

    assert len(results_intl) >= 1
    top_intl_hit = results_intl[0]
    assert "TRIPS" in top_intl_hit.doc_title
