"""Document serving route — returns RAG source files for citation links."""

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse

router = APIRouter(prefix="/api", tags=["docs"])

_DOCS_ROOT = Path(__file__).parent.parent.parent.parent / "src" / "rag" / "documents"


@router.get("/docs/{doc_path:path}", response_class=PlainTextResponse)
async def get_doc(doc_path: str) -> str:
    """Serve a RAG source document by its relative path.

    Used by the citation panel to open source documents in a new browser tab.
    Path is validated to stay within src/rag/documents/ to prevent traversal.
    """
    # Resolve and validate — must stay inside _DOCS_ROOT
    try:
        target = (_DOCS_ROOT / doc_path).resolve()
        _DOCS_ROOT.resolve()  # ensure root itself is valid
        if not str(target).startswith(str(_DOCS_ROOT.resolve())):
            raise HTTPException(status_code=403, detail="Access denied")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid path")

    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail=f"Document not found: {doc_path}")

    return target.read_text(encoding="utf-8")
