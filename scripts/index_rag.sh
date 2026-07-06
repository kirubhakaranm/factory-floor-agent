#!/bin/bash
set -euo pipefail

echo "=== PrimeEV Factory — RAG Indexing ==="

echo "1. Chunking documents..."
echo "2. Generating embeddings..."
echo "3. Upserting to ChromaDB..."

python -c "
from src.rag.embedder import index_all_documents
index_all_documents()
"

echo "=== RAG indexing complete! ==="
