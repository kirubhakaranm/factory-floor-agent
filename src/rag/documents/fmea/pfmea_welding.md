# Process FMEA: Welding (Stage WLD)

**PFMEA ID:** PFMEA-WLD-001 | **Revision:** 1.5 | **Date:** 2025-09-01  
**Process Owner:** Welding Engineering | **Cross-functional team:** Quality, Maintenance, Production

## Scope

All welding operations: Underbody (WLD-01-UBD), Side Panel (WLD-02-SDP), Roof/Closure (WLD-03-RCL)

## FMEA Table

| ID | Process Step | Potential Failure Mode | Potential Effect | SEV | Potential Cause | OCC | Current Controls | DET | RPN | Recommended Action |
|----|-------------|----------------------|------------------|-----|-----------------|-----|------------------|-----|-----|-------------------|
| WLD-001 | Resistance spot weld — WLD-01-UBD | Incomplete fusion | Structural weld joint failure, potential field safety issue — body integrity compromised | 9 | Weld current too low, insufficient electrode force, contaminated surface, electrode wear | 4 | 100% ultrasonic inspection on structural nodes, Cpk monitoring on nugget_diameter, peel test each shift | 4 | 144 | Increase weld current setpoint, implement real-time nugget formation monitoring; adjust weld schedule when Cpk < 1.33 |
| WLD-002 | Resistance spot weld — WLD-01-UBD | Porosity / voids in weld | Reduced joint strength, fatigue crack initiation under load | 7 | Moisture on surface, coated steel off-spec, weld time too short, electrode contamination | 4 | SPC on nugget_diameter, periodic peel test, receiving inspection of coated steel | 5 | 140 | Preheat protocol for coated steel, increase squeeze time 5 cycles, electrode cap change frequency review |
| WLD-003 | Resistance spot weld — all WLD | Weld spatter | Cosmetic defect on body surface, potential short circuit if in electrical area | 4 | Weld current too high, electrode force too low, flash between sheets | 6 | Visual inspection 100% at station exit, spatter shield maintenance | 5 | 120 | Reduce weld current 200A if spatter rate >3%, verify electrode force within spec; add shunt distance check |
| WLD-004 | Resistance spot weld — WLD-01-UBD | Burn-through | Hole in panel, scrap, structural gap | 7 | Weld current too high, panel thickness below spec, electrode tip worn flat | 3 | First-piece inspection, thickness measurement at incoming, electrode life tracking | 4 | 84 | Enforce electrode replacement at 3,000 welds max; add material thickness check at infeed |
| WLD-005 | Fixture locating — all WLD | Weld misalignment (>2mm) | Assembly fitment issue downstream, flange gap at hem | 7 | Fixture wear, locating pin bent, panel spring-back variation | 4 | Coordinate measurement every 50 bodies, fixture audit each shift | 3 | 84 | Implement in-station vision system for joint location verification; tighten fixture audit to every 25 bodies |
| WLD-006 | Resistance spot weld — WLD-02-SDP | Weld crack (hot crack) | Panel structural failure, visible crack after E-coat | 9 | High carbon equivalent steel, rapid quench, inter-pass temperature too low | 2 | Metallurgical review at material approval, weld schedule qualification per material grade | 4 | 72 | Require weld schedule requalification if steel supplier or grade changes |
| WLD-007 | Resistance spot weld — WLD-02-SDP | Undercut | Reduced cross-section at weld toe, fatigue initiation | 6 | Weld current too high for sheet thickness, wrong electrode tip geometry | 3 | Visual inspection first piece + every 100 welds, Cpk on nugget_diameter | 4 | 72 | Verify electrode tip geometry matches weld schedule spec; review current setpoint for panel combination |
| WLD-008 | Resistance spot weld — WLD-03-RCL | Blow hole / expulsion | Void at nugget surface, joint strength loss | 6 | Excessive weld current, contamination between sheets, electrode force too low | 4 | Visual inspection at station exit, peel test each shift | 4 | 96 | Add pre-weld surface cleaning step for roof panel; monitor electrode force with load cell |
| WLD-009 | Electrode maintenance — all WLD | Electrode tip wear beyond limit | Reduced nugget diameter, increased porosity and spatter | 8 | Exceeding 3,000-weld replacement interval, skipping dressing frequency | 3 | Electrode life counter in weld controller, dressing every 150–200 welds | 3 | 72 | Interlock weld controller to prevent production if electrode life counter exceeds limit |
| WLD-010 | Material handling — all WLD | Panel surface contamination (oil, scale) | Poor weld quality, porosity, adhesion failure in downstream painting | 6 | Excess stamping lubricant, handling damage, storage contamination | 4 | Visual check at load station, receiving inspection of stamped panels | 5 | 120 | Add weld flange wiping station before WLD-01-UBD; track contamination-related defects by supplier lot |

## High RPN Items (>120) — Action Required

1. **WLD-001 (RPN 144)**: Incomplete fusion at WLD-01-UBD — highest safety risk (SEV=9, structural underbody joint). Adjust weld current/electrode force when Cpk < 1.33. **Parameter change implemented 2026-03-01 — monitor for 30 days.**
2. **WLD-002 (RPN 140)**: Porosity / voids — preheat protocol and squeeze time adjustment required
3. **WLD-003 (RPN 120)**: Weld spatter — reduce current 200A if rate exceeds 3%
4. **WLD-010 (RPN 120)**: Surface contamination — add wiping station before WLD-01-UBD

## Notes on Parameter Change (2026-03-01)

Weld schedule on WLD-01-UBD was adjusted to address WLD-001 (incomplete fusion):
- Weld current increased from 8,200A nominal to 8,500A nominal
- Electrode force increased from 370 daN to 400 daN
- Squeeze time increased from 45 cycles to 50 cycles

Expected outcome: reduction in incomplete fusion rate, improvement in nugget_diameter Cpk above 1.33.  
Side effect to monitor: potential increase in weld spatter (WLD-003) at higher current — watch spatter rate.
