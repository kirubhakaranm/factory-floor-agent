# Equipment Manual: ABB IRB 5500 FlexPainter

**Machine IDs:** PNT-02-PRM-RBT01/02, PNT-03-CLR-RBT01  
**Manufacturer:** ABB | **Model:** IRB 5500-25 FlexPainter  
**Reach:** 2975mm | **Payload:** 13 kg

## Specifications

| Parameter | Value |
|-----------|-------|
| Payload | 13 kg (including bell applicator) |
| Reach | 2975mm |
| Repeatability | ±0.15mm |
| Axes | 6 + hollow wrist for paint supply |
| Controller | ABB IRC5P paint controller |
| Weight | 485 kg |
| ATEX zone | Zone 1 (explosion-proof rated) |
| Max TCP speed | 2000 mm/s |

## Applicator

- **Type**: Electrostatic rotary bell atomizer
- **Bell cup diameter**: 70mm
- **Bell speed range**: 10,000 - 65,000 rpm
- **Electrostatic voltage**: 0 - 90 kV
- **Shaping air range**: 50 - 600 NL/min
- **Color change time**: <10 sec (24-valve color changer)
- **Paint supply**: Gear pump metering, 50-500 cc/min

## Maintenance Schedule

| Interval | Action |
|----------|--------|
| Every color change | Automatic flush cycle (solvent + air purge) |
| Every shift | Clean bell cup exterior, check spray pattern on test card |
| Daily | Check shaping air pressure, paint supply hose condition |
| Weekly | Clean color change valves, inspect electrostatic cable |
| Monthly | Calibrate flow meter, check bell motor current draw |
| 2,000 hours | Replace bell cup bearing (turbine bearing) |
| 4,000 hours | Full applicator overhaul — seals, bearings, HV cable |
| 8,000 hours | Robot service — joint greasing, cable inspection |

## Common Failure Modes

1. **Bell bearing failure** — vibration increase, uneven spray pattern, noise. MTBF: ~2,500 hours. Replace turbine bearing set.
2. **Electrostatic short** — no charge on paint, poor transfer efficiency. Check HV cable insulation, clean isolating supports.
3. **Color change valve leak** — color contamination, mixed paint. Replace valve seat, check pneumatic actuation pressure.
4. **Flow control drift** — DFT variation, runs or thin spots. Recalibrate gear pump, check for air in paint lines.
5. **Paint hose clog** — flow interruption, pressure spike. Flush line, filter paint supply, check for gel formation.

## Spray Pattern Troubleshooting

| Pattern Defect | Cause | Fix |
|----------------|-------|-----|
| Heavy center | Bell speed too low, flow too high | Increase bell speed, reduce flow rate |
| Heavy edges (donut) | Bell speed too high, shaping air too low | Reduce bell speed, increase shaping air |
| Asymmetric pattern | Clogged shaping air port, damaged bell lip | Clean air ports, replace bell cup if chipped |
| Spitting/dripping | Air in paint line, worn check valve | Bleed paint line, replace check valve |
| Orange peel texture | Atomization too coarse — low bell speed + high viscosity | Increase bell speed, check paint viscosity, adjust temperature |
