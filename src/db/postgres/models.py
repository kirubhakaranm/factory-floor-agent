"""SQLAlchemy models for PrimeEV Motors factory database — ~25 tables."""

from datetime import date, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


# ─── Factory ───────────────────────────────────────────────────────────────────


class Line(Base):
    __tablename__ = "lines"

    line_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    stage: Mapped[str] = mapped_column(String(10))
    name: Mapped[str] = mapped_column(String(50))

    stations: Mapped[list["Station"]] = relationship(back_populates="line")


class Station(Base):
    __tablename__ = "stations"

    station_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    stage: Mapped[str] = mapped_column(String(10))
    name: Mapped[str] = mapped_column(String(50))
    position: Mapped[int] = mapped_column(Integer)
    line_id: Mapped[str] = mapped_column(String(20), ForeignKey("lines.line_id"))

    line: Mapped["Line"] = relationship(back_populates="stations")
    machines: Mapped[list["Machine"]] = relationship(back_populates="station")


class Machine(Base):
    __tablename__ = "machines"

    machine_id: Mapped[str] = mapped_column(String(30), primary_key=True)
    station_id: Mapped[str] = mapped_column(String(20), ForeignKey("stations.station_id"))
    machine_type: Mapped[str] = mapped_column(String(10))
    model: Mapped[str] = mapped_column(String(100))
    serial_number: Mapped[str] = mapped_column(String(50), nullable=True)
    install_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    firmware_version: Mapped[str | None] = mapped_column(String(20), nullable=True)
    total_operating_hours: Mapped[float] = mapped_column(Float, default=0.0)
    lifecycle_status: Mapped[str] = mapped_column(String(20), default="active")
    criticality: Mapped[str] = mapped_column(String(5))
    warranty_expiry: Mapped[date | None] = mapped_column(Date, nullable=True)
    last_overhaul: Mapped[date | None] = mapped_column(Date, nullable=True)
    next_overhaul: Mapped[date | None] = mapped_column(Date, nullable=True)
    maintenance_interval_hrs: Mapped[float] = mapped_column(Float, default=500.0)

    station: Mapped["Station"] = relationship(back_populates="machines")
    failures: Mapped[list["EquipmentFailure"]] = relationship(back_populates="machine")


# ─── People ────────────────────────────────────────────────────────────────────


class Operator(Base):
    __tablename__ = "operators"

    operator_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    shift: Mapped[str] = mapped_column(String(20))
    crew_id: Mapped[str] = mapped_column(String(20))
    certifications: Mapped[list] = mapped_column(JSON, default=list)
    hire_date: Mapped[date | None] = mapped_column(Date, nullable=True)


class Technician(Base):
    __tablename__ = "technicians"

    tech_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    shift: Mapped[str] = mapped_column(String(20))
    specializations: Mapped[list] = mapped_column(JSON, default=list)


class Crew(Base):
    __tablename__ = "crews"

    crew_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    shift_name: Mapped[str] = mapped_column(String(20))
    supervisor_id: Mapped[str] = mapped_column(String(20))


class Shift(Base):
    __tablename__ = "shifts"

    shift_id: Mapped[str] = mapped_column(String(30), primary_key=True)
    date: Mapped[date] = mapped_column(Date)
    shift_name: Mapped[str] = mapped_column(String(20))
    start_time: Mapped[datetime] = mapped_column(DateTime)
    end_time: Mapped[datetime] = mapped_column(DateTime)
    crew_id: Mapped[str] = mapped_column(String(20))
    production_target: Mapped[int] = mapped_column(Integer, default=27)


# ─── Product ───────────────────────────────────────────────────────────────────


class VehicleModel(Base):
    __tablename__ = "vehicle_models"

    model_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    year: Mapped[int] = mapped_column(Integer)
    variant: Mapped[str] = mapped_column(String(20))


class Component(Base):
    __tablename__ = "components"

    component_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    part_number: Mapped[str] = mapped_column(String(30), unique=True)
    description: Mapped[str] = mapped_column(String(200))
    category: Mapped[str] = mapped_column(String(10))
    station_id: Mapped[str] = mapped_column(String(20))
    supplier_id: Mapped[str] = mapped_column(String(20))
    unit_cost: Mapped[float] = mapped_column(Float)


class BillOfMaterials(Base):
    __tablename__ = "bill_of_materials"

    bom_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    model_id: Mapped[str] = mapped_column(String(20), ForeignKey("vehicle_models.model_id"))
    part_number: Mapped[str] = mapped_column(String(30))
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    station_id: Mapped[str] = mapped_column(String(20))


class VinRegistry(Base):
    __tablename__ = "vin_registry"

    vin_id: Mapped[str] = mapped_column(String(30), primary_key=True)
    model_id: Mapped[str] = mapped_column(String(20), ForeignKey("vehicle_models.model_id"))
    batch_id: Mapped[str] = mapped_column(String(20), nullable=True)
    production_date: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(20), default="completed")


# ─── Supply Chain ──────────────────────────────────────────────────────────────


class Supplier(Base):
    __tablename__ = "suppliers"

    supplier_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    category: Mapped[str] = mapped_column(String(50))
    rating: Mapped[float] = mapped_column(Float, default=4.0)
    lead_time_days: Mapped[int] = mapped_column(Integer, default=7)


class RawMaterial(Base):
    __tablename__ = "raw_materials"

    material_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    supplier_id: Mapped[str] = mapped_column(String(20), ForeignKey("suppliers.supplier_id"))
    part_number: Mapped[str] = mapped_column(String(30))
    description: Mapped[str] = mapped_column(String(200))


class ReceivingInspection(Base):
    __tablename__ = "receiving_inspections"

    ri_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    material_id: Mapped[str] = mapped_column(String(20))
    supplier_id: Mapped[str] = mapped_column(String(20), ForeignKey("suppliers.supplier_id"))
    lot_number: Mapped[str] = mapped_column(String(50))
    inspection_date: Mapped[date] = mapped_column(Date)
    inspector_id: Mapped[str] = mapped_column(String(20))
    result: Mapped[str] = mapped_column(String(20))
    disposition: Mapped[str] = mapped_column(String(20))
    first_article_status: Mapped[str] = mapped_column(String(20), default="approved")


class SupplierScorecard(Base):
    __tablename__ = "supplier_scorecards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    supplier_id: Mapped[str] = mapped_column(String(20), ForeignKey("suppliers.supplier_id"))
    month: Mapped[date] = mapped_column(Date)
    defect_ppm: Mapped[float] = mapped_column(Float)
    on_time_pct: Mapped[float] = mapped_column(Float)
    quality_score: Mapped[float] = mapped_column(Float)
    delivery_score: Mapped[float] = mapped_column(Float)
    overall_grade: Mapped[str] = mapped_column(String(5))


class SupplierNcr(Base):
    __tablename__ = "supplier_ncrs"

    ncr_id: Mapped[str] = mapped_column(String(30), primary_key=True)
    supplier_id: Mapped[str] = mapped_column(String(20), ForeignKey("suppliers.supplier_id"))
    lot_id: Mapped[str] = mapped_column(String(50))
    issue: Mapped[str] = mapped_column(Text)
    disposition: Mapped[str] = mapped_column(String(20))
    date: Mapped[date] = mapped_column(Date)


# ─── Production ────────────────────────────────────────────────────────────────


class ProductionOrder(Base):
    __tablename__ = "production_orders"

    po_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    model_id: Mapped[str] = mapped_column(String(20), ForeignKey("vehicle_models.model_id"))
    quantity: Mapped[int] = mapped_column(Integer)
    priority: Mapped[str] = mapped_column(String(20), default="normal")
    due_date: Mapped[date] = mapped_column(Date)


class ProductionBatch(Base):
    __tablename__ = "production_batches"

    batch_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    line_id: Mapped[str] = mapped_column(String(20))
    model_id: Mapped[str] = mapped_column(String(20), ForeignKey("vehicle_models.model_id"))
    start_time: Mapped[datetime] = mapped_column(DateTime)
    end_time: Mapped[datetime] = mapped_column(DateTime)
    units_produced: Mapped[int] = mapped_column(Integer)
    units_passed: Mapped[int] = mapped_column(Integer)


# ─── Quality ───────────────────────────────────────────────────────────────────


class DimensionalInspection(Base):
    __tablename__ = "dimensional_inspections"

    insp_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    vin_id: Mapped[str | None] = mapped_column(String(30), nullable=True)
    station_id: Mapped[str] = mapped_column(String(20))
    measurement_name: Mapped[str] = mapped_column(String(50))
    nominal: Mapped[float] = mapped_column(Float)
    upper_tol: Mapped[float] = mapped_column(Float)
    lower_tol: Mapped[float] = mapped_column(Float)
    actual_value: Mapped[float] = mapped_column(Float)
    result: Mapped[str] = mapped_column(String(10))
    timestamp: Mapped[datetime] = mapped_column(DateTime)


class SamplingInspection(Base):
    __tablename__ = "sampling_inspections"

    insp_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    station_id: Mapped[str] = mapped_column(String(20))
    lot_size: Mapped[int] = mapped_column(Integer)
    sample_size: Mapped[int] = mapped_column(Integer)
    aql_level: Mapped[float] = mapped_column(Float)
    accept_number: Mapped[int] = mapped_column(Integer)
    reject_number: Mapped[int] = mapped_column(Integer)
    defects_found: Mapped[int] = mapped_column(Integer)
    disposition: Mapped[str] = mapped_column(String(20))
    inspection_type: Mapped[str] = mapped_column(String(20))
    timestamp: Mapped[datetime] = mapped_column(DateTime)


class VisualChecklist(Base):
    __tablename__ = "visual_checklists"

    checklist_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    vin_id: Mapped[str | None] = mapped_column(String(30), nullable=True)
    station_id: Mapped[str] = mapped_column(String(20))
    checkpoint_items: Mapped[dict] = mapped_column(JSON)
    defect_category: Mapped[str] = mapped_column(String(20))
    timestamp: Mapped[datetime] = mapped_column(DateTime)


class ReworkRecord(Base):
    __tablename__ = "rework_records"

    rework_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    vin_id: Mapped[str | None] = mapped_column(String(30), nullable=True)
    station_id: Mapped[str] = mapped_column(String(20))
    defect_type: Mapped[str] = mapped_column(String(50))
    rework_action: Mapped[str] = mapped_column(Text)
    rework_time_min: Mapped[int] = mapped_column(Integer)
    re_inspect_result: Mapped[str] = mapped_column(String(10))
    cost: Mapped[float] = mapped_column(Float)
    timestamp: Mapped[date] = mapped_column(Date)


class ScrapRecord(Base):
    __tablename__ = "scrap_records"

    scrap_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    vin_id: Mapped[str | None] = mapped_column(String(30), nullable=True)
    station_id: Mapped[str] = mapped_column(String(20))
    reason: Mapped[str] = mapped_column(Text)
    cost: Mapped[float] = mapped_column(Float)
    timestamp: Mapped[date] = mapped_column(Date)


class DeviationRecord(Base):
    __tablename__ = "deviation_records"

    dev_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    vin_id: Mapped[str | None] = mapped_column(String(30), nullable=True)
    mrb_approval: Mapped[str] = mapped_column(String(50))
    justification: Mapped[str] = mapped_column(Text)


# ─── Equipment ─────────────────────────────────────────────────────────────────


class EquipmentFailure(Base):
    __tablename__ = "equipment_failures"

    failure_id: Mapped[str] = mapped_column(String(30), primary_key=True)
    machine_id: Mapped[str] = mapped_column(String(30), ForeignKey("machines.machine_id"))
    vin_id: Mapped[str | None] = mapped_column(String(30), nullable=True)
    failure_mode: Mapped[str] = mapped_column(String(10))
    failure_type: Mapped[str] = mapped_column(String(50))
    component_failed: Mapped[str] = mapped_column(String(50))
    severity: Mapped[str] = mapped_column(String(20))
    detected_by: Mapped[str] = mapped_column(String(30))
    failure_start: Mapped[datetime] = mapped_column(DateTime)
    failure_end: Mapped[datetime] = mapped_column(DateTime)
    downtime_min: Mapped[int] = mapped_column(Integer)
    production_units_lost: Mapped[int] = mapped_column(Integer, default=0)
    root_cause: Mapped[str | None] = mapped_column(Text, nullable=True)
    corrective_action: Mapped[str | None] = mapped_column(Text, nullable=True)
    preventive_action: Mapped[str | None] = mapped_column(Text, nullable=True)
    cost_parts: Mapped[float] = mapped_column(Float, default=0.0)
    cost_labor: Mapped[float] = mapped_column(Float, default=0.0)
    cost_lost_production: Mapped[float] = mapped_column(Float, default=0.0)
    linked_wo_id: Mapped[str | None] = mapped_column(String(20), nullable=True)

    machine: Mapped["Machine"] = relationship(back_populates="failures")


class MaintenanceHistory(Base):
    __tablename__ = "maintenance_history"

    maint_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    machine_id: Mapped[str] = mapped_column(String(30), ForeignKey("machines.machine_id"))
    type: Mapped[str] = mapped_column(String(20))
    trigger: Mapped[str] = mapped_column(String(20))
    started_at: Mapped[datetime] = mapped_column(DateTime)
    completed_at: Mapped[datetime] = mapped_column(DateTime)
    duration_min: Mapped[int] = mapped_column(Integer)
    technician_id: Mapped[str] = mapped_column(String(20))
    parts_replaced: Mapped[list] = mapped_column(JSON, default=list)
    labor_hours: Mapped[float] = mapped_column(Float)
    total_cost: Mapped[float] = mapped_column(Float)
    machine_condition_before: Mapped[int] = mapped_column(Integer)
    machine_condition_after: Mapped[int] = mapped_column(Integer)
    wo_id: Mapped[str | None] = mapped_column(String(20), nullable=True)


class WorkOrder(Base):
    __tablename__ = "work_orders"

    wo_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    machine_id: Mapped[str] = mapped_column(String(30), ForeignKey("machines.machine_id"))
    type: Mapped[str] = mapped_column(String(20))
    priority: Mapped[str] = mapped_column(String(20))
    description: Mapped[str] = mapped_column(Text)
    assigned_to: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class SparePartInventory(Base):
    __tablename__ = "spare_parts_inventory"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    part_number: Mapped[str] = mapped_column(String(20))
    description: Mapped[str] = mapped_column(String(200))
    compatible_machines: Mapped[list] = mapped_column(JSON, default=list)
    quantity_on_hand: Mapped[int] = mapped_column(Integer, default=0)
    reorder_point: Mapped[int] = mapped_column(Integer, default=1)
    lead_time_days: Mapped[int] = mapped_column(Integer)
    unit_cost: Mapped[float] = mapped_column(Float)
    location_bin: Mapped[str] = mapped_column(String(20))
    last_used_date: Mapped[date | None] = mapped_column(Date, nullable=True)


# ─── Inventory ─────────────────────────────────────────────────────────────────


class RawMaterialInventory(Base):
    __tablename__ = "raw_material_inventory"

    material_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    description: Mapped[str] = mapped_column(String(200))
    unit: Mapped[str] = mapped_column(String(10))
    quantity: Mapped[int] = mapped_column(Integer)
    reorder_point: Mapped[int] = mapped_column(Integer)
    reorder_qty: Mapped[int] = mapped_column(Integer)
    last_counted: Mapped[date] = mapped_column(Date)


class ConsumablesInventory(Base):
    __tablename__ = "consumables_inventory"

    item_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    station_id: Mapped[str] = mapped_column(String(20))
    description: Mapped[str] = mapped_column(String(200))
    unit: Mapped[str] = mapped_column(String(10))
    quantity: Mapped[int] = mapped_column(Integer)
    min_level: Mapped[int] = mapped_column(Integer)
    usage_rate_per_shift: Mapped[float] = mapped_column(Float)
    cost_per_unit: Mapped[float] = mapped_column(Float)


class FinishedGoods(Base):
    __tablename__ = "finished_goods"

    vin_id: Mapped[str] = mapped_column(String(30), primary_key=True)
    completion_date: Mapped[date] = mapped_column(Date)
    storage_location: Mapped[str | None] = mapped_column(String(20), nullable=True)
    ship_date: Mapped[date | None] = mapped_column(Date, nullable=True)
