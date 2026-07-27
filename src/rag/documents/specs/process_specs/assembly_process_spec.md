# Assembly Process Specification — PrimeEV Motors

**Applies to:** ASM-01-PWR, ASM-02-INT, ASM-03-FNL  
**Document:** ASM-PS-001 | **Revision:** 1.8 | **Effective:** 2025-06-01  
**Owner:** Assembly Engineering | **Approved by:** Manufacturing Engineering Manager

## Throughput Targets

| Metric | Target | Minimum Acceptable |
|--------|--------|--------------------|
| Daily vehicle output (all models) | **80 units/day** | 76 units/day (95% of target) |
| Per-shift throughput | **27 units/shift** (3 shifts × 27 = 81) | 26 units/shift |
| First Pass Yield (FPY) | ≥ 95% | 92% |
| OEE | ≥ 75% | 70% |

**Throughput shortfall trigger:** If actual daily output falls below 76 units (>5% below target) for 2 or more consecutive days, Production Manager must be notified and root cause analysis initiated within 24 hours.

## Station Cycle Time Targets

| Station | Operation | Ideal Cycle Time | Maximum Cycle Time |
|---------|-----------|-----------------|-------------------|
| ASM-01-PWR | Powertrain installation | 180 sec | 210 sec |
| ASM-02-INT | Interior and wiring | 240 sec | 275 sec |
| ASM-03-FNL | Final fit and trim | 200 sec | 230 sec |

**Line balance constraint:** ASM-02-INT is the pacemaker station — all other stations must complete within ASM-02-INT cycle time to avoid starvation/blockage.

## Model Mix Targets (Daily)

| Model | Daily Target | Shift Target |
|-------|-------------|--------------|
| PE-SD100 (Sedan) | 31 units | 10-11 units |
| PE-SV200 (SUV) | 25 units | 8-9 units |
| PE-CP300 (Compact) | 24 units | 8 units |
| **Total** | **80 units** | **27 units** |

## Quality Gates

- **ASM-01-PWR exit gate**: torque audit on all powertrain fasteners (100% electronic recording)
- **ASM-02-INT exit gate**: wiring continuity check + S&R pre-screen
- **ASM-03-FNL exit gate**: dimensional audit on door gaps, hood alignment, trunk fit

## Scrap and Rework Targets

| Metric | Target |
|--------|--------|
| Rework rate | < 2% of units |
| Scrap rate | < 0.1% of units |
| Rework cost per unit | < $150 average |
