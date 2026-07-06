# SOP-PNT-02: Prime and Basecoat Application

**Station:** PNT-02-PRM | **Machine:** PNT-02-PRM-RBT01 / RBT02  
**Revision:** 2.8 | **Effective:** 2025-08-01

## Purpose

Automated robotic application of primer surfacer and basecoat (color) using ABB IRB 5500 FlexPainter robots with electrostatic rotary bell atomizers.

## Process Sequence

1. **Sealer application** (manual station upstream — PVC sealer on seams)
2. **Primer surfacer** — waterborne primer, 2 coats, flash-off between coats
3. **Primer bake** (160°C, 15 min)
4. **Basecoat** — waterborne color, 2-3 coats depending on color
5. **Flash-off** (ambient, 5 min between coats)

## Key Parameters

| Parameter | Nominal | Min | Max |
|-----------|---------|-----|-----|
| Primer DFT | 35 µm | 30 µm | 40 µm |
| Basecoat DFT | 18 µm | 15 µm | 22 µm |
| Bell speed | 45,000 rpm | 35,000 | 55,000 |
| Shaping air | 350 NL/min | 300 | 400 |
| Electrostatic voltage | 60 kV | 50 kV | 70 kV |
| Booth temperature | 23°C | 21°C | 25°C |
| Booth humidity | 65% RH | 55% | 75% |
| Robot speed | 600 mm/s | 400 | 800 |
| Spray distance | 250 mm | 200 mm | 300 mm |

## Color Management

Current production colors for PrimeEV Motors:
- Pearl White (PEW-001) — 3 coats basecoat required (low hiding)
- Midnight Black (PEB-001) — 2 coats basecoat
- Storm Grey (PEG-001) — 2 coats basecoat
- Ocean Blue (PEU-001) — 2 coats basecoat + mid-coat
- Crimson Red (PER-001) — 3 coats basecoat (metallic)

## Troubleshooting

| Symptom | Likely Cause | Action |
|---------|-------------|--------|
| Orange peel | Atomization too coarse, viscosity high, speed too fast | Increase bell speed, check viscosity, reduce robot speed |
| Color mismatch | Wrong mix ratio, batch variation, DFT off-target | Verify mix formula, check spectrophotometer reading, adjust DFT |
| Fisheye | Silicone contamination, oil in compressed air | Find contamination source, check air dryer/filter, clean booth |
| Solvent pop | Flash-off too short, booth temp too high, DFT too thick | Extend flash time, reduce booth temp, reduce per-coat DFT |
| Runs/sags | Too much material, robot too close, viscosity too low | Reduce flow rate, increase spray distance, check viscosity |

## Booth Maintenance

- Continuous: booth airflow 0.3 m/s downward laminar flow — check manometers each shift
- Daily: clean paint lines, flush color change valves, check filter differential pressure
- Weekly: clean booth walls and grating, inspect spray nozzles, check water curtain
- Monthly: replace booth floor filters, calibrate humidity/temperature sensors
