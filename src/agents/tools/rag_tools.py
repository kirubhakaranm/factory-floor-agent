"""RAG search tools — search SOPs, manuals, specs, troubleshooting DB, FMEAs, case studies."""

from src.rag.embedder import (
    search_case_studies,
    search_fmea,
    search_manuals,
    search_sops,
    search_specs,
    search_troubleshooting,
)


def search_sop(query: str, station_id: str | None = None) -> list[dict]:
    """Search Standard Operating Procedures for relevant guidance.

    Use this to find operating parameters, procedures, safety requirements,
    and troubleshooting steps for a specific station or process.

    Args:
        query: Natural language search query (e.g., 'hydraulic press overheating procedure')
        station_id: Filter by station (optional, e.g., 'STP-01-PRS')

    Returns:
        Relevant SOP sections with text, source document, and section header
    """
    return search_sops(query, station_id=station_id, n_results=3)


def search_equipment_manual(query: str) -> list[dict]:
    """Search equipment manuals for machine specifications, maintenance schedules, and failure modes.

    Use this to find equipment specs, spare parts lists, maintenance intervals,
    and known failure modes for specific machines.

    Args:
        query: Search query (e.g., 'hydraulic pump replacement interval')

    Returns:
        Relevant manual sections with text, source, and section
    """
    return search_manuals(query, n_results=3)


def search_specification(query: str) -> list[dict]:
    """Search process and product specifications for tolerances, material requirements, and SPC parameters.

    Args:
        query: Search query (e.g., 'steel sheet thickness tolerance')

    Returns:
        Relevant specification sections
    """
    return search_specs(query, n_results=3)


def search_past_issues(query: str, station_id: str | None = None) -> list[dict]:
    """Search the troubleshooting database for past quality issues, failures, and their root causes.

    This database contains historical incident reports with root cause analysis,
    corrective actions, and lessons learned. Essential for diagnosing recurring problems.

    Args:
        query: Search query (e.g., 'weld porosity zinc coating')
        station_id: Filter by station (optional)

    Returns:
        Relevant past issues with symptoms, root cause, actions taken
    """
    return search_troubleshooting(query, station_id=station_id, n_results=5)


def search_fmea_risks(query: str) -> list[dict]:
    """Search DFMEA and PFMEA documents for known failure modes, risk priority numbers (RPN), and recommended actions.

    Args:
        query: Search query (e.g., 'stamping panel cracking risk')

    Returns:
        FMEA entries with failure mode, effect, severity, occurrence, detection, RPN
    """
    return search_fmea(query, n_results=3)


def search_case_study(query: str) -> list[dict]:
    """Search past case studies including 5-Why analyses, fishbone diagrams, DMAIC studies, and 8D reports.

    Args:
        query: Search query (e.g., 'paint adhesion failure analysis')

    Returns:
        Relevant case studies with investigation methodology and findings
    """
    return search_case_studies(query, n_results=3)
