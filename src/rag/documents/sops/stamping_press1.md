# SOP-STP-01: Hydraulic Press Operation — Press 1

**Station:** STP-01-PRS | **Machine:** STP-01-PRS-HYP01 / HYP02  
**Revision:** 3.2 | **Effective:** 2025-11-01  
**Owner:** Stamping Engineering | **Approved by:** Plant Manager

## Purpose

Defines the standard operating procedure for operating the Schuler TwinServo 2800 hydraulic presses at Station STP-01-PRS for chassis frame and body panel forming operations.

## Safety Requirements

- Lockout/Tagout (LOTO) must be performed before any die change or maintenance entry
- Two-hand anti-tie-down controls must be engaged before press cycle
- Light curtains must be verified operational at start of each shift
- Hearing protection required within 15m radius during press operation
- Maximum press force: 2800 tons — never override force limiters

## Startup Procedure

1. Verify LOTO has been released and all guards are in place
2. Check hydraulic fluid level — must be between MIN and MAX indicators on reservoir sight glass
3. Start hydraulic power unit — allow 5 minutes warm-up until oil temperature reaches 35°C minimum
4. Verify hydraulic pressure reaches 220 ± 10 bar on main gauge
5. Run three empty cycles to confirm ram travel and speed
6. Load first blank and run single stroke — inspect formed part against master sample
7. Record first-piece inspection results in quality log

## Operating Parameters

| Parameter | Nominal | Lower Limit | Upper Limit |
|-----------|---------|-------------|-------------|
| Hydraulic pressure | 220 bar | 200 bar | 240 bar |
| Oil temperature | 45°C | 35°C | 65°C |
| Ram speed (approach) | 250 mm/s | 200 mm/s | 300 mm/s |
| Ram speed (forming) | 15 mm/s | 10 mm/s | 25 mm/s |
| Cushion pressure | 80 bar | 60 bar | 100 bar |
| Cycle time | 45 sec | 38 sec | 55 sec |

## Material Handling

- Steel blanks must be oriented with rolling direction markings facing operator
- Apply stamping lubricant (Fuchs Renoform MZAN 58) to both surfaces before loading
- Inspect blanks for surface defects, rust, and dimensional conformance before forming
- Reject blanks with edge burrs exceeding 0.3mm

## Quality Checks

- First-piece inspection: full dimensional check against control plan
- Every 50th part: spot-check critical dimensions (panel thickness, draw depth, surface roughness)
- Continuous monitoring: press force vs. stroke curve on HMI — flag deviations >5%
- End of shift: last-piece inspection and record results

## Troubleshooting

| Symptom | Likely Cause | Action |
|---------|-------------|--------|
| Hydraulic pressure drops below 200 bar | Pump wear, relief valve leak, low fluid | Stop production, check pump output, inspect relief valve, verify fluid level |
| Oil temperature exceeds 65°C | Cooler fan failure, high ambient, excessive cycling | Reduce cycle rate, check cooler fans, verify coolant flow |
| Part shows cracking | Die wear, insufficient lubrication, material issue | Stop, inspect die surfaces, check lubricant application, verify material cert |
| Part shows wrinkling | Cushion pressure too low, blank holder gap | Adjust cushion pressure, check blank holder clearance, re-shim if needed |
| Excessive vibration | Loose bolting, unbalanced ram, bearing wear | Stop and inspect mounting bolts, check ram guides, measure vibration levels |

## Shutdown Procedure

1. Complete current cycle and remove finished part
2. Return ram to top dead center
3. Turn selector switch to OFF
4. If end of shift: leave hydraulic unit running for next shift; if extended shutdown: power down hydraulic unit after oil cools below 40°C
5. Clean die surfaces and apply rust preventive if shutdown exceeds 8 hours
6. Complete shift production log

## Lockout/Tagout (LOTO) Procedure — Hydraulic System

**Authority:** OSHA 29 CFR 1910.147 | **Applies to:** All maintenance and die change activities on STP-01-PRS-HYP01 / HYP02

### Energy Isolation Points

| Isolation Point | Location | Lock Type |
|----------------|----------|-----------|
| Main electrical disconnect (480V) | MCC panel E-STP01, breaker H1 | Hasp + personal lock |
| Hydraulic power unit circuit breaker | HPU control cabinet, CB-HYP-01 | Hasp + personal lock |
| Pneumatic supply valve | Air manifold, left side of press base | Red ball valve — lock open position |
| Stored hydraulic pressure (accumulator) | Accumulator bleed valve AV-001 | Bleed to zero, verify gauge reads 0 bar |

### LOTO Application Steps

1. Notify operator and supervisor — confirm press is in ready-to-service state
2. Return ram to top dead center (TDC) and complete current cycle
3. Press E-STOP and turn selector switch to OFF
4. Open and lock main electrical disconnect at MCC panel (breaker H1) — apply personal lock and tag
5. Open and lock HPU circuit breaker CB-HYP-01 — apply personal lock and tag
6. Close pneumatic supply ball valve at air manifold — apply personal lock
7. Open accumulator bleed valve AV-001 — wait for pressure gauge to drop to 0 bar (approx 2 minutes)
8. **Verify zero energy state:** attempt to start HPU — confirm no response; check that all hydraulic gauges read 0 bar
9. Begin maintenance work only after zero energy state is confirmed

### LOTO Release Steps

1. Remove all tools, materials, and personnel from press area
2. Close accumulator bleed valve AV-001
3. Open pneumatic supply valve — remove pneumatic lock
4. Close and unlock HPU circuit breaker CB-HYP-01 — remove personal lock and tag
5. Close and unlock main electrical disconnect — remove personal lock and tag
6. Verify all guards are reinstalled and light curtains are operational
7. Perform press startup procedure (see Startup Procedure section above)

## Preventive Maintenance Schedule

| Interval | Tasks | Parts Required |
|----------|-------|----------------|
| Every shift (8 hrs) | Check hydraulic fluid level at sight glass; inspect for visible leaks; verify pressure gauge reads 220 ± 10 bar at startup | — |
| Weekly (every 250 hrs) | Inspect hydraulic hoses and fittings for wear/seepage; check ram guide lubrication; verify light curtain alignment | Grease (Fuchs Renolin MR 15) |
| Every 500 operating hours (~3 weeks at full production) | Replace hydraulic filter element; change hydraulic fluid (20L Fuchs Renolin ZAF 46); replace O-ring set; inspect cylinder seals; check accumulator pre-charge pressure | SP-HYP-003 (cylinder seal kit), SP-HYP-005 (filter element), hydraulic fluid 20L |
| Every 2,000 operating hours (~3 months) | Full hydraulic pump inspection; pressure relief valve test and calibration; check all accumulator bladders; inspect ram guides for wear; torque all structural bolts | SP-HYP-001 (pump assembly if worn), SP-HYP-002 (relief valve if out of spec) |
| Annually | Full hydraulic system flush; replace all seals and O-rings; inspect cylinder bore; recalibrate all pressure and temperature sensors | Full seal kit, sensor calibration standards |

**Overdue criteria:** If any scheduled interval is exceeded by more than 20%, raise a priority PM work order immediately. Machine may continue operation until the 500-hour PM is overdue by >5 days, after which production must stop until PM is completed.

## Emergency Stop

- Press E-STOP button on operator panel or any of 4 satellite E-STOP locations
- Ram will halt immediately via pilot-operated check valves
- Do NOT attempt to restart until root cause is identified and cleared
- Report all E-STOP events to shift supervisor and log in incident system
