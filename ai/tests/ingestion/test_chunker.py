"""
ai/tests/ingestion/test_chunker.py

Unit tests for strategy analyzer and deterministic canonical chunker.
"""

from src.ingestion.strategy_analyzer import StrategyAnalyzer, ChunkingStrategyConfig
from src.ingestion.chunker import Chunker, CanonicalChunk


def test_statutory_chunking():
    doc_meta = {
        "id": "doc_in_patents_act_1970",
        "title": "The Patents Act, 1970",
        "jurisdiction": "INDIA",
        "document_type": "STATUTE",
        "source_url": "https://wipolex.wipo.int/en/legislation/details/2143",
        "verification_status": "VERIFIED_OFFICIAL_GAZETTE",
    }

    sample_text = """
    Section 3. What are not inventions.
    The following are not inventions within the meaning of this Act:
    (d) the mere discovery of a new form of a known substance which does not result in the enhancement of the known efficacy of that substance;
    (e) a substance obtained by a mere admixture resulting only in the aggregation of the properties of the components thereof;
    (p) an invention which in effect is traditional knowledge or which is an aggregation or duplication of known properties of traditionally known component or components.

    Section 5. [Repealed by Patents (Amendment) Act, 2005].
    """

    strategy = StrategyAnalyzer.analyze_document(
        document_id=doc_meta["id"],
        target_collection="legal_statutory",
        document_type=doc_meta["document_type"],
        sample_text=sample_text,
    )

    chunks = Chunker.chunk_document(doc_meta, sample_text, strategy)
    assert len(chunks) >= 1

    chunk_3 = chunks[0]
    assert "Patents Act, 1970" in chunk_3.content
    assert "Section 3" in chunk_3.payload.get("section_ref", "")
    assert "traditional knowledge" in chunk_3.content
    assert chunk_3.payload["target_collection"] == "legal_statutory"
    assert chunk_3.payload["jurisdiction"] == "india"


def test_treaty_chunking():
    doc_meta = {
        "id": "doc_intl_trips",
        "title": "Agreement on Trade-Related Aspects of Intellectual Property Rights",
        "jurisdiction": "INTERNATIONAL",
        "document_type": "TREATY",
        "source_url": "https://wipolex.wipo.int/en/treaties/details/231",
        "verification_status": "VERIFIED_OFFICIAL_TREATY",
    }

    sample_text = """
    Article 27: Patentable Subject Matter
    1. Subject to the provisions of paragraphs 2 and 3, patents shall be available for any inventions, whether products or processes, in all fields of technology, provided that they are new, involve an inventive step and are capable of industrial application.
    2. Members may exclude from patentability inventions, the prevention within their territory of the commercial exploitation of which is necessary to protect ordre public or morality, including to protect human, animal or plant life or health or to avoid serious prejudice to the environment, provided that such exclusion is not made merely because the exploitation is prohibited by their law.

    Article 28: Rights Conferred
    1. A patent shall confer on its owner the following exclusive rights...
    """

    strategy = StrategyAnalyzer.analyze_document(
        document_id=doc_meta["id"],
        target_collection="international_export",
        document_type=doc_meta["document_type"],
        sample_text=sample_text,
    )

    chunks = Chunker.chunk_document(doc_meta, sample_text, strategy)
    assert len(chunks) >= 2

    c1 = chunks[0]
    assert "Article 27" in c1.payload.get("article_ref", "")
    assert c1.payload["target_collection"] == "international_export"
    assert c1.payload["jurisdiction"] == "international"
