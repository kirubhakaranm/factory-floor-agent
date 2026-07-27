# SOP-ASM-02: Interior and Wiring Installation

**Station:** ASM-02-INT | **Machine:** ASM-02-INT-RBT01 (UR10e cobot)  
**Revision:** 2.6 | **Effective:** 2025-10-15

## Purpose

Installation of dashboard, center console, seats, headliner, door trim, and main wiring harness.

## Installation Sequence

1. **Main wiring harness** — route from engine bay through firewall, along floor tunnel, to rear
2. **Dashboard assembly** — pre-built sub-assembly, installed as unit with cobot assist
3. **Center console** — manual installation, 6 fasteners + 3 electrical connectors
4. **HVAC unit** — pre-installed in dashboard sub-assembly, connect refrigerant lines
5. **Headliner** — manual, clip retention (12 clips), sun visor and dome light connection
6. **Door trim panels** — 4 doors, clip retention + 2 screws each, connect window/lock harness
7. **Seats** — 4 mounting bolts per seat (M10, 45 Nm), seat belt anchor bolt (M12, 50 Nm)
8. **Steering column** — 4 bolts, connect clock spring, ADAS connector, tilt/telescope motor

## Quality Focus Areas

- **Squeak and Rattle (S&R)**: all clips must be fully seated — partially seated clips are the #1 warranty complaint
- **Panel gaps**: door trim to door panel gap: 2.0 ±0.5mm uniform
- **Wiring routing**: no pinch points, no sharp bends (<25mm radius), all connectors clicked and lock tabs verified
- **Seat belt anchor**: safety-critical torque — 100% electronic torque recording per VIN

## Troubleshooting

| Symptom | Likely Cause | Action |
|---------|-------------|--------|
| Clip broken during install | Wrong clip type, angle of insertion, panel warped | Replace clip, verify part number, inspect panel for warp |
| Panel gap uneven | Mounting point shifted, trim panel distorted, body variation | Adjust mounting, replace trim if distorted, check body dimensions |
| Squeak/rattle detected | Loose clip, foam pad missing, wire harness touching panel | Find source with stethoscope, secure clip, add anti-squeak foam |
| Wiring connector won't seat | Bent terminal, wrong connector, contamination | Inspect terminals, verify part number, clean and re-attempt |
| Dashboard fitment issue | Body variation, dashboard sub-assembly out of spec | Measure body reference points, check dashboard dimensions |

## Cycle Time Breakdown

| Operation | Time | Notes |
|-----------|------|-------|
| Wiring harness | 90 sec | Longest single operation |
| Dashboard | 45 sec | Cobot-assisted lift and position |
| Center console | 30 sec | Manual |
| Headliner | 30 sec | Manual |
| Door trim (×4) | 20 sec each | 80 sec total |
| Seats (×4-5) | 15 sec each | 60-75 sec total |
| Total | ~240 sec | Station cycle time target |

## Model Changeover Procedure — PE-SD100 ↔ PE-SV200

**Trigger:** Any switch between Sedan (PE-SD100) and SUV (PE-SV200) on Assembly Line  
**Minimum changeover time target:** 45 minutes  
**Required sign-offs:** Production Supervisor + Quality Engineer

### Pre-Changeover Checklist

1. Confirm current model batch is complete — no WIP units in station
2. Notify downstream stations (ASM-03-FNL, QAT-01-ALN) of model switch
3. Print new traveler and BOM from MES for incoming model

### Tooling and Fixture Swap

| Item | PE-SD100 | PE-SV200 | Action |
|------|----------|----------|--------|
| Seat mounting fixture | 4-seat config | 5-seat config (3rd row) | Swap fixture, verify torque spec |
| Dashboard sub-assembly | Sedan dash | SUV dash with panoramic roof controls | Change sub-assembly cart |
| Wiring harness routing guide | Standard | Extended (SUV longer body) | Swap routing template |
| Headliner clip template | 12-clip | 14-clip (panoramic roof model) | Swap template |

### BOM Changeover Steps

1. In MES: close current model production order, open new model order
2. Scan new BOM QR code at station kiosk — verify model ID displayed matches body on line
3. Pull correct sub-assembly kits from supermarket (dashboard, seats, door trim — model-specific)
4. Return unused previous-model components to supermarket — do not mix model parts

### First Article Inspection

1. Build first unit of new model at 50% cycle time (do not rush)
2. Perform full dimensional check per new model control plan
3. Verify seat belt anchor torque recorded under correct VIN
4. Quality Engineer sign-off required before releasing line to full production speed

### Changeover Sign-Off

- Production Supervisor: confirms tooling swap complete and BOM updated in MES
- Quality Engineer: confirms first article inspection passed
- Document changeover in shift log with start time, end time, and first-article VIN
