"""Embedding pipeline — chunk documents, generate embeddings, upsert to ChromaDB."""

from pathlib import Path

import chromadb

from src.config.settings import settings
from src.rag.chunker import Chunk, chunk_all_documents

COLLECTION_NAME = "primeev_factory_docs"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

DOCS_DIR = Path(__file__).parent / "documents"


def get_chroma_client() -> chromadb.ClientAPI:
    """Get ChromaDB client — uses HTTP client for Docker, ephemeral for testing."""
    try:
        return chromadb.HttpClient(
            host=settings.chroma_host,
            port=settings.chroma_port,
        )
    except Exception:
        return chromadb.EphemeralClient()


def index_all_documents(docs_dir: Path | None = None) -> int:
    """Chunk all documents, embed, and upsert to ChromaDB. Returns chunk count."""
    docs_dir = docs_dir or DOCS_DIR

    print(f"  Scanning documents in {docs_dir}...")
    chunks = chunk_all_documents(docs_dir)
    print(f"  Found {len(chunks)} chunks from documents")

    if not chunks:
        print("  No documents found to index.")
        return 0

    client = get_chroma_client()

    # Delete existing collection if it exists
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass

    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"description": "PrimeEV Motors factory knowledge base"},
    )

    # Batch upsert
    batch_size = 100
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        ids = [f"chunk-{i + j}" for j in range(len(batch))]
        documents = [c.text for c in batch]
        metadatas = [
            {k: v for k, v in c.metadata.items() if v is not None}
            for c in batch
        ]

        collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
        )

    print(f"  Indexed {len(chunks)} chunks into ChromaDB collection '{COLLECTION_NAME}'")
    return len(chunks)


def search(
    query: str,
    doc_type: str | None = None,
    station_id: str | None = None,
    n_results: int = 5,
) -> list[dict]:
    """Search the RAG corpus. Returns list of {text, metadata, distance}."""
    client = get_chroma_client()

    try:
        collection = client.get_collection(COLLECTION_NAME)
    except Exception:
        return []

    conditions = []
    if doc_type:
        conditions.append({"doc_type": {"$eq": doc_type}})
    if station_id:
        conditions.append({"station_id": {"$eq": station_id}})

    if len(conditions) == 0:
        where_filter = None
    elif len(conditions) == 1:
        where_filter = conditions[0]
    else:
        where_filter = {"$and": conditions}

    results = collection.query(
        query_texts=[query],
        n_results=n_results,
        where=where_filter,
    )

    output = []
    for i in range(len(results["ids"][0])):
        output.append({
            "text": results["documents"][0][i],
            "metadata": results["metadatas"][0][i],
            "distance": results["distances"][0][i] if results.get("distances") else None,
        })

    return output


def search_sops(query: str, station_id: str | None = None, n_results: int = 3) -> list[dict]:
    """Search the RAG corpus for SOP documents, optionally scoped to a station."""
    return search(query, doc_type="sop", station_id=station_id, n_results=n_results)


def search_manuals(query: str, n_results: int = 3) -> list[dict]:
    """Search the RAG corpus for equipment or process manual documents."""
    return search(query, doc_type="manual", n_results=n_results)


def search_specs(query: str, n_results: int = 3) -> list[dict]:
    """Search the RAG corpus for process or product specification documents."""
    return search(query, doc_type="spec", n_results=n_results)


def search_troubleshooting(query: str, station_id: str | None = None, n_results: int = 5) -> list[dict]:
    """Search the troubleshooting knowledge base, optionally scoped to a station."""
    return search(query, doc_type="troubleshooting", station_id=station_id, n_results=n_results)


def search_fmea(query: str, n_results: int = 3) -> list[dict]:
    """Search FMEA documents for failure modes and their effects."""
    return search(query, doc_type="fmea", n_results=n_results)


def search_case_studies(query: str, n_results: int = 3) -> list[dict]:
    """Search historical case study documents for past incidents and resolutions."""
    return search(query, doc_type="case_study", n_results=n_results)
