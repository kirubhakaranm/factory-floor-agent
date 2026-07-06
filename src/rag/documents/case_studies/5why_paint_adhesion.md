# 5-Why Analysis: Paint Adhesion Failure on PE-SV200 Roof Panel

**Date:** 2025-09-18 | **Analyst:** Quality Engineering  
**Station:** PNT-01-ECT, PNT-02-PRM | **Affected:** PE-SV200 (SUV only)

## Problem Statement
13 PE-SV200 vehicles failed paint adhesion crosshatch test (ASTM D3359) at final inspection. Primer delaminated from e-coat on roof panel. No PE-SD100 or PE-CP300 vehicles affected.

## 5-Why Analysis

**Why 1: Why did the primer delaminate from the e-coat?**
→ Adhesion test showed 1B rating (poor) instead of required 4B. The primer did not bond to the e-coat surface on the roof panel.

**Why 2: Why didn't the primer bond to the e-coat on the roof?**
→ E-coat surface was contaminated with silicone residue, preventing proper intercoat adhesion. FTIR analysis confirmed dimethylpolysiloxane on e-coat surface.

**Why 3: Why was there silicone contamination on the e-coat surface?**
→ The PE-SV200 roof panel has an optional panoramic sunroof with adhesive-bonded reinforcement bracket. The adhesive used (PU-bond 440) contains a silicone release agent on the backing tape. Residue transferred to the adjacent roof surface during body shop handling.

**Why 4: Why did the silicone transfer to the adjacent surface?**
→ The adhesive tape backing was peeled in the body shop and placed on the roof panel surface temporarily while the operator positioned the bracket. This was not in the work instruction — it was a workaround the operator developed because there was no designated waste bin within reach.

**Why 5: Why was there no waste bin within reach?**
→ The workstation layout was designed before the panoramic sunroof option was added. The waste bin location was never updated for the new process step.

## Root Cause
Workstation layout did not accommodate the panoramic sunroof adhesive process, leading operators to develop an unapproved workaround that contaminated the roof surface with silicone.

## Corrective Actions
1. Added waste bin at operator's immediate reach for adhesive backing
2. Updated work instruction to specify: backing tape must be placed directly into waste bin, never on vehicle surface
3. Reworked 13 vehicles: sand, re-prime, re-basecoat, re-clearcoat (cost: $15,600)

## Preventive Actions
1. Silicone contamination check (water break test) added before primer application for SV200
2. Workstation layout review required for all new model/option introductions
3. Operator re-training on contamination risks

## PDCA Link
- This issue led to PDCA-2025-012: Workstation Layout Review Process for New Options
