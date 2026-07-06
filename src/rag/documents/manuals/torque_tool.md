# Equipment Manual: Electronic Torque Fastening System

**Used at:** ASM-01-PWR, ASM-02-INT, ASM-03-FNL  
**Controller:** Atlas Copco Power Focus 6000  
**Tools:** Tensor STB angle/torque nutrunners

## Specifications

| Parameter | Value |
|-----------|-------|
| Torque range | 5 - 200 Nm (model dependent) |
| Angle measurement | ±0.5° resolution |
| Torque accuracy | ±2% of reading |
| Speed | 100 - 1000 rpm (adjustable) |
| Communication | Ethernet/IP, PROFINET, Open Protocol |
| Traceability | 100% torque + angle data logged per VIN and bolt location |

## Fastening Strategy

All safety-critical fasteners use **torque + angle** monitoring:
1. Rundown at high speed to snug torque (typically 30% of final)
2. Final tightening at controlled speed
3. Verify torque within spec window
4. Verify angle within spec window (indicates correct bolt/clamp load)
5. Result: OK (green) or NOK (red) — NOK stops the line

## Critical Fastener Classes

| Class | Examples | Strategy |
|-------|----------|----------|
| Safety-critical (A) | Battery mount, seat belt anchor, suspension bolts | Torque + angle, 100% recorded, electronic verification |
| Structural (B) | Drive unit mount, subframe bolts | Torque monitored, 100% recorded |
| General (C) | Interior trim, non-structural covers | Torque only, sample verification |

## Maintenance Schedule

| Interval | Action |
|----------|--------|
| Daily | Verify torque accuracy with calibration joint (master transducer) |
| Weekly | Clean tool, inspect socket condition, check cable |
| Monthly | Full calibration against reference transducer |
| 6 months | Send to calibration lab for certified calibration (ISO 17025) |
| Annually | Replace motor brushes, inspect gearing |

## Common Issues

| Symptom | Likely Cause | Action |
|---------|-------------|--------|
| Torque scatter (high variation) | Worn socket, contaminated threads, inconsistent lubrication | Replace socket, clean bolt/nut threads, verify lubricant application |
| Angle reject (too high) | Stripped thread, cross-thread, soft joint | Inspect thread, replace bolt, check joint hardness |
| Angle reject (too low) | Pre-existing clamp, double-hit, hardened washer | Verify bolt is new, check torque strategy ramp |
| Communication fault | Cable damage, controller network issue | Check Ethernet cable, restart controller, verify IP settings |
| Tool overheat | Excessive duty cycle, blocked cooling vents | Allow cool-down, clean vents, reduce cycle rate |

## Torque Traceability

Every torque result is stored with:
- VIN
- Bolt location ID (e.g., "battery_mount_LF_01")
- Target torque and actual torque
- Target angle and actual angle
- Timestamp
- Tool serial number
- Operator badge ID
- Result (OK/NOK)

Data is retained for 15 years per automotive safety recall requirements.
