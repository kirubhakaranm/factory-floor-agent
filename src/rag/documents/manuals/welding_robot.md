# Fanuc R-2000iC/210F Welding Robot — Maintenance Manual

**Applies to:** WLD-01-UBD-RBT01, WLD-01-UBD-RBT02, WLD-02-SDP-RBT01, WLD-03-RCL-RBT01  
**Model:** Fanuc R-2000iC/210F | **Payload:** 210 kg | **Reach:** 2650 mm  
**Revision:** 2.1 | **Effective:** 2025-06-01

## Vibration Limits and Diagnostics

### Normal Operating Ranges

| Joint | Normal Vibration | Warning Level | Alarm Level |
|-------|-----------------|---------------|-------------|
| J1 (rotation) | < 1.0 mm/s | 1.0–2.0 mm/s | > 2.0 mm/s |
| J2 (lower arm) | < 1.0 mm/s | 1.0–2.0 mm/s | > 2.0 mm/s |
| J3 (upper arm) | < 0.8 mm/s | 0.8–1.5 mm/s | > 1.5 mm/s |
| Overall (RMS) | < 1.0 mm/s | 1.0–2.0 mm/s | > 2.0 mm/s |

**Any sustained reading above 2.0 mm/s requires immediate inspection.** Intermittent peaks above 2.0 mm/s indicate early-stage reducer wear or bearing degradation and require inspection within 72 hours.

### Vibration Causes by Pattern

| Pattern | Likely Cause |
|---------|-------------|
| Gradual increase over weeks | Reducer gear wear — grease contamination or lubrication breakdown |
| Sudden spike, then normal | Loose mechanical connection — check joint bolts and cable harness |
| High at one joint only | Bearing failure in that joint motor |
| High at all joints | Base mounting looseness or structural resonance |

## Reducer Gear Inspection Procedure

**Trigger:** Vibration sustained above 1.5 mm/s, or after 8,000 operating hours, or after any collision event.

### Pre-Inspection

1. Perform LOTO on robot controller cabinet (R-30iB controller) — lock main breaker
2. Manually release brakes using brake release switch on teach pendant (only with controller powered off and LOTO applied)
3. Support robot arm with floor jack to prevent drop when brakes released

### Backlash Measurement

1. Lock all joints except the joint under test
2. Apply 5 Nm torque at the joint flange using torque wrench
3. Measure angular deflection with dial indicator mounted at 300 mm radius
4. Calculate backlash: `Backlash (arcmin) = deflection_mm / (300 mm × π/10800)`

**Acceptance criteria:**

| Joint | New | Acceptable | Replace Required |
|-------|-----|------------|-----------------|
| J1 | 1–3 arcmin | < 8 arcmin | ≥ 8 arcmin |
| J2 | 1–3 arcmin | < 8 arcmin | ≥ 8 arcmin |
| J3 | 1–3 arcmin | < 6 arcmin | ≥ 6 arcmin |

### Grease Inspection

1. Remove reducer drain plug — collect 10 mL sample of grease
2. Inspect for: metallic particles (grey/silver sheen), discoloration (black = overheating), water contamination (white emulsion)
3. Use Ferrograph analysis if metallic particles visible
4. Replace grease if contaminated — use Fanuc A98L-0040-0174 (Molywhite RE No. 00) only

### Reducer Replacement Decision

Replace reducer if any of the following:
- Backlash exceeds acceptance criteria above
- Metallic particles visible in grease sample
- Vibration does not decrease after grease replacement
- Noise change: grinding or clicking not present before

**Replacement part:** Fanuc A97L-0218-0176 (J1/J2), A97L-0218-0177 (J3)  
**Lead time:** 3–5 weeks from Fanuc authorized distributor — order immediately upon decision to replace

## Preventive Maintenance Schedule

| Interval | Task |
|----------|------|
| Every 3 months (750 hrs) | Grease all joints (Molywhite RE No. 00), inspect cable harness, check tool flange bolts |
| Every 6 months (1,500 hrs) | Backlash check on J1-J3, inspect reducer seals for leaks, verify brake holding torque |
| Every 2 years (4,000 hrs) | Full reducer grease replacement, wrist unit inspection, battery replacement (J4-J6 encoders) |
| Every 4 years (8,000 hrs) | Reducer overhaul or replacement evaluation, full cable harness replacement |

## Fault Codes

| Code | Description | Action |
|------|-------------|--------|
| SRVO-062 | Brake alarm | Check brake power supply, replace brake unit if voltage OK |
| SRVO-023 | Stop error excess | Reducer backlash exceeds limit — inspect and replace |
| SRVO-043 | Disturbance torque excess | Collision or mechanical binding — inspect robot path and tooling |
| INTP-127 | Vibration detected | Run vibration diagnosis from Fanuc ROBOGUIDE, inspect reducers |

## Emergency Procedures

**If robot vibrates excessively during production:**
1. Press E-STOP immediately
2. Do NOT attempt to continue cycle — excess vibration can cause weld gun misalignment and tooling damage
3. Run vibration diagnostic: `MENUS → System → Master/Cal → Vibration Check`
4. If vibration confirmed above alarm level, tag robot OUT OF SERVICE and contact maintenance
5. Notify production supervisor — activate contingency routing to backup robot if available
