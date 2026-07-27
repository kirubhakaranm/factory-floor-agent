# Equipment Manual: Schuler TwinServo 2800 Hydraulic Press

**Machine IDs:** STP-01-PRS-HYP01, STP-01-PRS-HYP02  
**Manufacturer:** Schuler AG | **Model:** TwinServo 2800  
**Press Force:** 2800 tons | **Bed Size:** 4500 × 2400mm

## Specifications

| Parameter | Value |
|-----------|-------|
| Maximum force | 28,000 kN (2800 tons) |
| Stroke | 800mm |
| Slide speed (rapid approach) | 250 mm/s |
| Slide speed (working) | 15 mm/s |
| Slide speed (return) | 200 mm/s |
| Bed area | 4500 × 2400mm |
| Shut height | 1200mm |
| Motor power | 2 × 160 kW |
| Hydraulic pressure (max) | 280 bar |
| Hydraulic oil capacity | 3,000 L |
| Oil specification | ISO VG 46, HLP |
| Cooling water requirement | 120 L/min at 15-20°C |
| Weight | 280 tons |

## Hydraulic System

- **Main pumps**: 2× Bosch Rexroth A10VSO 140 variable displacement axial piston
- **Servo valves**: Moog D661 proportional directional valves (4 per slide)
- **Accumulators**: 4× bladder type, 50L each, precharge 150 bar nitrogen
- **Filtration**: 10µm return line filter, 3µm servo valve filter, kidney loop with offline filtration
- **Oil cooler**: Plate heat exchanger, 120 kW capacity

## Maintenance Schedule

| Interval | Action |
|----------|--------|
| Every shift | Check oil level, inspect for leaks, verify pressure readings |
| 500 hours | Sample hydraulic oil for particle count and water content |
| 500 hours | Inspect cylinder seals for external leakage |
| 1,000 hours | Replace return line filter elements |
| 1,000 hours | Check accumulator precharge pressure (should be 150 ±5 bar) |
| 2,000 hours | Replace servo valve filters |
| 2,000 hours | Inspect slide gibs and adjust clearance (target 0.05mm) |
| 5,000 hours | Full hydraulic system flush and oil change |
| 10,000 hours | Major overhaul — cylinder reseal, pump inspection, valve overhaul |

## Solenoid Valve Assembly

Each slide axis uses **4× Moog D661 proportional directional control valves**, each driven by an integrated solenoid coil assembly. The solenoid converts electrical control signals into hydraulic spool movement.

### Solenoid Valve Operating Specifications

| Parameter | Value |
|-----------|-------|
| Rated operating pressure | 350 bar (max system exposure) |
| Normal system pressure range | 180–240 bar |
| Maximum continuous pressure | 280 bar |
| Overpressure alarm threshold | 265 bar |
| Solenoid supply voltage | 24 VDC ±10% |
| Solenoid coil resistance | 26 Ω ±5% at 20°C |
| Maximum coil current | 0.92 A |
| Rated duty cycle | Continuous (100%) at ≤40°C ambient |
| Coil temperature limit | 85°C (winding); exceeding causes insulation degradation |
| MTBF (solenoid coil, continuous duty) | ~15,000 operating hours |
| MTBF (valve spool/body, clean oil) | ~25,000 operating hours |
| Response time (0→full stroke) | ≤25 ms at nominal pressure |

### Overstrain (OSF) Failure Mode

**Definition:** Overstrain condition occurs when the solenoid coil or valve spool is subjected to sustained load exceeding rated capacity, causing insulation breakdown, spool seizure, or coil burnout.

**Root causes of solenoid overstrain on hydraulic presses:**

1. **Elevated system back-pressure** — If downstream restriction (blocked filter, worn cylinder seals, contamination) increases circuit resistance, the solenoid must exert greater force to move the spool, accelerating wear.
2. **Excessive cycling frequency** — Production rate increases or cycle time reductions beyond design parameters increase thermal load on the coil. At 100% duty cycle, coil temperature is the limiting factor.
3. **Hydraulic oil contamination** — Particulates >10 µm lodge in the valve spool clearance (2–4 µm), causing stiction. The solenoid then operates against mechanical resistance, drawing excess current and generating heat.
4. **Coil insulation degradation** — Repeated thermal cycling (on/off at shift changes) causes insulation micro-cracking. Accelerated by oil contamination soaking into coil windings.
5. **Incorrect replacement specification** — Aftermarket solenoid coils with resistance or voltage rating outside spec cause current draw outside the nominal 0.92 A, reducing service life.

**Diagnostic indicators of developing overstrain:**
- Solenoid coil current draw >1.1 A (measurable at control cabinet terminal block)
- Coil surface temperature >60°C during normal cycle (infrared gun measurement)
- Valve response time drifting >35 ms (detected by position encoder lag)
- Oil particle count trending above ISO 4406 class 18/16/13 (check oil sample)

### Solenoid Valve Inspection Procedure

**Every PM (recommended interval: ≤500 hours or 2 weeks for high-cycle machines):**
1. Measure solenoid coil resistance with multimeter at control cabinet (spec: 26 Ω ±5%). Out-of-spec → replace coil.
2. Verify supply voltage at solenoid terminals during cycle: 24 VDC ±10%. Low voltage causes excess current draw.
3. Check coil surface temperature with infrared thermometer during steady-state production. >60°C → investigate cause before next shift.
4. Inspect coil connector for oil ingress, pin corrosion, or loose crimp.

**At 500-hour interval:**
1. Pull valve spool and inspect for scoring, pitting, or contamination buildup.
2. Clean spool with clean solvent (mineral spirits) and compressed air. Do NOT use abrasives.
3. Check spool clearance against bore — acceptable: 2–4 µm; replace valve body if >8 µm.
4. Replace solenoid coil as a precautionary measure if machine has had ≥2 OSF events in 6 months.

### Solenoid Valve Replacement Notes

- **Part number for solenoid coil:** SP-HYP-007 (Moog genuine coil; 24 VDC, 26 Ω). Do NOT substitute aftermarket coils — resistance tolerance varies, causing coil current to fall outside design range.
- **Part number for complete valve assembly:** SP-HYP-003 (Moog D661 complete valve, $3,200; lead time 14 days).
- After replacement: cycle valve 50 times at reduced pressure (100 bar) before returning to full production. Monitor coil temperature during first 2 hours of production.

## Common Failure Modes

1. **Solenoid valve overstrain (OSF)** — Coil burnout or spool seizure from excess load, contamination-induced stiction, or thermal cycling. MTBF: ~15,000 hours (clean oil); significantly lower with contaminated oil or high cycling frequency. See Solenoid Valve section above for full diagnostic procedure.
2. **Hydraulic pump wear** — reduced flow rate, pressure drops, increased noise. MTBF: ~8,000 hours. Replace pump cartridge.
3. **Cylinder seal failure** — external oil leak, position drift. MTBF: ~12,000 hours. Replace seal kit.
4. **Servo valve contamination** — erratic slide motion, position error. Caused by oil contamination. Flush and replace valve.
5. **Accumulator bladder failure** — slow press cycle, pressure fluctuations. Check precharge with nitrogen gauge. Replace bladder.
6. **Cooler fouling** — oil temperature rise. Clean heat exchanger plates, check cooling water flow.

## Spare Parts List

| Part Number | Description | Lead Time | Unit Cost |
|-------------|-------------|-----------|-----------|
| SP-HYP-001 | Hydraulic pump cartridge (Rexroth A10VSO 140) | 14 days | $2,800 |
| SP-HYP-002 | Cylinder seal kit (main ram) | 7 days | $450 |
| SP-HYP-003 | Servo valve (Moog D661) | 14 days | $3,200 |
| SP-HYP-004 | Return line filter element (10µm) | 3 days | $65 |
| SP-HYP-005 | Accumulator bladder (50L) | 7 days | $380 |
| SP-HYP-006 | Slide gib set (bronze) | 14 days | $1,200 |
| SP-HYP-007 | Solenoid coil (Moog) | 5 days | $180 |
