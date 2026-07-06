# SOP-ASM-01: Powertrain and Battery Installation

**Station:** ASM-01-PWR | **Machine:** ASM-01-PWR-RBT01 / RBT02  
**Revision:** 3.5 | **Effective:** 2025-11-01

## Purpose

Installation of battery pack, front/rear drive units, HV junction box, and high-voltage wiring to painted body. This station handles all powertrain mechanical and electrical connections.

## Safety — High Voltage

- **All personnel must hold HV Safety certification (minimum 60 hours training)**
- HV interlock must be verified DISCONNECTED before any manual intervention
- Insulated gloves rated 1000V Class 0 must be worn when handling HV components
- HV verification meter must confirm <30V DC before touching any HV terminal
- No metal jewelry, watches, or conductive tools in HV work zone

## Installation Sequence

1. **Battery pack** — robotic lift from AGV, locate on body mounting points (8 bolts M12)
2. **Front drive unit** — robotic positioning, 6 mounting bolts M10 + 2 locating pins
3. **Rear drive unit** — same as front, different bracket geometry per model
4. **HV junction box** — manual installation, 4 bolts M8, torque to spec
5. **HV cable routing** — manual, follow routing clips, secure with cable ties every 200mm
6. **Coolant line connections** — quick-connect fittings, verify click engagement
7. **HV connector mating** — verify lock indicators (orange lock tabs fully seated)
8. **Torque verification** — all critical fasteners checked with electronic torque wrench

## Critical Torque Specifications

| Fastener | Spec (Nm) | Tolerance | Tool |
|----------|-----------|-----------|------|
| Battery mount bolts M12 | 95 Nm | ±5 Nm | Electronic torque wrench, recorded |
| Drive unit mount M10 | 65 Nm | ±3 Nm | Electronic torque wrench, recorded |
| HV junction box M8 | 25 Nm | ±2 Nm | Preset torque wrench |
| Coolant fittings | Hand-tight + 1/4 turn | - | Manual |
| Ground stud M6 | 10 Nm | ±1 Nm | Preset torque wrench |

All critical torque values are electronically recorded per VIN — traceability is mandatory.

## Troubleshooting

| Symptom | Likely Cause | Action |
|---------|-------------|--------|
| Torque out-of-spec (high) | Cross-threaded, wrong bolt grade, contaminated threads | Remove bolt, inspect threads, clean and re-torque. Scrap bolt if damaged |
| Torque out-of-spec (low) | Stripped thread, incorrect tightening sequence, lubricant issue | Inspect thread, re-tap if minor damage, replace insert if stripped |
| Bolt missing alert | Missed in sequence, bolt feeder empty | Check feeder, manually install and torque, record in system |
| Connector not seated | Misalignment, bent pin, contamination | Inspect connector, straighten pins, clean contacts, re-mate |
| Fluid leak at coolant connection | O-ring damaged, fitting not fully engaged | Replace O-ring, re-seat fitting, verify click, pressure test |

## Model Variations

| Component | PE-SD100 | PE-SV200 | PE-CP300 |
|-----------|----------|----------|----------|
| Battery pack | 75 kWh, 450 kg | 100 kWh, 580 kg | 55 kWh, 340 kg |
| Front drive unit | Standard (150 kW) | Performance (200 kW) | None (RWD only) |
| Rear drive unit | Standard (200 kW) | Performance (250 kW) | Standard (150 kW) |
| HV voltage | 400V | 800V | 400V |
