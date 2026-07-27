"""Bill of Materials and MRP tools."""

from typing import Literal

from src.datagen.factory_model import FACTORY_VEHICLE_MODELS


def get_bom_for_model(
    model_id: Literal["PE-SD100", "PE-SV200", "PE-CP300"],
) -> list[dict] | str:
    """[ACTION]: Retrieve the complete Bill of Materials for a vehicle model. [TARGET]: factory model (in-memory static data).

    [INPUT PREREQUISITE]: model_id must be one of the three Literal model IDs.
    PE-SD100 = Sedan, PE-SV200 = SUV, PE-CP300 = Compact.

    [OUTPUT GUARANTEE]: Returns the full component list with one row per component: part_number,
    description, category, station_id, supplier_id, unit_cost. Categories include:
    CHS, EXT, INT, PWR, ELC, BAT, SUS, BRK, FST, SEL, RAW. The Sedan and SUV models each have
    ~26 components across 7 stations.

    [NEGATIVE BOUNDARY]: Returns design-intent BOM — not a live inventory check.
    To verify material availability for a planned run, use check_mrp after getting the BOM.
    Cannot return BOM for sub-components or assemblies.

    Args:
        model_id: Vehicle model: 'PE-SD100', 'PE-SV200', or 'PE-CP300'

    Returns:
        List of BOM component dicts, or TERMINAL string if model_id not found.
    """
    model = FACTORY_VEHICLE_MODELS.get(model_id)
    if not model:
        return (
            f"TERMINAL: Vehicle model '{model_id}' not found. "
            "Valid models: PE-SD100 (Sedan), PE-SV200 (SUV), PE-CP300 (Compact). "
            "Do not retry — correct the model_id."
        )
    return [
        {
            "part_number": c.part_number,
            "description": c.description,
            "category": c.category,
            "station_id": c.station_id,
            "supplier_id": c.supplier_id,
            "unit_cost": c.unit_cost,
        }
        for c in model.components
    ]


def get_component_usage(part_number: str) -> list[dict] | str:
    """[ACTION]: Find which vehicle models use a specific component part number. [TARGET]: factory model (in-memory static data).

    [INPUT PREREQUISITE]: part_number must be a valid component identifier in format
    {CATEGORY}-{MODEL}-{SEQ} (e.g. 'CHS-SD100-001'). Obtain part numbers from get_bom_for_model.

    [OUTPUT GUARANTEE]: Returns one row per model that uses this part, with: model_id, model_name,
    station_id, quantity. If a part is shared across models, multiple rows are returned.

    [NEGATIVE BOUNDARY]: Returns only models in the current factory configuration (3 models).
    Cannot return supplier lead times or current stock — use get_spare_parts or get_raw_material_stock.

    Args:
        part_number: Component part number (e.g. 'CHS-SD100-001')

    Returns:
        List of model-usage dicts, or TERMINAL string if part not found in any BOM.
    """
    results = []
    for model_id, model in FACTORY_VEHICLE_MODELS.items():
        for c in model.components:
            if c.part_number == part_number:
                results.append({
                    "model_id": model_id,
                    "model_name": model.name,
                    "station_id": c.station_id,
                    "quantity": 1,
                })
    if not results:
        return (
            f"TERMINAL: Part number '{part_number}' not found in any vehicle BOM. "
            "Verify the part number from get_bom_for_model output. Do not retry."
        )
    return results


def check_mrp(
    model_id: Literal["PE-SD100", "PE-SV200", "PE-CP300"],
    planned_quantity: int,
) -> list[dict] | str:
    """[ACTION]: Compute material requirements for a planned production quantity. [TARGET]: factory model (in-memory static data).

    [INPUT PREREQUISITE]: model_id must be one of the three Literal model IDs. planned_quantity
    must be a positive integer. Note: this returns requirements only — to check actual stock
    coverage, compare against get_raw_material_stock output.

    [OUTPUT GUARANTEE]: Returns one row per BOM component with: part_number, description,
    required_qty (= planned_quantity × 1 unit per vehicle), unit_cost, total_cost, supplier_id.
    Does not indicate whether stock is sufficient — that comparison must be done separately.

    [NEGATIVE BOUNDARY]: Does not check actual inventory levels — it computes requirements only.
    Does not account for safety stock or reorder points. For a full MRP check with stock status,
    combine this output with get_raw_material_stock results.

    Args:
        model_id: Vehicle model: 'PE-SD100', 'PE-SV200', or 'PE-CP300'
        planned_quantity: Number of units to produce

    Returns:
        List of material requirement dicts, or TERMINAL string if model not found.
    """
    model = FACTORY_VEHICLE_MODELS.get(model_id)
    if not model:
        return (
            f"TERMINAL: Vehicle model '{model_id}' not found. "
            "Valid models: PE-SD100, PE-SV200, PE-CP300. Do not retry."
        )
    return [
        {
            "part_number": c.part_number,
            "description": c.description,
            "required_qty": planned_quantity,
            "unit_cost": c.unit_cost,
            "total_cost": round(c.unit_cost * planned_quantity, 2),
            "supplier_id": c.supplier_id,
        }
        for c in model.components
    ]
