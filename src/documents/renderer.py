"""PDF renderer — renders document models to PDF via Jinja2 HTML + weasyprint."""

import logging
from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from src.documents.models import (
    DocumentMeta,
    DocumentType,
    EightDReport,
    IncidentReport,
    MaintenanceNotice,
    NcrReport,
    PdcaRecord,
    WorkOrderDoc,
)

logger = logging.getLogger("primeev.documents.renderer")

TEMPLATES_DIR = Path(__file__).parent / "templates"
OUTPUT_DIR = Path(__file__).parent / "generated"

_jinja_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=True,
)

TEMPLATE_MAP = {
    DocumentType.EIGHT_D: "8d_report.html",
    DocumentType.NCR: "ncr_report.html",
    DocumentType.WORK_ORDER: "work_order.html",
    DocumentType.INCIDENT_REPORT: "incident_report.html",
    DocumentType.PDCA_RECORD: "pdca_record.html",
    DocumentType.MAINTENANCE_NOTICE: "maintenance_notice.html",
}


def render_html(doc_type: DocumentType, meta: DocumentMeta, doc: object) -> str:
    """Render a document to HTML string."""
    template_name = TEMPLATE_MAP[doc_type]
    template = _jinja_env.get_template(template_name)
    return template.render(meta=meta, doc=doc)


def render_pdf(doc_type: DocumentType, meta: DocumentMeta, doc: object) -> Path:
    """Render a document to PDF file. Returns path to generated PDF.

    Falls back to HTML-only if weasyprint is not available.
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    html_content = render_html(doc_type, meta, doc)
    filename_base = f"{meta.doc_id}_{meta.created_at.strftime('%Y%m%d_%H%M%S')}"

    # Try weasyprint for PDF
    try:
        from weasyprint import HTML

        pdf_path = OUTPUT_DIR / f"{filename_base}.pdf"
        HTML(string=html_content, base_url=str(TEMPLATES_DIR)).write_pdf(str(pdf_path))
        meta.pdf_path = str(pdf_path)
        logger.info("PDF generated: %s", pdf_path)
        return pdf_path
    except ImportError:
        # Fallback: save as HTML (weasyprint requires system libs)
        html_path = OUTPUT_DIR / f"{filename_base}.html"
        html_path.write_text(html_content, encoding="utf-8")
        meta.pdf_path = str(html_path)
        logger.warning("weasyprint not available — saved as HTML: %s", html_path)
        return html_path


def generate_doc_id(doc_type: DocumentType) -> str:
    """Generate a unique document ID."""
    now = datetime.now()
    prefix = {
        DocumentType.EIGHT_D: "8D",
        DocumentType.NCR: "NCR",
        DocumentType.WORK_ORDER: "WO",
        DocumentType.INCIDENT_REPORT: "IR",
        DocumentType.PDCA_RECORD: "PDCA",
        DocumentType.MAINTENANCE_NOTICE: "MN",
    }[doc_type]
    return f"{prefix}-{now.strftime('%y%m%d')}-{now.strftime('%H%M%S')}"
