# Equipment Manual: Meidensha DYNAS3 LI 200 Chassis Dynamometer

**Machine IDs:** QAT-03-DYN-TST01, QAT-03-DYN-TST02  
**Manufacturer:** Meidensha | **Model:** DYNAS3 LI 200  
**Type:** 4WD chassis dynamometer with road load simulation

## Specifications

| Parameter | Value |
|-----------|-------|
| Maximum speed | 200 km/h |
| Maximum power absorption | 200 kW per axle |
| Roller diameter | 1219mm (48") |
| Roller surface | Knurled steel, 80-grit equivalent |
| Inertia simulation | 800 - 3500 kg (electronic) |
| Speed accuracy | ±0.1 km/h |
| Force accuracy | ±0.5% of reading |
| Axle spacing | Adjustable 2200 - 3200mm |

## Test Capabilities

1. **Speed test** — maximum speed verification
2. **Acceleration test** — 0-100 km/h time measurement
3. **Brake test** — stopping distance from specified speed
4. **ABS/ESC test** — split-mu and full-mu braking verification
5. **NVH measurement** — vibration sensors on steering wheel, seat rail, floor
6. **Range estimation** — drive cycle simulation (WLTP, EPA)
7. **Regenerative braking** — energy recovery measurement

## Maintenance Schedule

| Interval | Action |
|----------|--------|
| Daily | Clean roller surface (remove tire dust), verify roller alignment |
| Weekly | Check load cell calibration with known weight, inspect roller bearings |
| Monthly | Full load cell calibration, verify speed sensor accuracy with optical tach |
| Quarterly | Inspect drive motor brushes (if applicable), check cooling system |
| Annually | Roller resurfacing (re-knurl if worn smooth), bearing replacement |

## Safety Systems

- Vehicle restraint straps: 4-point, 5000 kg rated, must be secured before any test above 30 km/h
- Exhaust extraction: not required for EV, but ventilation system mandatory for battery thermal events
- Emergency roller lock: activated on E-STOP, rollers brake to stop within 3 seconds from 200 km/h
- Fire suppression: Novec 1230 system aimed at vehicle undercarriage, automatic activation at 150°C

## Common Issues

| Symptom | Likely Cause | Action |
|---------|-------------|--------|
| Speed reading unstable | Roller surface contamination, speed sensor fault | Clean rollers, recalibrate speed sensor |
| Force reading drift | Load cell calibration drift, temperature effect | Recalibrate with known weights, check ambient temp |
| Vehicle not tracking straight | Roller alignment, tire pressure unequal | Verify roller parallelism, check tire pressures |
| Excessive roller noise | Bearing wear, roller surface damage | Inspect bearings, check for flat spots on roller |
| Inertia simulation error | Controller calibration, motor drive fault | Recalibrate inertia simulation, check drive controller |
