# Process Specification: Stamping Operations

**Spec ID:** PS-STP-001 | **Revision:** 2.1 | **Effective:** 2025-07-01

## Material Specifications

| Material | Grade | Thickness | Tensile Strength | Yield Strength | Elongation |
|----------|-------|-----------|------------------|----------------|------------|
| Body panels (outer) | DC06 (IF steel) | 0.8mm ± 0.04mm | 270-350 MPa | 120-180 MPa | ≥38% |
| Structural (floor, rails) | DP600 | 1.2mm ± 0.06mm | ≥600 MPa | 340-420 MPa | ≥20% |
| Reinforcements | DP980 | 1.5mm ± 0.08mm | ≥980 MPa | 600-720 MPa | ≥10% |
| Hood/trunk (aluminum) | 6016-T4 | 1.0mm ± 0.05mm | ≥180 MPa | 110-150 MPa | ≥24% |

## Forming Process Limits

| Parameter | Specification | Measurement Method |
|-----------|--------------|-------------------|
| Maximum thinning | <20% of original thickness | Ultrasonic thickness gauge |
| Draw depth | Per part spec ± 0.5mm | CMM |
| Springback compensation | Built into die geometry | Simulation (AutoForm) validated by CMM |
| Surface roughness (outer panels) | Ra ≤ 1.2 µm | Profilometer |
| Burr height (trimmed edges) | ≤ 0.15mm (target), ≤ 0.30mm (max) | Burr gauge |
| Hole position tolerance | ± 0.15mm from nominal | CMM or go/no-go gauge |
| Edge quality | No double-shear, no rollover >30% of thickness | Visual + microscope |

## Lubrication Specification

- **Lubricant**: Fuchs Renoform MZAN 58 (zinc phosphate compatible, waterborne)
- **Application**: Roller coater, both sides of blank
- **Film weight**: 1.0 - 2.0 g/m²
- **Compatibility**: Must not interfere with downstream e-coat adhesion
- **Shelf life**: 12 months from manufacture date

## SPC Requirements

| Parameter | Control Chart | Sample Size | Frequency | Cpk Target |
|-----------|--------------|-------------|-----------|------------|
| Panel thickness | X-bar & R | 5 | Every 50 parts | ≥1.33 |
| Draw depth | X-bar & R | 5 | Every 50 parts | ≥1.33 |
| Surface roughness | Individuals & MR | 1 | Every 100 parts | ≥1.33 |
| Burr height | Individuals & MR | 1 | Every 25 parts | ≥1.67 |
| Hole position | X-bar & R | 3 | Every 50 parts | ≥1.33 |
