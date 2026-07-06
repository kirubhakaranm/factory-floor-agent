# SOP-QAT-03: Dynamometer and Road Test

**Station:** QAT-03-DYN | **Machine:** QAT-03-DYN-TST01 / TST02 (Meidensha DYNAS3 LI 200)  
**Revision:** 3.1 | **Effective:** 2025-11-15

## Purpose

Final functional validation of completed vehicle on chassis dynamometer — verifying powertrain, brakes, steering, ADAS calibration, and NVH before shipment.

## Test Sequence (Total: ~5 minutes per vehicle)

### Phase 1: Stationary Checks (60 sec)
- HV system self-test — verify no DTC codes
- Brake light, headlamp, turn signal verification
- Horn test
- Wiper/washer operation
- Window operation (all 4)
- Mirror adjustment motors

### Phase 2: Low-Speed Roll (30 km/h, 60 sec)
- Steering response — verify power assist engages, no dead spots
- Brake application — verify ABS module activates, pedal feel normal
- Transmission/drive unit engagement — smooth torque delivery
- Suspension — listen for clunks, rattles, or abnormal noise

### Phase 3: High-Speed Roll (100 km/h, 90 sec)
- NVH assessment — vibration sensor threshold: <0.8 mm/s RMS on steering wheel
- Wind noise — not assessable on dyno (flagged for road test only)
- Wheel balance — vibration at speed, <0.05g at 100 km/h
- Powertrain efficiency — regenerative braking verification

### Phase 4: ABS/Stability Test (60 sec)
- Hard braking from 80 km/h — ABS activation, straight-line stability
- Split-mu braking simulation — ESC intervention verification
- Traction control — wheel slip simulation on low-friction roller

### Phase 5: ADAS Calibration Verification (30 sec)
- Front camera alignment check (static target board)
- Radar self-test
- Ultrasonic sensor ping test (12 sensors)

## Pass/Fail Criteria

| Test | Pass | Fail |
|------|------|------|
| DTC codes | Zero active DTCs | Any active DTC |
| Steering vibration at 100 km/h | <0.8 mm/s RMS | ≥0.8 mm/s RMS |
| Brake stopping distance 80→0 | <28m | ≥28m |
| ABS activation | Confirmed via CAN log | No activation detected |
| NVH — interior noise at 100 km/h | <68 dBA | ≥68 dBA |
| Regen braking | Energy recovery detected | No recovery |

## Troubleshooting

| Symptom | Likely Cause | Action |
|---------|-------------|--------|
| Vibration at speed | Wheel imbalance, tire defect, drive shaft | Rebalance wheels, inspect tires, check CV joints |
| Brake noise (squeal) | Pad glazing, rotor surface, caliper alignment | Bed-in brakes with 10 moderate stops, check rotor run-out |
| Steering pull | Alignment off, brake drag, tire pressure unequal | Send to alignment station, check caliper slides, verify pressures |
| Warning light active | DTC set, sensor fault, wiring issue | Read DTCs, trace fault, repair and clear codes, re-test |
| Regen not functioning | HV contactor issue, BMS fault, motor controller | Check HV system status, read BMS codes, verify motor controller |
| Poor acceleration | Drive unit fault, battery SOC low, throttle mapping | Check motor phase currents, verify SOC >50%, check throttle calibration |

## End of Line Release

- All phases PASS → vehicle receives **EOL PASS** stamp in quality system
- Any FAIL → vehicle routed to repair bay with failure code
- Repaired vehicles must complete full dyno re-test
- Final quality release requires sign-off by shift quality supervisor
