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

## Emergency Stop

- Press E-STOP button on operator panel or any of 4 satellite E-STOP locations
- Ram will halt immediately via pilot-operated check valves
- Do NOT attempt to restart until root cause is identified and cleared
- Report all E-STOP events to shift supervisor and log in incident system
