"""
ai/data/corpus/seed/load_seed.py

Embeds and inserts the verified seed records (legal_knowledge.jsonl,
ipr_prior_art.jsonl, ayush_tk.jsonl) into a Postgres/pgvector `chunks` table.

Deliberately does NOT touch schema_examples_DO_NOT_EMBED.jsonl \u2014 that file exists
for unit tests only, not for the real vector DB. See README.md in this folder
for why.

This script is meant to be run once, early, to prove the ingestion -> embedding
-> retrieval path works end to end on real content \u2014 a fast-tracked stand-in for
Phase 1 (T1.2/T1.3) + Phase 2 (T2.1) using pre-chunked JSONL instead of raw PDFs.
It is NOT a substitute for building the real parser/chunker in those tasks; it
does substitute for producing pgvector-embedded rows to develop and test the
retrieval layer (T2.1-T2.3) against before that pipeline exists.

Usage:
    pip install sentence-transformers psycopg2-binary pgvector python-dotenv
    export DATABASE_URL=postgresql://user:pass@localhost:5432/dbname
    python load_seed.py

Requires the pgvector extension enabled and a `chunks` table matching the shape
below. If backend/ai has already created this table via migration (see
ai/prompts/phases.md T2.1), point this script at that table/column names
instead of the CREATE TABLE below \u2014 don't create a duplicate table.
"""

import json
import os
import sys
from pathlib import Path

SEED_DIR = Path(__file__).parent
COLLECTIONS = {
    "legal_knowledge": SEED_DIR / "legal_knowledge.jsonl",
    "ipr_prior_art": SEED_DIR / "ipr_prior_art.jsonl",
    "ayush_tk": SEED_DIR / "ayush_tk.jsonl",
}

# Which field in each record holds the text to embed \u2014 collections don't share
# a single text field name per the schema (legal_knowledge/regulatory_standards
# use "text", ipr_prior_art uses "abstract"+"description", ayush_tk uses
# "traditional_use").
EMBED_TEXT_BUILDERS = {
    "legal_knowledge": lambda r: r.get("text", ""),
    "ipr_prior_art": lambda r: " ".join(
        filter(None, [r.get("title"), r.get("abstract"), r.get("description")])
    ),
    "ayush_tk": lambda r: " ".join(
        filter(None, [r.get("title"), r.get("traditional_use")])
    ),
}


def load_records(path: Path) -> list[dict]:
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
    return records


def get_embedder():
    """
    Loads BAAI/bge-m3 per ai/coding_conventions.md's Stack section. If this
    isn't installed yet (e.g. running this before Phase 0 T0.3 is done), fall
    back to a clear error rather than silently writing zero-vectors \u2014 a chunk
    with a fake embedding is worse than no chunk, same principle as everywhere
    else in this project.
    """
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        print(
            "sentence-transformers not installed. Run: "
            "pip install sentence-transformers",
            file=sys.stderr,
        )
        sys.exit(1)
    model = SentenceTransformer("BAAI/bge-m3")
    return lambda texts: model.encode(texts, normalize_embeddings=True).tolist()


def ensure_table(cur):
    """
    Only creates the table if it doesn't already exist \u2014 if backend has already
    migrated a `chunks` table (T2.1 in backend/prompts/phases.md), this is a
    no-op and you should confirm the column names match before relying on it.
    """
    cur.execute(
        """
        CREATE EXTENSION IF NOT EXISTS vector;
        CREATE TABLE IF NOT EXISTS chunks (
            id TEXT PRIMARY KEY,
            collection TEXT NOT NULL,
            jurisdiction TEXT,
            document_type TEXT,
            title TEXT,
            section TEXT,
            source_url TEXT,
            source_type TEXT,
            verification_status TEXT,
            text TEXT NOT NULL,
            metadata JSONB,
            embedding VECTOR(1024)
        );
        CREATE INDEX IF NOT EXISTS chunks_jurisdiction_idx ON chunks (jurisdiction);
        CREATE INDEX IF NOT EXISTS chunks_collection_idx ON chunks (collection);
        """
    )


def main():
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("Set DATABASE_URL before running.", file=sys.stderr)
        sys.exit(1)

    try:
        import psycopg2
        import psycopg2.extras
    except ImportError:
        print(
            "psycopg2 not installed. Run: pip install psycopg2-binary",
            file=sys.stderr,
        )
        sys.exit(1)

    embed = get_embedder()

    conn = psycopg2.connect(database_url)
    cur = conn.cursor()
    ensure_table(cur)

    total_inserted = 0
    for collection, path in COLLECTIONS.items():
        if not path.exists():
            print(f"Skipping {collection}: {path} not found.")
            continue

        records = load_records(path)
        text_builder = EMBED_TEXT_BUILDERS[collection]
        texts = [text_builder(r) for r in records]
        embeddings = embed(texts)

        for record, text, embedding in zip(records, texts, embeddings):
            cur.execute(
                """
                INSERT INTO chunks
                    (id, collection, jurisdiction, document_type, title,
                     section, source_url, source_type, verification_status,
                     text, metadata, embedding)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    text = EXCLUDED.text,
                    embedding = EXCLUDED.embedding,
                    metadata = EXCLUDED.metadata
                """,
                (
                    record["id"],
                    collection,
                    record.get("jurisdiction"),
                    record.get("document_type") or record.get("record_type"),
                    record.get("title"),
                    record.get("section"),
                    record.get("source_url"),
                    record.get("source_type"),
                    record.get("verification_status"),
                    text,
                    json.dumps(record),
                    embedding,
                ),
            )
            total_inserted += 1

        print(f"{collection}: embedded and inserted {len(records)} records.")

    conn.commit()
    cur.close()
    conn.close()
    print(f"Done. {total_inserted} chunks embedded and inserted total.")
    print(
        "Reminder: records with verification_status="
        "'VERIFIED_CORE_FACTS_SOME_FIELDS_UNCONFIRMED' or "
        "'VERIFIED_FACTS_PARAPHRASED_TEXT' are safe for facts but their exact "
        "wording/dates should be confirmed before being quoted verbatim to a "
        "user \u2014 see README.md in this folder."
    )


if __name__ == "__main__":
    main()
