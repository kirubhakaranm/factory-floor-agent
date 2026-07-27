# Welding Process Specification — PrimeEV Motors

**Applies to:** WLD-01-UBD, WLD-02-SDP, WLD-03-RCL  
**Document:** WLD-PS-001 | **Revision:** 2.4 | **Effective:** 2025-03-01  
**Owner:** Welding Engineering | **Approved by:** Manufacturing Engineering Manager

## Resistance Spot Weld — Process Parameters

### Nugget Diameter Requirements

| Panel Type | Minimum Nugget Diameter | Target | Maximum |
|------------|------------------------|--------|---------|
| Body structural panels (underbody, side panel) | **4.5 mm** | 5.5 mm | 7.0 mm |
| Roof and closure panels | 4.0 mm | 5.0 mm | 6.5 mm |
| Reinforcement brackets | 4.0 mm | 4.8 mm | 6.0 mm |
| Non-structural trim attachments | 3.5 mm | 4.5 mm | 6.0 mm |

**Nugget diameter below minimum = non-conforming weld — requires re-weld or MRB disposition.**

### Weld Schedule Parameters — Underbody (WLD-01-UBD)

| Parameter | Nominal | Lower Limit | Upper Limit | Unit |
|-----------|---------|-------------|-------------|------|
| Weld current | 8,500 | 8,000 | 9,200 | A |
| Squeeze time | 50 | 40 | 60 | cycles (60Hz) |
| Weld time | 16 | 14 | 18 | cycles |
| Hold time | 8 | 6 | 10 | cycles |
| Electrode force | 400 | 350 | 450 | daN |
| Shunt distance (min) | 25 | 20 | — | mm |

### Electrode Condition Requirements

- Electrode tip diameter: 6.0 ± 0.5 mm — dress if outside range
- Maximum electrode life before replacement: 3,000 welds
- Dressing frequency: every 150–200 welds (F-type tip dresser, 1–2 cuts)
- Electrode cap type: RWMA Class 2 copper alloy (Cr-Zr-Cu)

## Process Capability Requirements

| Parameter | Minimum Cpk Required | Action if Below |
|-----------|---------------------|-----------------|
| nugget_diameter | **1.33** | Mandatory corrective action — adjust weld schedule, inspect electrodes |
| weld_current | 1.33 | Review transformer tap setting, check electrode contact resistance |
| electrode_force | 1.33 | Inspect gun cylinder pressure, check arm deflection |
| squeeze_time | 1.67 | No known issue — verify timer calibration |
| shunt_distance | 1.33 | Review fixture layout, adjust weld sequence |

**Cpk between 1.0 and 1.33 = marginal — monitor closely, initiate parameter review within 5 business days.**  
**Cpk below 1.0 = not capable — stop production and initiate immediate corrective action.**

## Weld Quality Verification

### Peel Test (Destructive)
- Frequency: first piece each shift + every 500 welds
- Acceptance: nugget must pull from one sheet (button pull) with diameter ≥ minimum spec
- Failure mode: interfacial fracture = weld schedule issue; partial pull = electrode wear

### Ultrasonic Inspection (Non-Destructive)
- Frequency: 100% on safety-critical welds (underbody structural nodes)
- Equipment: Olympus EPOCH 6LT phased array
- Acceptance criteria: nugget diameter ≥ 4.5 mm confirmed by A-scan

## Out-of-Control Response

If SPC signals an out-of-control condition on nugget_diameter:
1. Do not stop production immediately — verify with peel test on next 3 joints
2. If peel test confirms non-conformance → stop and quarantine last 50 bodies
3. Adjust weld current +200A or inspect/dress electrodes
4. Re-run 5 qualification welds before resuming production
5. Notify Quality Engineer and log corrective action in MES
