# SOP-PNT-03: Clearcoat Application and Cure

**Station:** PNT-03-CLR | **Machine:** PNT-03-CLR-RBT01, PNT-03-CLR-OVN01  
**Revision:** 2.5 | **Effective:** 2025-09-01

## Purpose

Application of 2K urethane clearcoat for UV protection, gloss, and scratch resistance, followed by thermal cure in the Dürr EcoInCure oven.

## Key Parameters

| Parameter | Nominal | Min | Max |
|-----------|---------|-----|-----|
| Clearcoat DFT | 45 µm | 40 µm | 55 µm |
| Cure temperature | 140°C | 135°C | 145°C |
| Cure time | 25 min at metal temp | 22 min | 30 min |
| Gloss (20° angle) | 90 GU | 85 GU | - |
| DOI (distinctness of image) | 85 | 80 | - |
| Hardness (pencil) | H | F min | - |

## Oven Zones

The EcoInCure 4.0 oven has 4 temperature zones:
1. Ramp-up zone: ambient → 100°C (5 min)
2. Hold zone 1: 100°C (3 min) — solvent flash
3. Ramp zone 2: 100°C → 140°C (4 min)
4. Cure zone: 140°C (25 min) — crosslinking

Body metal temperature must reach 140°C within tolerance. IR pyrometers at oven exit verify.

## Troubleshooting

| Symptom | Likely Cause | Action |
|---------|-------------|--------|
| Runs/sags | Excessive DFT, robot too slow, viscosity low | Reduce flow rate, increase robot speed, check mix ratio |
| Dust inclusion | Booth contamination, filter bypass, body not tacked | Replace filters, check seals, apply tack cloth before clearcoat |
| Haze/low gloss | Under-cure, contaminated clearcoat, moisture in line | Verify oven temp profile, check material, drain air lines |
| Pinholes | Solvent entrapment, cure too fast, DFT too thick | Extend flash before oven, reduce ramp rate, reduce per-coat thickness |
| Yellowing | Over-cure, wrong hardener ratio, UV exposure in booth | Check oven temp, verify 2K mix ratio, cover booth windows |
| Cracking/checking | Over-bake, incompatible layer adhesion | Reduce cure time, verify primer/base compatibility with clearcoat batch |

## Cure Validation

- Monthly: run cure window study (under-cure, nominal, over-cure) with QUV accelerated weathering test
- Each oven maintenance: run temperature uniformity survey with 12-channel data logger (Datapaq)
- Out-of-spec cure: quarantine affected bodies, perform solvent rub test (MEK double rubs >100 required)
