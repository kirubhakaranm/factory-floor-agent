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
    """[ACTION]: Search Standard Operating Procedures for operating parameters, procedures, and safety requirements. [TARGET]: ChromaDB SOP corpus (~15 documents, one per station).

    [INPUT PREREQUISITE]: query must be a natural language description of what you're looking for.
    station_id must be a valid station code if provided (e.g. 'STP-01-PRS').
    Use this when you need procedure steps, operating limits, or sign-off requirements.

    [OUTPUT GUARANTEE]: Returns up to 3 relevant SOP sections with: text, source document,
    section header. Sections contain the actual procedure text, not summaries.

    [NEGATIVE BOUNDARY]: Cannot search equipment manuals — use search_equipment_manual.
    Cannot search process or product specifications — use search_specification.
    Returns chunks, not the full SOP document; adjacent sections may be missing.

    Args:
        query: Natural language search query (e.g. 'hydraulic press overheating procedure')
        station_id: Filter by station (optional, e.g. 'STP-01-PRS')

    Returns:
        List of up to 3 relevant SOP section dicts.
    """
    return search_sops(query, station_id=station_id, n_results=3)


def search_equipment_manual(query: str) -> list[dict]:
    """[ACTION]: Search equipment manuals for machine specifications, maintenance schedules, and known failure modes. [TARGET]: ChromaDB manual corpus (~5 documents, one per machine type).

    [INPUT PREREQUISITE]: query should reference a specific machine type or symptom.
    Do not call this for process-level specs — use search_specification instead.

    [OUTPUT GUARANTEE]: Returns up to 3 relevant manual sections with: text, source, section.
    Sections may include: spec tables, maintenance intervals, spare parts lists, failure mode descriptions.

    [NEGATIVE BOUNDARY]: Cannot search SOPs — use search_sop. Cannot search troubleshooting DB —
    use search_past_issues. Manual content is static; does not reflect field modifications.

    Args:
        query: Search query (e.g. 'hydraulic pump replacement interval', 'servo drive alarm codes')

    Returns:
        List of up to 3 relevant manual section dicts.
    """
    return search_manuals(query, n_results=3)


def search_specification(query: str) -> list[dict]:
    """[ACTION]: Search process and product specifications for tolerances, material requirements, and SPC parameters. [TARGET]: ChromaDB specs corpus (5 process specs + 3 product specs).

    [INPUT PREREQUISITE]: query should reference a specific characteristic, material, or process
    parameter. Use this to retrieve engineering design intent before comparing against actual data.

    [OUTPUT GUARANTEE]: Returns up to 3 relevant specification sections with: text, source, section.
    May include: dimensional tolerances, GD&T callouts, material grades, SPC parameter targets.

    [NEGATIVE BOUNDARY]: Cannot search SOPs or manuals — use the appropriate tools for those.
    Returns specification text, not actual measurement results — use get_dimensional_results for that.

    Args:
        query: Search query (e.g. 'steel sheet thickness tolerance', 'weld nugget diameter spec')

    Returns:
        List of up to 3 relevant specification section dicts.
    """
    return search_specs(query, n_results=3)


def search_past_issues(query: str, station_id: str | None = None) -> list[dict]:
    """[ACTION]: Search the troubleshooting database for past quality issues, failures, and their root causes. [TARGET]: ChromaDB troubleshooting DB corpus (~40 historical incident records).

    [INPUT PREREQUISITE]: query should describe the symptom or defect type being investigated.
    station_id filters by station if provided. Essential for diagnosing recurring problems —
    check here before performing a full diagnosis from sensor data alone.

    [OUTPUT GUARANTEE]: Returns up to 5 relevant past issues with: text, source, section.
    Records include: symptom description, root cause identified, corrective actions taken,
    and lessons learned.

    [NEGATIVE BOUNDARY]: Returns historical incidents only — not live failure data.
    For current failures, use get_failure_history. For FMEA risk rankings, use search_fmea_risks.

    Args:
        query: Search query (e.g. 'weld porosity zinc coating', 'paint orange peel root cause')
        station_id: Filter by station (optional)

    Returns:
        List of up to 5 relevant past issue dicts.
    """
    return search_troubleshooting(query, station_id=station_id, n_results=5)


def search_fmea_risks(query: str) -> list[dict]:
    """[ACTION]: Search DFMEA and PFMEA documents for known failure modes, risk priority numbers (RPN), and recommended actions. [TARGET]: ChromaDB FMEA corpus (3 DFMEA + 5 PFMEA documents).

    [INPUT PREREQUISITE]: query should reference a specific process, component, or failure mode.
    DFMEA covers product design risks; PFMEA covers manufacturing process risks.

    [OUTPUT GUARANTEE]: Returns up to 3 relevant FMEA entries with: text, source, section.
    Entries include: failure mode, effect, severity (S), occurrence (O), detection (D), RPN = S×O×D,
    and recommended actions.

    [NEGATIVE BOUNDARY]: Cannot return historical failure occurrences — use get_failure_history.
    FMEA content is static design-phase risk documentation.

    Args:
        query: Search query (e.g. 'stamping panel cracking risk', 'battery connection failure mode')

    Returns:
        List of up to 3 relevant FMEA entry dicts.
    """
    return search_fmea(query, n_results=3)


def search_case_study(query: str) -> list[dict]:
    """[ACTION]: Search past case studies including 5-Why analyses, fishbone diagrams, DMAIC studies, and 8D reports. [TARGET]: ChromaDB case studies corpus (~5 documents).

    [INPUT PREREQUISITE]: query should describe the type of problem or investigation approach
    you're referencing. Use for precedent — "have we solved something similar before?"

    [OUTPUT GUARANTEE]: Returns up to 3 relevant case study sections with: text, source, section.
    Documents include investigation methodology, root cause narrative, and outcomes.

    [NEGATIVE BOUNDARY]: Returns historical case studies only — not templates for new investigations.
    For creating new 8D or PDCA documents, use action_tools.

    Args:
        query: Search query (e.g. 'paint adhesion failure analysis', 'weld defect DMAIC study')

    Returns:
        List of up to 3 relevant case study section dicts.
    """
    return search_case_studies(query, n_results=3)
