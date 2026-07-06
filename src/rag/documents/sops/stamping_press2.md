# SOP-STP-02: Servo Press Operation — Press 2

**Station:** STP-02-PRS | **Machine:** STP-02-PRS-SRV01  
**Revision:** 2.1 | **Effective:** 2025-09-15  
**Owner:** Stamping Engineering

## Purpose

Standard procedure for operating the Komatsu H2F 1600 servo press for floor pan, hood, and trunk lid forming at Station STP-02-PRS.

## Safety Requirements

- LOTO before die change or maintenance
- Two-hand controls with anti-tie-down
- Light curtains verified each shift start
- Maximum press force: 1600 tons

## Startup Procedure

1. Release LOTO and verify all guards
2. Power on servo drive system — wait for initialization (approx 90 seconds)
3. Verify servo motor temperature below 40°C
4. Run three empty test strokes — confirm position accuracy within ±0.05mm
5. Load first blank, run single stroke, perform first-piece inspection

## Operating Parameters

| Parameter | Nominal | Lower Limit | Upper Limit |
|-----------|---------|-------------|-------------|
| Servo motor temperature | 35°C | 20°C | 55°C |
| Press force | 1200 kN | 800 kN | 1600 kN |
| Position accuracy | ±0.02mm | - | ±0.05mm |
| Slide velocity | 80 mm/s | 30 mm/s | 120 mm/s |
| Cycle time | 45 sec | 35 sec | 55 sec |
| Energy recovery | 35% | 25% | - |

## Key Differences from Hydraulic Press

- Servo press provides programmable slide motion profiles — different speed/force at each point in stroke
- Energy recovery system captures braking energy — monitor recovery percentage on HMI
- No hydraulic fluid to maintain, but servo motor temperature is critical
- Higher positional accuracy than hydraulic — enables thinner materials and tighter tolerances

## Troubleshooting

| Symptom | Likely Cause | Action |
|---------|-------------|--------|
| Servo motor overheating (>55°C) | Excessive duty cycle, cooling fan failure, high ambient | Reduce cycle rate, check cooling system, clean motor fins |
| Position error alarm | Encoder drift, mechanical backlash, ball screw wear | Recalibrate encoder, check ball screw preload, measure backlash |
| Part shows surface scratches | Die surface damage, blank contamination, insufficient lubrication | Inspect die, clean blank feed path, increase lubrication |
| Split or tear in formed part | Excessive forming speed, material too hard, die clearance | Reduce slide velocity at contact, verify material tensile strength, adjust die gap |

## Shutdown Procedure

1. Return slide to top dead center
2. Select STANDBY mode — servo drives remain powered for thermal stability
3. Full shutdown only for extended downtime: power off servo drives, then main disconnect
4. Log production count and any parameter changes made during shift
