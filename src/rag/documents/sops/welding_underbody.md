# SOP-WLD-01: Underbody Spot Welding

**Station:** WLD-01-UBD | **Machine:** WLD-01-UBD-RBT01 / RBT02  
**Revision:** 4.1 | **Effective:** 2025-08-20  
**Owner:** Body-in-White Engineering

## Purpose

Defines the welding procedure for underbody assembly — joining floor pan, front and rear rails, cross members, and suspension mounting points using resistance spot welding (RSW).

## Weld Schedule Parameters

| Parameter | Nominal | Min | Max |
|-----------|---------|-----|-----|
| Weld current | 9.5 kA | 8.0 kA | 11.0 kA |
| Weld time | 12 cycles (200ms) | 10 cycles | 16 cycles |
| Squeeze time | 8 cycles (133ms) | 6 cycles | 10 cycles |
| Hold time | 5 cycles (83ms) | 3 cycles | 8 cycles |
| Electrode force | 4.2 kN | 3.5 kN | 5.0 kN |
| Nugget diameter (target) | 5.5mm | 4.5mm | 7.0mm |

## Electrode Management

- **Tip dressing**: Every 200 welds — automatic tip dresser integrated in robot cell
- **Tip replacement**: Every 3,000 welds or when dressed diameter exceeds 8mm
- **Cap alignment check**: Every shift start — verify electrode alignment within 0.5mm
- **Cooling water flow**: Minimum 4 L/min per electrode — verify flow indicators are green

## Quality Requirements

- **Nugget diameter**: 4.5mm minimum (destructive peel test on sample coupons every 4 hours)
- **Weld spacing**: Per weld map — tolerance ±3mm
- **No expulsion**: Weld spatter indicates excessive current or contamination — adjust immediately
- **No burn-through**: Indicates excessive current on thin-gauge material — reduce by 0.5 kA increments
- **Shunt distance**: Minimum 15mm between adjacent weld spots to prevent current shunting

## Troubleshooting

| Symptom | Likely Cause | Action |
|---------|-------------|--------|
| Undersized nugget (<4.5mm) | Low current, worn electrodes, poor fit-up | Increase current 0.5 kA, dress/replace tips, check clamp fixtures |
| Weld expulsion (spatter) | Excessive current, contamination, gap between sheets | Reduce current 0.5 kA, clean surfaces, check fixture clamping |
| Burn-through | Current too high for material gauge, electrode mushroomed | Reduce current, dress electrodes, verify material thickness |
| Porosity in nugget | Coated material off-gassing, moisture, contamination | Extend squeeze time by 2 cycles, clean parts, verify coating spec |
| Electrode sticking | Low force, contamination, wrong electrode alloy | Increase force, clean parts, verify CuCrZr electrode material |
| Inconsistent nugget size | Shunt path through adjacent welds, fixture variation | Review weld sequence, increase shunt distance, recalibrate fixture |

## Weld Sequence

The underbody has 287 spot welds per vehicle. Weld sequence is critical to minimize distortion:
1. Front rail to floor pan (42 welds)
2. Rear rail to floor pan (38 welds)
3. Cross members (56 welds)
4. Suspension mount reinforcements (24 welds)
5. Tunnel reinforcement (18 welds)
6. Remaining structural welds per weld map

## Shift Changeover

1. Verify electrode tip condition — dress if >200 welds since last dress
2. Run weld test coupon — peel test to verify nugget diameter
3. Check cooling water flow on all guns
4. Review any parameter changes from previous shift in HMI log
