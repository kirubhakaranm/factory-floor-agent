# Equipment Manual: Fanuc R-2000iC Spot Welding Robot

**Machine IDs:** WLD-01-UBD-RBT01/02, WLD-02-SDP-RBT01/02  
**Manufacturer:** Fanuc | **Model:** R-2000iC/210F  
**Payload:** 210 kg | **Reach:** 2655mm

## Specifications

| Parameter | Value |
|-----------|-------|
| Payload capacity | 210 kg |
| Maximum reach | 2655mm |
| Repeatability | ±0.05mm |
| Axes | 6 |
| Controller | Fanuc R-30iB Plus |
| Weight | 1130 kg |
| Power supply | 480V, 3-phase, 50/60 Hz |
| IP rating | IP67 (wrist), IP54 (body) |

## Welding Equipment

- **Weld gun**: Obara C-type servo gun, 5 kN electrode force
- **Weld controller**: Bosch Rexroth PSI 6300 (adaptive control, 1kHz monitoring)
- **Transformer**: 80 kVA mid-frequency (1000 Hz DC inverter)
- **Electrodes**: CuCrZr (Group A), 16mm dome radius, tip life 3,000 welds
- **Cooling**: Deionized water, 4 L/min per electrode, 15-20°C

## Maintenance Schedule

| Interval | Action |
|----------|--------|
| Every 200 welds | Automatic tip dressing (built into cell) |
| Every shift | Check electrode alignment, water flow indicators, cable condition |
| 3,000 welds | Replace electrode caps |
| Weekly | Grease robot joints (Fanuc-specified grease), check dress cutter blade |
| Monthly | Calibrate weld controller force sensor, check transformer primary current |
| 3,000 hours | Replace robot wrist unit seal, inspect cable harness |
| 6,000 hours | Major robot service — all joint reducers inspection, brake check |
| 10,000 hours | Reducer gear replacement (joints 1-3), full calibration |

## Common Failure Modes

1. **Joint motor overload** — excessive payload, collision, reducer wear. Check motor current trend. MTBF: ~15,000 hours.
2. **Reducer gear backlash** — weld position drift, path accuracy degradation. Measure backlash with dial indicator. Replace reducer.
3. **Electrode wear** — nugget diameter undersized, weld quality decline. Dress or replace caps per schedule.
4. **Cable harness fatigue** — intermittent signal loss, weld misfire. Common on dress-side cable. Replace harness.
5. **Teach pendant failure** — screen fault, button failure. Replace pendant module.
6. **Cooling water leak** — corrosion at electrode holder. Replace holder, inspect DI water quality (resistivity >1 MΩ·cm).

## Alarm Codes

| Code | Description | Action |
|------|-------------|--------|
| SRVO-023 | Joint 1 motor overcurrent | Check load, reduce speed, inspect reducer |
| SRVO-037 | Motor overheating | Reduce duty cycle, check cooling, clean motor fins |
| SRVO-050 | Collision detected | Inspect robot and fixture, reset collision sensor, re-teach if needed |
| WELD-101 | Weld current out of range | Check transformer, electrode condition, cable connections |
| WELD-205 | Electrode force error | Calibrate force sensor, check servo gun mechanism |
