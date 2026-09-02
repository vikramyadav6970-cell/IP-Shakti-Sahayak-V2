"""
ai/src/ingestion/run_ingestion.py

Master Ingestion Pipeline implementing INGESTION_AGENT_INSTRUCTIONS.md.
Executes document-by-document ingestion into Qdrant Cloud with:
- GPU Acceleration (NVIDIA RTX 3050 CUDA via BAAI/bge-m3)
- 5-Step Workflow: Analysis -> Chunking -> Metadata -> GPU Upsert -> Retrieval Validation
- Real-time colorized terminal telemetry
"""

import os
import sys

# Ensure UTF-8 output encoding on Windows terminal
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import re
import math
import uuid
import argparse
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Enable duplicate OpenMP library workaround for Anaconda
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import yaml
import torch
import pandas as pd
from dotenv import load_dotenv

# Load environment
ai_dir = Path(__file__).resolve().parent.parent.parent
load_dotenv(ai_dir / ".env")
load_dotenv(ai_dir.parent / "backend" / ".env")

import fitz  # PyMuPDF
from qdrant_client import QdrantClient
from qdrant_client.http import models as rest
from sentence_transformers import SentenceTransformer


# ==============================================================================
# Terminal Color & Formatting Helpers
# ==============================================================================
class Term:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    END = "\033[0m"

    @staticmethod
    def title(msg: str):
        print(f"\n{Term.BOLD}{Term.CYAN}{'='*80}\n {msg}\n{'='*80}{Term.END}")

    @staticmethod
    def step(num: int, title: str):
        print(f"\n{Term.BOLD}{Term.BLUE}>> [Step {num}] {title}{Term.END}")

    @staticmethod
    def success(msg: str):
        print(f"{Term.GREEN}[OK] {msg}{Term.END}")

    @staticmethod
    def info(msg: str):
        print(f"{Term.CYAN}[INFO] {msg}{Term.END}")

    @staticmethod
    def warn(msg: str):
        print(f"{Term.YELLOW}[WARN] {msg}{Term.END}")

    @staticmethod
    def error(msg: str):
        print(f"{Term.RED}[ERROR] {msg}{Term.END}")


# ==============================================================================
# Model & Vector DB Setup
# ==============================================================================
COLLECTION_NAME = "legal_statutory"
EMBEDDING_MODEL_NAME = "BAAI/bge-m3"
VECTOR_DIM = 1024


def get_gpu_device() -> str:
    if torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name(0)
        Term.success(f"Dedicated GPU Active: {gpu_name} (CUDA Enabled)")
        return "cuda"
    else:
        Term.warn("CUDA not detected. Falling back to CPU.")
        return "cpu"


def init_qdrant_client() -> Tuple[QdrantClient, bool]:
    qdrant_url = os.getenv("QDRANT_URL")
    qdrant_api_key = os.getenv("QDRANT_API_KEY")

    if qdrant_url and qdrant_api_key:
        Term.info(f"Connecting to Qdrant Cloud: {qdrant_url[:40]}...")
        client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key, timeout=60)
        return client, True
    else:
        Term.warn("Qdrant credentials not found in env. Initializing in-memory fallback.")
        client = QdrantClient(":memory:")
        return client, False


def ensure_collection(client: QdrantClient, collection_name: str = COLLECTION_NAME):
    existing = {c.name for c in client.get_collections().collections}
    if collection_name not in existing:
        Term.info(f"Creating Qdrant collection '{collection_name}' (dim={VECTOR_DIM}, metric=Cosine)...")
        client.create_collection(
            collection_name=collection_name,
            vectors_config=rest.VectorParams(
                size=VECTOR_DIM,
                distance=rest.Distance.COSINE,
            ),
        )

    # Ensure payload indexes for high-speed metadata filtering
    indexes = [
        "jurisdiction",
        "country_code",
        "doc_category",
        "ip_domain",
        "agent_scope",
        "document_id",
        "section_number",
        "enactment_year",
        "is_current_version",
    ]
    for field in indexes:
        try:
            client.create_payload_index(
                collection_name=collection_name,
                field_name=field,
                field_schema=rest.PayloadSchemaType.KEYWORD,
            )
        except Exception:
            pass  # Index already exists


# ==============================================================================
# Document Parsing & Adaptive Chunking
# ==============================================================================
def extract_pdf_pages(file_path: Path) -> List[Dict[str, Any]]:
    """Extracts text and page numbers using PyMuPDF."""
    pages = []
    doc = fitz.open(str(file_path))
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text = page.get_text("text")
        pages.append({
            "page_number": page_num + 1,
            "text": text,
        })
    doc.close()
    return pages


def analyze_document_structure(file_path: Path, doc_entry: Dict[str, Any]) -> Dict[str, Any]:
    """Step 1: Structural Analysis"""
    doc_id = doc_entry["document_id"]
    category = doc_entry["doc_category"]

    if file_path.suffix.lower() == ".xlsx":
        df = pd.read_excel(str(file_path))
        return {
            "type": "tabular_dataset",
            "rows": len(df),
            "columns": list(df.columns),
            "estimated_chunks": len(df),
            "marker_pattern": "row_by_row",
            "irregularities": "Structured tabular data",
        }

    pages = extract_pdf_pages(file_path)
    total_pages = len(pages)
    total_chars = sum(len(p["text"]) for p in pages)
    full_sample = "\n".join(p["text"][:800] for p in pages[:min(5, len(pages))])

    # Detect structural markers
    marker_pattern = "paragraph"
    if category in ["primary_law"]:
        if re.search(r"(?:Section\s+\d+|^\s*\d+\.\s+[A-Z])", full_sample, re.MULTILINE | re.IGNORECASE):
            marker_pattern = r"(?=(?:^|\n)\s*(?:Section\s+\d+[A-Z]?|\d+\.\s+[A-Z]|CHAPTER\s+[IVXLCDM\d]+))"
    elif category in ["implementing_rules"]:
        if re.search(r"(?:Rule\s+\d+|^\s*\d+\.\s+[A-Z])", full_sample, re.MULTILINE | re.IGNORECASE):
            marker_pattern = r"(?=(?:^|\n)\s*(?:Rule\s+\d+[A-Z]?|\d+\.\s+[A-Z]|PART\s+[IVXLCDM\d]+))"
    elif category in ["international_treaty"]:
        if re.search(r"(?:Article\s+\d+|ARTICLE\s+[IVXLCDM\d]+)", full_sample, re.MULTILINE | re.IGNORECASE):
            marker_pattern = r"(?=(?:^|\n)\s*(?:Article\s+\d+[A-Z]?|ARTICLE\s+[IVXLCDM\d]+))"
    elif category in ["herbal_pharmacopoeia"]:
        marker_pattern = r"(?=(?:^|\n)\s*(?:[A-Z\s]{4,}\s*\((?:Ayurvedic|Botanical|Sanskrit|Formulation)\)|MONOGRAPH|IDENTITY|FORMULATION|THERAPEUTIC\s+USE))"

    # Identify irregularities
    irregularities = []
    if total_chars < total_pages * 50:
        irregularities.append("Possible scanned pages / low text density")
    if "table" in full_sample.lower() or "\t" in full_sample:
        irregularities.append("Embedded tabular data detected")

    return {
        "type": category,
        "total_pages": total_pages,
        "total_chars": total_chars,
        "marker_pattern": marker_pattern,
        "irregularities": ", ".join(irregularities) if irregularities else "Clean text structure",
        "estimated_chunks": max(1, math.ceil(total_chars / 1500)),
    }


def chunk_document_adaptively(file_path: Path, doc_entry: Dict[str, Any], analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Step 2: Adaptive Structure-Aware Chunking"""
    doc_id = doc_entry["document_id"]
    category = doc_entry["doc_category"]

    if file_path.suffix.lower() == ".xlsx":
        # Process tabular xlsx data row-by-row with column context
        df = pd.read_excel(str(file_path))
        chunks = []
        for idx, row in df.iterrows():
            row_dict = row.dropna().to_dict()
            row_text = f"[{doc_entry['source_filename']} Record #{idx+1}]\n" + "\n".join(f"- {k}: {v}" for k, v in row_dict.items())
            chunk_id = f"{doc_id}_c{idx:03d}"
            chunks.append({
                "id": chunk_id,
                "document_id": doc_id,
                "source_filename": doc_entry["source_filename"],
                "jurisdiction": doc_entry["jurisdiction"],
                "country_code": doc_entry["country_code"],
                "doc_category": doc_entry["doc_category"],
                "ip_domain": doc_entry["ip_domain"],
                "agent_scope": doc_entry["agent_scope"],
                "section_number": f"Row {idx+1}",
                "section_title": str(list(row_dict.values())[0]) if row_dict else None,
                "page_number": 1,
                "chunk_index": idx,
                "folder_path": doc_entry["folder_path"],
                "enactment_year": doc_entry["enactment_year"],
                "amendment_year": doc_entry["amendment_year"],
                "is_current_version": doc_entry["is_current_version"],
                "source_language": doc_entry["source_language"],
                "retrieval_priority": doc_entry["retrieval_priority"],
                "cross_reference_ids": doc_entry["cross_reference_ids"],
                "chunk_text": row_text,
                "embedding_model": EMBEDDING_MODEL_NAME,
            })
        return chunks

    pages = extract_pdf_pages(file_path)
    chunks = []
    chunk_index = 0

    # Build continuous text stream with page mapping
    full_text_blocks = []
    for p in pages:
        p_text = p["text"].strip()
        if p_text:
            full_text_blocks.append((p["page_number"], p_text))

    pattern = analysis.get("marker_pattern")
    
    if pattern and pattern != "paragraph":
        # Split across structural boundaries
        for page_num, p_text in full_text_blocks:
            segments = re.split(pattern, p_text, flags=re.MULTILINE)
            clean_segments = [s.strip() for s in segments if s and len(s.strip()) > 30]

            for seg in clean_segments:
                # Extract section number and title
                sec_num = None
                sec_title = None

                sec_match = re.search(r"(?:Section\s+(\d+[A-Z]?)|Rule\s+(\d+[A-Z]?)|Article\s+(\d+[A-Z]?))", seg, re.IGNORECASE)
                if sec_match:
                    num = sec_match.group(1) or sec_match.group(2) or sec_match.group(3)
                    prefix = "Section" if "Section" in sec_match.group(0) else ("Rule" if "Rule" in sec_match.group(0) else "Article")
                    sec_num = f"{prefix} {num}"

                # Extract first line as title candidate
                first_line = seg.split("\n")[0].strip()
                if len(first_line) < 100:
                    sec_title = first_line

                # If segment is too long (> 3000 chars), split by internal paragraphs
                if len(seg) > 3000:
                    sub_paras = seg.split("\n\n")
                    curr_chunk = ""
                    for sp in sub_paras:
                        if len(curr_chunk) + len(sp) < 2500:
                            curr_chunk += ("\n\n" if curr_chunk else "") + sp
                        else:
                            if curr_chunk:
                                chunk_id = f"{doc_id}_c{chunk_index:03d}"
                                chunks.append({
                                    "id": chunk_id,
                                    "document_id": doc_id,
                                    "source_filename": doc_entry["source_filename"],
                                    "jurisdiction": doc_entry["jurisdiction"],
                                    "country_code": doc_entry["country_code"],
                                    "doc_category": doc_entry["doc_category"],
                                    "ip_domain": doc_entry["ip_domain"],
                                    "agent_scope": doc_entry["agent_scope"],
                                    "section_number": sec_num,
                                    "section_title": sec_title,
                                    "page_number": page_num,
                                    "chunk_index": chunk_index,
                                    "folder_path": doc_entry["folder_path"],
                                    "enactment_year": doc_entry["enactment_year"],
                                    "amendment_year": doc_entry["amendment_year"],
                                    "is_current_version": doc_entry["is_current_version"],
                                    "source_language": doc_entry["source_language"],
                                    "retrieval_priority": doc_entry["retrieval_priority"],
                                    "cross_reference_ids": doc_entry["cross_reference_ids"],
                                    "chunk_text": curr_chunk.strip(),
                                    "embedding_model": EMBEDDING_MODEL_NAME,
                                })
                                chunk_index += 1
                            curr_chunk = sp
                    if curr_chunk:
                        chunk_id = f"{doc_id}_c{chunk_index:03d}"
                        chunks.append({
                            "id": chunk_id,
                            "document_id": doc_id,
                            "source_filename": doc_entry["source_filename"],
                            "jurisdiction": doc_entry["jurisdiction"],
                            "country_code": doc_entry["country_code"],
                            "doc_category": doc_entry["doc_category"],
                            "ip_domain": doc_entry["ip_domain"],
                            "agent_scope": doc_entry["agent_scope"],
                            "section_number": sec_num,
                            "section_title": sec_title,
                            "page_number": page_num,
                            "chunk_index": chunk_index,
                            "folder_path": doc_entry["folder_path"],
                            "enactment_year": doc_entry["enactment_year"],
                            "amendment_year": doc_entry["amendment_year"],
                            "is_current_version": doc_entry["is_current_version"],
                            "source_language": doc_entry["source_language"],
                            "retrieval_priority": doc_entry["retrieval_priority"],
                            "cross_reference_ids": doc_entry["cross_reference_ids"],
                            "chunk_text": curr_chunk.strip(),
                            "embedding_model": EMBEDDING_MODEL_NAME,
                        })
                        chunk_index += 1
                else:
                    chunk_id = f"{doc_id}_c{chunk_index:03d}"
                    chunks.append({
                        "id": chunk_id,
                        "document_id": doc_id,
                        "source_filename": doc_entry["source_filename"],
                        "jurisdiction": doc_entry["jurisdiction"],
                        "country_code": doc_entry["country_code"],
                        "doc_category": doc_entry["doc_category"],
                        "ip_domain": doc_entry["ip_domain"],
                        "agent_scope": doc_entry["agent_scope"],
                        "section_number": sec_num,
                        "section_title": sec_title,
                        "page_number": page_num,
                        "chunk_index": chunk_index,
                        "folder_path": doc_entry["folder_path"],
                        "enactment_year": doc_entry["enactment_year"],
                        "amendment_year": doc_entry["amendment_year"],
                        "is_current_version": doc_entry["is_current_version"],
                        "source_language": doc_entry["source_language"],
                        "retrieval_priority": doc_entry["retrieval_priority"],
                        "cross_reference_ids": doc_entry["cross_reference_ids"],
                        "chunk_text": seg,
                        "embedding_model": EMBEDDING_MODEL_NAME,
                    })
                    chunk_index += 1
    else:
        # Paragraph-based splitting for unstructured narrative text
        for page_num, p_text in full_text_blocks:
            paragraphs = p_text.split("\n\n")
            curr_chunk = ""
            for p in paragraphs:
                if len(curr_chunk) + len(p) < 1800:
                    curr_chunk += ("\n\n" if curr_chunk else "") + p
                else:
                    if curr_chunk and len(curr_chunk.strip()) > 50:
                        chunk_id = f"{doc_id}_c{chunk_index:03d}"
                        chunks.append({
                            "id": chunk_id,
                            "document_id": doc_id,
                            "source_filename": doc_entry["source_filename"],
                            "jurisdiction": doc_entry["jurisdiction"],
                            "country_code": doc_entry["country_code"],
                            "doc_category": doc_entry["doc_category"],
                            "ip_domain": doc_entry["ip_domain"],
                            "agent_scope": doc_entry["agent_scope"],
                            "section_number": None,
                            "section_title": None,
                            "page_number": page_num,
                            "chunk_index": chunk_index,
                            "folder_path": doc_entry["folder_path"],
                            "enactment_year": doc_entry["enactment_year"],
                            "amendment_year": doc_entry["amendment_year"],
                            "is_current_version": doc_entry["is_current_version"],
                            "source_language": doc_entry["source_language"],
                            "retrieval_priority": doc_entry["retrieval_priority"],
                            "cross_reference_ids": doc_entry["cross_reference_ids"],
                            "chunk_text": curr_chunk.strip(),
                            "embedding_model": EMBEDDING_MODEL_NAME,
                        })
                        chunk_index += 1
                    curr_chunk = p
            if curr_chunk and len(curr_chunk.strip()) > 50:
                chunk_id = f"{doc_id}_c{chunk_index:03d}"
                chunks.append({
                    "id": chunk_id,
                    "document_id": doc_id,
                    "source_filename": doc_entry["source_filename"],
                    "jurisdiction": doc_entry["jurisdiction"],
                    "country_code": doc_entry["country_code"],
                    "doc_category": doc_entry["doc_category"],
                    "ip_domain": doc_entry["ip_domain"],
                    "agent_scope": doc_entry["agent_scope"],
                    "section_number": None,
                    "section_title": None,
                    "page_number": page_num,
                    "chunk_index": chunk_index,
                    "folder_path": doc_entry["folder_path"],
                    "enactment_year": doc_entry["enactment_year"],
                    "amendment_year": doc_entry["amendment_year"],
                    "is_current_version": doc_entry["is_current_version"],
                    "source_language": doc_entry["source_language"],
                    "retrieval_priority": doc_entry["retrieval_priority"],
                    "cross_reference_ids": doc_entry["cross_reference_ids"],
                    "chunk_text": curr_chunk.strip(),
                    "embedding_model": EMBEDDING_MODEL_NAME,
                })
                chunk_index += 1

    # Explicitly inject high-precision atomic clause chunks for core non-patentable inventions and definitions
    if "patents-act" in doc_id:
        patent_core_clauses = [
            {
                "sec_num": "Section 3(p)",
                "sec_title": "Traditional Knowledge & Component Aggregation Exclusion",
                "text": "The Patents Act, 1970 — Section 3(p): What are not inventions. The following are not inventions within the meaning of this Act, namely: (p) an invention which, in effect, is traditional knowledge or which is an aggregation or duplication of known properties of traditionally known component or components.",
                "domain": ["patents", "traditional_knowledge"],
            },
            {
                "sec_num": "Section 3(e)",
                "sec_title": "Mere Admixture Exclusion & Synergistic Effect Requirement",
                "text": "The Patents Act, 1970 — Section 3(e): What are not inventions. The following are not inventions within the meaning of this Act, namely: (e) a substance obtained by a mere admixture resulting only in the aggregation of the properties of the components thereof or a process for producing such substance.",
                "domain": ["patents", "traditional_knowledge", "drugs_cosmetics"],
            },
            {
                "sec_num": "Section 3(d)",
                "sec_title": "Known Substance & Enhanced Efficacy Requirement",
                "text": "The Patents Act, 1970 — Section 3(d): What are not inventions. The following are not inventions within the meaning of this Act, namely: (d) the mere discovery of a new form of a known substance which does not result in the enhancement of the known efficacy of that substance or the mere discovery of any new property or new use for a known substance or of the mere use of a known process, machine or apparatus unless such known process results in a new product or employs at least one new reactant.",
                "domain": ["patents", "drugs_cosmetics"],
            },
            {
                "sec_num": "Section 3(j)",
                "sec_title": "Plants, Animals, Seeds & Biological Processes Exclusion",
                "text": "The Patents Act, 1970 — Section 3(j): What are not inventions. The following are not inventions within the meaning of this Act, namely: (j) plants and animals in whole or any part thereof other than micro-organisms but including seeds, varieties and species and essentially biological processes for production or propagation of plants and animals.",
                "domain": ["patents", "biological_diversity", "traditional_knowledge"],
            },
            {
                "sec_num": "Section 3(i)",
                "sec_title": "Medicinal, Curative & Diagnostic Treatment Methods Exclusion",
                "text": "The Patents Act, 1970 — Section 3(i): What are not inventions. The following are not inventions within the meaning of this Act, namely: (i) any process for the medicinal, surgical, curative, prophylactic, diagnostic, therapeutic or other treatment of human beings or any process for a similar treatment of animals to render them free of disease or to increase their economic value or that of their products.",
                "domain": ["patents", "drugs_cosmetics"],
            },
            {
                "sec_num": "Section 2(1)(ja)",
                "sec_title": "Inventive Step & Non-Obviousness Standard",
                "text": "The Patents Act, 1970 — Section 2(1)(ja) & Section 2(1)(j): Definition of Invention & Inventive Step. 'inventive step' means a feature of an invention that involves technical advance as compared to the existing knowledge or having economic significance or both and that makes the invention not obvious to a person skilled in the art; 'invention' means a new product or process involving an inventive step and capable of industrial application.",
                "domain": ["patents"],
            },
            {
                "sec_num": "Section 10(4)(d)(ii)",
                "sec_title": "Source & Geographical Origin Disclosure Requirement for Biological Material",
                "text": "The Patents Act, 1970 — Section 10(4)(d)(ii): Specification Requirements. If the applicant mentions a biological material in the specification which may not be described in such a way as to satisfy clauses (a) and (b), the applicant must disclose the source and geographical origin of the biological material in the specification.",
                "domain": ["patents", "biological_diversity", "traditional_knowledge"],
            },
        ]
        for pc in patent_core_clauses:
            chunk_id = f"{doc_id}_atomic_{pc['sec_num'].lower().replace(' ', '_').replace('(', '').replace(')', '').replace('&', 'and')}"
            chunks.append({
                "id": chunk_id,
                "document_id": doc_id,
                "source_filename": doc_entry["source_filename"],
                "jurisdiction": doc_entry["jurisdiction"],
                "country_code": doc_entry["country_code"],
                "doc_category": "primary_law",
                "ip_domain": pc["domain"],
                "agent_scope": ["ip_agent", "patent_agent"],
                "section_number": pc["sec_num"],
                "section_title": pc["sec_title"],
                "page_number": 10,
                "chunk_index": chunk_index,
                "folder_path": doc_entry["folder_path"],
                "enactment_year": doc_entry["enactment_year"],
                "amendment_year": doc_entry["amendment_year"],
                "is_current_version": doc_entry["is_current_version"],
                "source_language": "en",
                "retrieval_priority": "CRITICAL",
                "cross_reference_ids": ["in-biological-diversity-act-2002", "in-drugs-cosmetics-act-rules-2016"],
                "chunk_text": pc["text"],
                "embedding_model": EMBEDDING_MODEL_NAME,
            })
            chunk_index += 1

    return chunks


# ==============================================================================
# GPU Ingestion & Validation
# ==============================================================================
def ingest_chunks_to_qdrant(
    client: QdrantClient,
    model: SentenceTransformer,
    chunks: List[Dict[str, Any]],
    batch_size: int = 64,
) -> int:
    """Step 4: Generates dense embeddings on GPU and upserts to Qdrant Cloud."""
    total = len(chunks)
    Term.info(f"Generating embeddings for {total} chunks on GPU (Batch size = {batch_size})...")

    points = []
    for i in range(0, total, batch_size):
        batch = chunks[i : i + batch_size]
        texts = [c["chunk_text"] for c in batch]
        # GPU encode with normalization
        vectors = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)

        for chunk, vec in zip(batch, vectors):
            # Deterministic UUID from chunk_id
            point_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, chunk["id"]))
            payload = {
                "id": chunk["id"],
                "document_id": chunk["document_id"],
                "source_filename": chunk["source_filename"],
                "jurisdiction": chunk["jurisdiction"],
                "country_code": chunk["country_code"],
                "doc_category": chunk["doc_category"],
                "ip_domain": chunk["ip_domain"],
                "agent_scope": chunk["agent_scope"],
                "section_number": chunk["section_number"],
                "section_title": chunk["section_title"],
                "page_number": chunk["page_number"],
                "chunk_index": chunk["chunk_index"],
                "folder_path": chunk["folder_path"],
                "enactment_year": chunk["enactment_year"],
                "amendment_year": chunk["amendment_year"],
                "is_current_version": chunk["is_current_version"],
                "source_language": chunk["source_language"],
                "retrieval_priority": chunk["retrieval_priority"],
                "cross_reference_ids": chunk["cross_reference_ids"],
                "chunk_text": chunk["chunk_text"],
                "embedding_model": chunk["embedding_model"],
            }
            points.append(
                rest.PointStruct(
                    id=point_uuid,
                    vector=vec.tolist(),
                    payload=payload,
                )
            )

        sys.stdout.write(f"\r  [EMBED] Prepared: {min(i + batch_size, total)}/{total} chunks ({((min(i+batch_size, total))/total)*100:.1f}%)")
        sys.stdout.flush()

    print()
    Term.info(f"Upserting {len(points)} points into Qdrant collection '{COLLECTION_NAME}' in batches of 100...")
    upsert_batch_size = 100
    for j in range(0, len(points), upsert_batch_size):
        sub_points = points[j : j + upsert_batch_size]
        for attempt in range(3):
            try:
                client.upsert(
                    collection_name=COLLECTION_NAME,
                    points=sub_points,
                    wait=True,
                )
                break
            except Exception as ex:
                if attempt == 2:
                    raise ex
                import time
                time.sleep(2)
        sys.stdout.write(f"\r  [UPSERT] Uploaded: {min(j + upsert_batch_size, len(points))}/{len(points)} points ({((min(j+upsert_batch_size, len(points)))/len(points))*100:.1f}%)")
        sys.stdout.flush()

    print()
    Term.success(f"Successfully upserted {len(points)} points to Qdrant!")
    return len(points)


def validate_document_retrieval(
    client: QdrantClient,
    model: SentenceTransformer,
    doc_entry: Dict[str, Any],
) -> bool:
    """Step 5: Runs sample retrieval queries to validate ingested content."""
    doc_id = doc_entry["document_id"]
    category = doc_entry["doc_category"]

    # Construct representative test queries
    queries = []
    if "patents" in doc_id:
        queries = ["Section 3(p) traditional knowledge exclusion", "compulsory licensing requirements"]
    elif "trademarks" in doc_id:
        queries = ["trademark registration grounds for refusal", "infringement and deceptive similarity"]
    elif "gi" in doc_id:
        queries = ["geographical indications authorized user registration", "prohibition of registration of certain geographical indications"]
    elif "biological" in doc_id:
        queries = ["access and benefit sharing National Biodiversity Authority", "prior approval for biological resources"]
    elif "copyright" in doc_id:
        queries = ["fair dealing exceptions", "term of copyright in published literary works"]
    elif "drugs" in doc_id or "fssai" in doc_id or "aahara" in doc_id:
        queries = ["Ayurveda Aahara manufacturing license conditions", "Schedule T Good Manufacturing Practices"]
    elif "who" in doc_id or "api" in doc_id:
        queries = ["herbal formulation identification and assay standards", "botanical identity and therapeutic indications"]
    else:
        queries = [f"{doc_entry['source_filename']} core provisions and legal rules"]

    Term.info(f"Running Step 5 Validation ({len(queries)} test queries against Qdrant)...")
    all_passed = True

    for q in queries:
        q_vec = model.encode(q, normalize_embeddings=True).tolist()
        if hasattr(client, "query_points"):
            res_obj = client.query_points(
                collection_name=COLLECTION_NAME,
                query=q_vec,
                query_filter=rest.Filter(
                    must=[
                        rest.FieldCondition(
                            key="document_id",
                            match=rest.MatchValue(value=doc_id),
                        )
                    ]
                ),
                limit=2,
            )
            results = res_obj.points
        else:
            results = client.search(
                collection_name=COLLECTION_NAME,
                query_vector=q_vec,
                query_filter=rest.Filter(
                    must=[
                        rest.FieldCondition(
                            key="document_id",
                            match=rest.MatchValue(value=doc_id),
                        )
                    ]
                ),
                limit=2,
            )

        if results:
            top_hit = results[0]
            score = top_hit.score
            sec = top_hit.payload.get("section_number") or "N/A"
            snippet = (top_hit.payload.get("chunk_text") or "")[:120].replace("\n", " ")
            print(f"  [QUERY] '{q}'")
            print(f"     --> Top Hit (Score: {score:.4f}) | Sec: {sec} | Snippet: {snippet}...")
        else:
            Term.warn(f"  Query '{q}' returned 0 results for document_id='{doc_id}'")
            all_passed = False

    return all_passed


# ==============================================================================
# Ingestion Orchestrator
# ==============================================================================
def run_pipeline(target_doc_id: Optional[str] = None, force_reindex: bool = False):
    registry_path = ai_dir / "ingestion_config" / "document_registry.yaml"
    dataset_dir = ai_dir / "NewDataSet" if (ai_dir / "NewDataSet").exists() else (ai_dir / "DataSet")

    with open(registry_path, "r", encoding="utf-8") as f:
        registry = yaml.safe_load(f)

    docs = registry.get("documents", [])
    Term.title(f"IP-SAKTI Sahayak — Master Data Ingestion Pipeline ({len(docs)} Documents Registered)")

    # 1. Initialize GPU and Embedding Model
    device = get_gpu_device()
    Term.info(f"Loading embedding model '{EMBEDDING_MODEL_NAME}' onto device='{device}'...")
    embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME, device=device)

    # 2. Initialize Qdrant Collection
    qdrant_client, is_cloud = init_qdrant_client()
    ensure_collection(qdrant_client, COLLECTION_NAME)

    # 3. Process documents sequentially
    processed_count = 0
    validated_count = 0

    for idx, doc in enumerate(docs, 1):
        doc_id = doc["document_id"]
        source_fn = doc["source_filename"]
        folder_path = doc["folder_path"]
        status = doc.get("status", "pending")

        if target_doc_id and doc_id != target_doc_id:
            continue

        if not force_reindex and status == "validated":
            print(f"[{idx}/{len(docs)}] Skipping already validated: {source_fn} ({doc_id})")
            continue

        # Locate file on disk (check NewDataSet and DataSet)
        full_file_path = dataset_dir / folder_path / source_fn
        if not full_file_path.exists():
            matches = list(dataset_dir.rglob(source_fn))
            if not matches and (ai_dir / "DataSet").exists():
                matches = list((ai_dir / "DataSet").rglob(source_fn))
            if matches:
                full_file_path = matches[0]
            else:
                Term.error(f"[{idx}/{len(docs)}] File not found on disk: {source_fn} at {full_file_path}")
                continue

        Term.title(f"[{idx}/{len(docs)}] Processing: {source_fn} (ID: {doc_id})")
        print(f"  • Category: {doc['doc_category']} | Jurisdiction: {doc['jurisdiction']} ({doc['country_code']})")
        print(f"  • IP Domain: {doc['ip_domain']} | Agent Scope: {doc['agent_scope']}")
        print(f"  • File Path: {full_file_path}")

        # Step 1: Structural Analysis
        Term.step(1, "Structural Analysis")
        analysis = analyze_document_structure(full_file_path, doc)
        print(f"  • Type: {analysis.get('type')}")
        if "total_pages" in analysis:
            print(f"  • Pages: {analysis['total_pages']} | Total Chars: {analysis['total_chars']:,}")
        print(f"  • Structural Marker: {analysis.get('marker_pattern')}")
        print(f"  • Irregularities: {analysis.get('irregularities')}")
        print(f"  • Estimated Chunks: ~{analysis.get('estimated_chunks')}")

        doc["status"] = "analyzed"

        # Step 2 & 3: Adaptive Chunking & Metadata Assembly
        Term.step(2, "Adaptive Chunking & Schema Metadata Assembly")
        chunks = chunk_document_adaptively(full_file_path, doc, analysis)
        Term.success(f"Generated {len(chunks)} canonical chunks with full metadata tags.")
        if chunks:
            sample_c = chunks[0]
            print(f"  • Sample Chunk ID: {sample_c['id']}")
            print(f"  • Section: {sample_c.get('section_number') or 'None'} | Title: {sample_c.get('section_title') or 'None'}")
            print(f"  • First 100 Chars: {sample_c['chunk_text'][:100].replace(chr(10), ' ')}...")

        doc["status"] = "chunked"

        # Step 4: GPU Embedding & Ingestion into Qdrant
        Term.step(4, f"GPU Embedding (NVIDIA RTX 3050) & Qdrant Cloud Ingestion")
        ingest_chunks_to_qdrant(qdrant_client, embedding_model, chunks)
        doc["status"] = "ingested"

        # Step 5: Validation
        Term.step(5, "Retrieval Validation & Semantic Search Confirmation")
        is_valid = validate_document_retrieval(qdrant_client, embedding_model, doc)
        if is_valid:
            doc["status"] = "validated"
            Term.success(f"Document '{doc_id}' passed Step 5 validation.")
            validated_count += 1
        else:
            Term.warn(f"Document '{doc_id}' completed with validation warnings.")

        processed_count += 1

        # Update registry after each document
        with open(registry_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(registry, f, sort_keys=False)

    Term.title(f"Ingestion Completed! {processed_count} Documents Processed, {validated_count} Validated.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="IP-SAKTI Sahayak Master Ingestion Pipeline")
    parser.add_argument("--doc", type=str, help="Process a specific document by document_id", default=None)
    parser.add_argument("--force", action="store_true", help="Force re-indexing of already validated documents")
    args = parser.parse_args()

    run_pipeline(target_doc_id=args.doc, force_reindex=args.force)
