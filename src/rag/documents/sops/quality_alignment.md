# SOP-QAT-01: Wheel Alignment Check

**Station:** QAT-01-ALN | **Machine:** QAT-01-ALN-TST01 (Hunter WA Series)  
**Revision:** 1.8 | **Effective:** 2025-10-01

## Purpose

Verify front and rear wheel alignment parameters on completed vehicles before road test.

## Alignment Specifications

| Parameter | Front | Rear |
|-----------|-------|------|
| Camber | -0.5° ± 0.3° | -1.0° ± 0.3° |
| Caster | 3.5° ± 0.5° | N/A |
| Toe (total) | 0.10° ± 0.05° toe-in | 0.20° ± 0.08° toe-in |
| SAI (Steering Axis Inclination) | 13.0° ± 0.5° | N/A |
| Thrust angle | 0.00° ± 0.10° | 0.00° ± 0.10° |

## Procedure

1. Drive vehicle onto alignment rack — tires must be at production pressure (2.8 bar cold)
2. Attach wheel clamps and sensor heads
3. Roll-back compensation procedure (push vehicle 30cm backward, then 30cm forward)
4. Read live values on Hunter console
5. Compare to spec — if any parameter out of range, adjust:
   - Camber: eccentric cam bolt adjustment
   - Toe: tie rod end adjustment (front), eccentric cam (rear)
   - Caster: strut tower spacer (fixed — requires engineering disposition if out of spec)
6. Re-measure after adjustment to confirm in-spec
7. Print alignment report — attached to vehicle quality record

## Troubleshooting

| Symptom | Likely Cause | Action |
|---------|-------------|--------|
| Camber out of spec (both sides) | Suspension mounting point, strut assembly | Check strut bolts torque, measure body mounting points |
| Camber out of spec (one side) | Bent knuckle, damaged lower arm | Inspect knuckle and arm, replace if bent, re-measure |
| Toe out of range | Tie rod not adjusted at assembly, steering rack off-center | Adjust tie rod, center steering wheel, re-measure |
| Thrust angle off | Rear suspension misaligned, body rear section twisted | Check rear subframe bolts, measure body datum points |

## Pass/Fail Criteria

- All parameters within spec: **PASS** — proceed to water leak test
- One parameter marginal (within 80-100% of tolerance): **CONDITIONAL PASS** — note on quality record, monitor trend
- Any parameter beyond tolerance: **FAIL** — adjust and re-test, or route to rework
