# SOP-PNT-01: E-Coat (Electrodeposition Coating)

**Station:** PNT-01-ECT | **Machine:** PNT-01-ECT-PMP01 / PMP02  
**Revision:** 3.0 | **Effective:** 2025-07-01

## Purpose

Electrodeposition coating process providing corrosion protection to the body-in-white. The body is submerged in an e-coat tank and electrically charged to deposit a uniform epoxy coating.

## Process Stages

1. **Alkaline cleaning** (pH 10-12, 55°C, 2 min) — remove oils, stamping lubricant
2. **Rinse 1** (DI water, ambient)
3. **Zinc phosphate conversion** (pH 3.0-3.5, 52°C, 90 sec) — crystalline phosphate coating 2-4 g/m²
4. **Rinse 2** (DI water)
5. **E-coat immersion** (voltage 280V, bath temp 30°C, 180 sec) — cathodic epoxy deposition
6. **UF permeate rinse** (3 stages) — recover dragout
7. **Bake oven** (180°C, 20 min) — cure e-coat film

## Key Parameters

| Parameter | Nominal | Min | Max |
|-----------|---------|-----|-----|
| E-coat bath temperature | 30°C | 28°C | 32°C |
| Applied voltage | 280V | 260V | 320V |
| Bath solids (NV%) | 20% | 18% | 22% |
| Bath pH | 5.8 | 5.5 | 6.2 |
| Conductivity | 1200 µS/cm | 1000 | 1500 |
| Film thickness (dry) | 20 µm | 17 µm | 25 µm |
| Bake temperature | 180°C | 175°C | 185°C |
| Phosphate coating weight | 3.0 g/m² | 2.0 | 4.5 |

## Quality Checks

- Film thickness: measure at 6 control points per body (roof, hood, fender, door, rocker, underbody) with Elcometer DFT gauge
- Adhesion: crosshatch adhesion test (ASTM D3359) — must achieve 4B or 5B rating
- Salt spray resistance: 1000-hour minimum per ASTM B117 (quarterly validation coupon)
- Visual: no bare spots, craters, drips, or runs

## Troubleshooting

| Symptom | Likely Cause | Action |
|---------|-------------|--------|
| Thin coverage (<17µm) | Low voltage, bath solids depleted, short dip time | Increase voltage, add resin, verify immersion time |
| Bare spots | Surface contamination, air pocket entrapment | Improve cleaning, adjust body entry angle, check rotation |
| Craters | Silicone contamination, oil splash | Identify contamination source, check upstream cleaning, sample bath |
| Drips at drain holes | Insufficient drain time, plugged drain holes | Extend drain time, verify all drain holes are open |
| E-coat too thick (>25µm) | Excessive voltage, long dip time, low bath conductivity | Reduce voltage, verify timer, check conductivity |

## Bath Maintenance

- Daily: measure pH, conductivity, NV%, temperature
- Weekly: bacteria count, UF membrane flux rate, anode bag inspection
- Monthly: full bath analysis by supplier (CoatChem Solutions), adjust chemistry
- Quarterly: drain and clean tank, inspect anodes, replace UF membranes if flux <50% of initial
