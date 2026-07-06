"""Bill of Materials and MRP tools."""

from src.datagen.factory_model import FACTORY_VEHICLE_MODELS


def get_bom_for_model(model_id: str) -> list[dict]:
    """Get the complete Bill of Materials for a vehicle model.

    Args:
        model_id: Vehicle model ID (PE-SD100, PE-SV200, PE-CP300)

    Returns:
        List of components with part_number, description, category, station, supplier, cost
    """
    model = FACTORY_VEHICLE_MODELS.get(model_id)
    if not model:
        return [{"error": f"Model {model_id} not found. Valid: PE-SD100, PE-SV200, PE-CP300"}]

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


def get_component_usage(part_number: str) -> list[dict]:
    """Find which vehicle models use a specific component.

    Args:
        part_number: Component part number (e.g., 'CHS-SD100-001')

    Returns:
        List of models using this component with quantity and station
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
        return [{"error": f"Part {part_number} not found in any BOM"}]
    return results


def check_mrp(model_id: str, planned_quantity: int) -> list[dict]:
    """Check material requirements for a planned production quantity.

    Args:
        model_id: Vehicle model ID
        planned_quantity: Number of units planned

    Returns:
        List of components needed with required quantity and estimated cost
    """
    model = FACTORY_VEHICLE_MODELS.get(model_id)
    if not model:
        return [{"error": f"Model {model_id} not found"}]

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
