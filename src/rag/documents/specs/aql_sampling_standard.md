# AQL Sampling Standard — PrimeEV Motors Quality System

**Standard:** ANSI/ASQ Z1.4 (Attribute Sampling)  
**Applies to:** All incoming material, in-process, and finished goods sampling inspections  
**Owner:** Quality Engineering | **Revision:** 1.3 | **Effective:** 2025-01-01

## AQL Levels by Product Category

| Product / Process Category | AQL Level | Rationale |
|---------------------------|-----------|-----------|
| Safety-critical structural welds | 0.065 | Zero tolerance — weld failures cause vehicle safety risk |
| Body panel dimensional (critical dimensions) | 0.65 | High impact on fit and finish |
| Paint / surface finish | 1.0 | Customer-visible; aesthetic impact |
| Interior trim and assembly | 1.0 | Customer-visible |
| Powertrain assembly | 0.65 | Performance and reliability impact |
| Raw material incoming (steel, aluminum) | 1.0 | Material properties affect downstream quality |
| Consumables and fasteners | 2.5 | Lower criticality |

## Sampling Plan Table (ANSI/ASQ Z1.4, Normal Inspection, Level II)

| Lot Size | Sample Size Code | Sample Size | AQL 0.065 | AQL 0.65 | AQL 1.0 | AQL 2.5 |
|----------|-----------------|-------------|-----------|----------|---------|---------|
| 2–8 | A | 2 | — | — | — | 0/1 |
| 9–15 | B | 3 | — | — | — | 0/1 |
| 16–25 | C | 5 | — | — | 0/1 | 0/1 |
| 26–50 | D | 8 | — | — | 0/1 | 0/1 |
| 51–90 | E | 13 | — | 0/1 | 0/1 | 1/2 |
| 91–150 | F | 20 | — | 0/1 | 0/1 | 1/2 |
| 151–280 | G | 32 | 0/1 | 0/1 | **1/2** | 2/3 |
| 281–500 | H | 50 | 0/1 | 1/2 | 1/2 | 3/4 |
| 501–1200 | J | 80 | 0/1 | 1/2 | 2/3 | 5/6 |
| 1201–3200 | K | 125 | 0/1 | 2/3 | 3/4 | 7/8 |
| 3201–10000 | L | 200 | 1/2 | 3/4 | 5/6 | 10/11 |

**Accept/Reject notation:** Accept number / Reject number. Example: **1/2** = accept if defects ≤ 1, reject if defects ≥ 2.

`—` = use next larger sample size code.

## How to Use This Table

1. Determine lot size from receiving or production records
2. Identify the applicable AQL level from the product category table above
3. Find the row matching the lot size — read the sample size and accept/reject numbers
4. Count actual defects found in the sample
5. **If defects found ≥ reject number → REJECT the lot**
6. **If defects found ≤ accept number → ACCEPT the lot**

## Disposition of Rejected Lots

| Option | When to Use |
|--------|-------------|
| Return to Supplier (RTS) | Incoming material with confirmed supplier defect |
| 100% Screening | When defect rate is low and sorting is feasible; keep conforming parts |
| MRB (Material Review Board) | When parts may be usable with deviation; requires engineering sign-off |
| Scrap | When defects are safety-critical or sorting is not economical |

**Tightened Inspection** is triggered automatically when 2 out of 5 consecutive lots are rejected. Tightened inspection uses the next larger sample size code.

## Stamping Incoming Material — Specific Requirements

- Steel blanks (SUP-MTL01, SUP-MTL02): AQL 1.0, visual + dimensional inspection required
- Lot sizes for stamping blanks: typically 150–300 blanks per delivery
- Critical inspection points: edge condition, surface defects, thickness, temper designation
- Any lot with surface contamination, rust, or incorrect temper must be rejected regardless of AQL outcome
