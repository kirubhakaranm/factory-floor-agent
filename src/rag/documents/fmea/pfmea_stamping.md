# Process FMEA: Stamping (Stage STP)

**PFMEA ID:** PFMEA-STP-001 | **Revision:** 2.0 | **Date:** 2025-08-01  
**Process Owner:** Stamping Engineering | **Cross-functional team:** Quality, Maintenance, Production

## Scope
All stamping operations: Press 1 (STP-01-PRS), Press 2 (STP-02-PRS), Trim/Pierce (STP-03-TRM)

## FMEA Table

| ID | Process Step | Potential Failure Mode | Potential Effect | SEV | Potential Cause | OCC | Current Controls | DET | RPN | Recommended Action |
|----|-------------|----------------------|------------------|-----|-----------------|-----|------------------|-----|-----|-------------------|
| STP-001 | Blank loading | Wrong material loaded | Wrong thickness panel, assembly fit issues | 7 | Operator error, similar appearance of blanks | 3 | Material label scan, thickness sensor on infeed | 3 | 63 | Add vision system for material ID verification |
| STP-002 | Hydraulic forming | Panel cracking | Scrap, production delay | 8 | Die wear, insufficient lubrication, material hardness | 4 | Press force monitoring, first-piece inspection | 4 | 128 | Implement force-displacement curve monitoring with auto-stop |
| STP-003 | Hydraulic forming | Panel wrinkling | Rework, cosmetic defect | 6 | Cushion pressure too low, blank holder gap | 5 | Visual inspection every 50 parts | 5 | 150 | Add cushion pressure SPC monitoring, reduce inspection interval to 25 parts |
| STP-004 | Hydraulic forming | Excessive thinning | Structural weakness, field failure | 9 | Die radius too sharp, material stretch too high | 3 | FLD analysis at die design, periodic thickness measurement | 4 | 108 | Online thickness measurement with ultrasonic sensor |
| STP-005 | Hydraulic press | Hydraulic oil overheating | Press shutdown, production stop | 7 | Cooler failure, high ambient, excessive cycling | 4 | Temperature sensor with alarm at 65°C | 3 | 84 | Predictive monitoring of oil temperature trend — alert on rising gradient |
| STP-006 | Trim operation | Excessive burr (>0.3mm) | Cut hazard during assembly, quality reject | 7 | Dull trim steel, excessive clearance | 5 | Burr height measurement every 25 parts | 4 | 140 | Automated burr sensor on trim station, auto-stop at 0.25mm |
| STP-007 | Trim operation | Slug retention failure | Slug in die, next part damage | 8 | Worn spring stripper, oil on die, slug shape | 3 | Visual die inspection each shift | 5 | 120 | Add slug detection sensor (proximity sensor in die slug chute) |
| STP-008 | Pierce operation | Oversized hole | Loose fastener, assembly quality | 6 | Punch wear, clearance drift | 4 | Go/no-go gauge every 50 parts | 4 | 96 | Track punch stroke count, replace at 80% of life limit |
| STP-009 | Material handling | Surface scratch on blank | Cosmetic defect visible after paint | 5 | Conveyor damage, rough handling, debris | 4 | Visual inspection at load station | 6 | 120 | Install felt-lined conveyor guides, air blow debris removal |
| STP-010 | Press operation | Hydraulic pump failure | Major downtime (4+ hours) | 9 | Oil contamination, seal wear, overdue maintenance | 3 | Oil analysis every 500 hrs, PM schedule | 4 | 108 | Reduce oil analysis to 250 hrs (per ISSUE-2025-003), stock spare pump |

## High RPN Items (>120) — Action Required

1. **STP-003 (RPN 150)**: Panel wrinkling — add SPC monitoring on cushion pressure
2. **STP-006 (RPN 140)**: Excessive burr — install automated burr sensor
3. **STP-002 (RPN 128)**: Panel cracking — implement force-displacement curve monitoring
4. **STP-007 (RPN 120)**: Slug retention — add slug detection sensor
5. **STP-009 (RPN 120)**: Surface scratch — install felt-lined conveyor guides
