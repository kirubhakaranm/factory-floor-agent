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
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Declarative base class for all SQLAlchemy ORM models."""


# ─── Factory ───────────────────────────────────────────────────────────────────


class Line(Base):
    """A named production line grouping stations within a manufacturing stage."""

    __tablename__ = "lines"

    line_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    stage: Mapped[str] = mapped_column(String(10))
    name: Mapped[str] = mapped_column(String(50))

    stations: Mapped[list["Station"]] = relationship(back_populates="line")


class Station(Base):
    """A production station at a specific position on a line."""

    __tablename__ = "stations"

    station_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    stage: Mapped[str] = mapped_column(String(10))
    name: Mapped[str] = mapped_column(String(50))
    position: Mapped[int] = mapped_column(Integer)
    line_id: Mapped[str] = mapped_column(String(20), ForeignKey("lines.line_id"))

    line: Mapped["Line"] = relationship(back_populates="stations")
    machines: Mapped[list["Machine"]] = relationship(back_populates="station")


class Machine(Base):
    """A physical machine asset assigned to a station with maintenance tracking."""

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
    """A factory floor operator with certifications and shift assignment."""

    __tablename__ = "operators"

    operator_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    shift: Mapped[str] = mapped_column(String(20))
    crew_id: Mapped[str] = mapped_column(String(20))
    certifications: Mapped[list] = mapped_column(JSON, default=list)
    hire_date: Mapped[date | None] = mapped_column(Date, nullable=True)


class Technician(Base):
    """A maintenance technician with specializations and shift assignment."""

    __tablename__ = "technicians"

    tech_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    shift: Mapped[str] = mapped_column(String(20))
    specializations: Mapped[list] = mapped_column(JSON, default=list)


class Crew(Base):
    """A named crew group assigned to a shift with a designated supervisor."""

    __tablename__ = "crews"

    crew_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    shift_name: Mapped[str] = mapped_column(String(20))
    supervisor_id: Mapped[str] = mapped_column(String(20))


class Shift(Base):
    """A scheduled shift record linking a date, time window, and crew assignment."""

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
    """A vehicle model variant produced at the factory."""

    __tablename__ = "vehicle_models"

    model_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    year: Mapped[int] = mapped_column(Integer)
    variant: Mapped[str] = mapped_column(String(20))


class Component(Base):
    """A unique part number with supplier, category, and cost attributes."""

    __tablename__ = "components"

    component_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    part_number: Mapped[str] = mapped_column(String(30), unique=True)
    description: Mapped[str] = mapped_column(String(200))
    category: Mapped[str] = mapped_column(String(10))
    station_id: Mapped[str] = mapped_column(String(20))
    supplier_id: Mapped[str] = mapped_column(String(20))
    unit_cost: Mapped[float] = mapped_column(Float)


class BillOfMaterials(Base):
    """Association between a vehicle model and the parts it requires at each station."""

    __tablename__ = "bill_of_materials"

    bom_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    model_id: Mapped[str] = mapped_column(String(20), ForeignKey("vehicle_models.model_id"))
    part_number: Mapped[str] = mapped_column(String(30))
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    station_id: Mapped[str] = mapped_column(String(20))


class VinRegistry(Base):
    """Registry of every manufactured vehicle identified by VIN."""

    __tablename__ = "vin_registry"

    vin_id: Mapped[str] = mapped_column(String(30), primary_key=True)
    model_id: Mapped[str] = mapped_column(String(20), ForeignKey("vehicle_models.model_id"))
    batch_id: Mapped[str] = mapped_column(String(20), nullable=True)
    production_date: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(20), default="completed")


# ─── Supply Chain ──────────────────────────────────────────────────────────────


class Supplier(Base):
    """An external supplier providing raw materials or components."""

    __tablename__ = "suppliers"

    supplier_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    category: Mapped[str] = mapped_column(String(50))
    rating: Mapped[float] = mapped_column(Float, default=4.0)
    lead_time_days: Mapped[int] = mapped_column(Integer, default=7)


class RawMaterial(Base):
    """A raw material master record linking a part number to its supplier."""

    __tablename__ = "raw_materials"

    material_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    supplier_id: Mapped[str] = mapped_column(String(20), ForeignKey("suppliers.supplier_id"))
    part_number: Mapped[str] = mapped_column(String(30))
    description: Mapped[str] = mapped_column(String(200))


class ReceivingInspection(Base):
    """Record of an incoming lot inspection at the receiving dock."""

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
    """Monthly quality and delivery performance scorecard for a supplier."""

    __tablename__ = "supplier_scorecards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    supplier_id: Mapped[str] = mapped_column(String(20), ForeignKey("suppliers.supplier_id"))
    month: Mapped[date] = mapped_column(Date)
    defect_ppm: Mapped[float] = mapped_column(Float)
    on_time_pct: Mapped[float] = mapped_column(Float)
    quality_score: Mapped[float] = mapped_column(Float)
    delivery_score: Mapped[float] = mapped_column(Float)
    overall_grade: Mapped[str] = mapped_column(String(5))
    lot_count: Mapped[int] = mapped_column(Integer, default=0)


class SupplierNcr(Base):
    """A non-conformance report raised against a supplier lot."""

    __tablename__ = "supplier_ncrs"

    ncr_id: Mapped[str] = mapped_column(String(30), primary_key=True)
    supplier_id: Mapped[str] = mapped_column(String(20), ForeignKey("suppliers.supplier_id"))
    lot_id: Mapped[str] = mapped_column(String(50))
    issue: Mapped[str] = mapped_column(Text)
    disposition: Mapped[str] = mapped_column(String(20))
    date: Mapped[date] = mapped_column(Date)


# ─── Production ────────────────────────────────────────────────────────────────


class ProductionOrder(Base):
    """A planned production order for a specific vehicle model and quantity."""

    __tablename__ = "production_orders"

    po_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    model_id: Mapped[str] = mapped_column(String(20), ForeignKey("vehicle_models.model_id"))
    quantity: Mapped[int] = mapped_column(Integer)
    priority: Mapped[str] = mapped_column(String(20), default="normal")
    due_date: Mapped[date] = mapped_column(Date)


class ProductionBatch(Base):
    """A completed production batch with unit counts and yield on a line."""

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
    """A single dimensional measurement result at a station, linked to a spec and optional VIN."""

    __tablename__ = "dimensional_inspections"

    insp_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    vin_id: Mapped[str | None] = mapped_column(String(30), nullable=True)
    station_id: Mapped[str] = mapped_column(String(20))
    measurement_name: Mapped[str] = mapped_column(String(50))
    spec_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("measurement_specs.spec_id"), nullable=True)
    nominal: Mapped[float] = mapped_column(Float)
    upper_tol: Mapped[float] = mapped_column(Float)
    lower_tol: Mapped[float] = mapped_column(Float)
    actual_value: Mapped[float] = mapped_column(Float)
    result: Mapped[str] = mapped_column(String(10))
    timestamp: Mapped[datetime] = mapped_column(DateTime)


class SamplingInspection(Base):
    """AQL-based sampling inspection result for an incoming or in-process lot."""

    __tablename__ = "sampling_inspections"

    insp_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    station_id: Mapped[str] = mapped_column(String(20))
    lot_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
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
    """Visual inspection checklist results per unit at a gate station."""

    __tablename__ = "visual_checklists"

    checklist_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    vin_id: Mapped[str | None] = mapped_column(String(30), nullable=True)
    station_id: Mapped[str] = mapped_column(String(20))
    checkpoint_items: Mapped[dict] = mapped_column(JSON)
    defect_category: Mapped[str] = mapped_column(String(20))
    timestamp: Mapped[datetime] = mapped_column(DateTime)


class ReworkRecord(Base):
    """Record of a rework event triggered by a failed dimensional inspection."""

    __tablename__ = "rework_records"

    rework_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    vin_id: Mapped[str | None] = mapped_column(String(30), nullable=True)
    station_id: Mapped[str] = mapped_column(String(20))
    defect_type: Mapped[str] = mapped_column(String(50))
    rework_action: Mapped[str] = mapped_column(Text)
    rework_time_min: Mapped[int] = mapped_column(Integer)
    re_inspect_result: Mapped[str] = mapped_column(String(10))
    cost: Mapped[float] = mapped_column(Float)
    timestamp: Mapped[datetime] = mapped_column(DateTime)


class ScrapRecord(Base):
    """Record of a unit scrapped due to an unrecoverable defect."""

    __tablename__ = "scrap_records"

    scrap_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    vin_id: Mapped[str | None] = mapped_column(String(30), nullable=True)
    station_id: Mapped[str] = mapped_column(String(20))
    reason: Mapped[str] = mapped_column(Text)
    cost: Mapped[float] = mapped_column(Float)
    timestamp: Mapped[datetime] = mapped_column(DateTime)


class DeviationRecord(Base):
    """An approved deviation allowing a non-conforming unit to continue production."""

    __tablename__ = "deviation_records"

    dev_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    vin_id: Mapped[str | None] = mapped_column(String(30), nullable=True)
    mrb_approval: Mapped[str] = mapped_column(String(50))
    justification: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    reviewed_by: Mapped[str | None] = mapped_column(String(50), nullable=True)
    disposition_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="open")


# ─── Equipment ─────────────────────────────────────────────────────────────────


class EquipmentFailure(Base):
    """An equipment failure event with downtime, costs, and corrective action details."""

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
    """A completed preventive or corrective maintenance event for a machine."""

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
    """A work order directing a technician to carry out a corrective or preventive task."""

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
    """Spare part stock record with compatible machines, reorder point, and bin location."""

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
    """Current stock snapshot for a raw material with reorder thresholds."""

    __tablename__ = "raw_material_inventory"

    material_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    description: Mapped[str] = mapped_column(String(200))
    unit: Mapped[str] = mapped_column(String(10))
    quantity: Mapped[int] = mapped_column(Integer)
    reorder_point: Mapped[int] = mapped_column(Integer)
    reorder_qty: Mapped[int] = mapped_column(Integer)
    last_counted: Mapped[date] = mapped_column(Date)


class ConsumablesInventory(Base):
    """Current stock of a consumable item at a specific station."""

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
    """Finished vehicle awaiting shipment, keyed by VIN."""

    __tablename__ = "finished_goods"

    vin_id: Mapped[str] = mapped_column(String(30), primary_key=True)
    completion_date: Mapped[date] = mapped_column(Date)
    storage_location: Mapped[str | None] = mapped_column(String(20), nullable=True)
    ship_date: Mapped[date | None] = mapped_column(Date, nullable=True)


# ─── New normalized / traceability tables ─────────────────────────────────────


class MeasurementSpec(Base):
    """Master spec table for dimensional measurement parameters.
    Normalizes nominal/tolerance out of dimensional_inspections (26K rows → 300 rows).
    Enables spec revision history via effective_date / superseded_date.
    """
    __tablename__ = "measurement_specs"
    __table_args__ = (
        UniqueConstraint("station_id", "measurement_name", "effective_date",
                         name="uq_measurement_spec"),
    )

    spec_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    station_id: Mapped[str] = mapped_column(String(20), ForeignKey("stations.station_id"))
    measurement_name: Mapped[str] = mapped_column(String(50))
    nominal: Mapped[float] = mapped_column(Float)
    upper_tol: Mapped[float] = mapped_column(Float)
    lower_tol: Mapped[float] = mapped_column(Float)
    usl: Mapped[float | None] = mapped_column(Float, nullable=True)
    lsl: Mapped[float | None] = mapped_column(Float, nullable=True)
    effective_date: Mapped[date] = mapped_column(Date)
    superseded_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    drawing_ref: Mapped[str | None] = mapped_column(String(50), nullable=True)


class ComponentConsumption(Base):
    """Daily component-level consumption per production batch.
    Closes the traceability gap: supplier lot → receiving inspection →
    component_consumption → production_batch → vin_registry.
    """
    __tablename__ = "component_consumption"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    batch_id: Mapped[str] = mapped_column(String(20), ForeignKey("production_batches.batch_id"))
    consumed_date: Mapped[date] = mapped_column(Date)
    station_id: Mapped[str] = mapped_column(String(20))
    part_number: Mapped[str] = mapped_column(String(30))
    model_id: Mapped[str] = mapped_column(String(20))
    lot_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    qty_consumed: Mapped[int] = mapped_column(Integer)
    shift: Mapped[str | None] = mapped_column(String(20), nullable=True)


class InventoryTransaction(Base):
    """Unified inventory movement log — raw materials, consumables, spare parts.
    Enables date-based RCA: 'what material was consumed on date X at station Y?'
    qty_change > 0 = receipt/replenishment; qty_change < 0 = issue/consumption.
    """
    __tablename__ = "inventory_transactions"

    txn_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    txn_datetime: Mapped[datetime] = mapped_column(DateTime)
    item_type: Mapped[str] = mapped_column(String(20))   # raw_material / consumable / spare_part
    item_id: Mapped[str] = mapped_column(String(30))
    station_id: Mapped[str | None] = mapped_column(String(20), nullable=True)
    qty_change: Mapped[int] = mapped_column(Integer)
    reason: Mapped[str] = mapped_column(String(50))      # production / maintenance / replenishment / adjustment
    ref_id: Mapped[str | None] = mapped_column(String(30), nullable=True)   # WO / batch / PO id
    performed_by: Mapped[str | None] = mapped_column(String(30), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


# ─── Quality Master Data ────────────────────────────────────────────────────────


class DefectCode(Base):
    """Master catalog of all named defects per station.
    Replaces hardcoded STATION_DEFECTS strings with queryable rows that carry
    category, severity, and detection method — enabling structured RCA filters.
    """
    __tablename__ = "defect_codes"

    defect_code: Mapped[str] = mapped_column(String(30), primary_key=True)
    name: Mapped[str] = mapped_column(String(60))
    stage: Mapped[str] = mapped_column(String(10))
    station_id: Mapped[str] = mapped_column(String(20), ForeignKey("stations.station_id"))
    category: Mapped[str] = mapped_column(String(20))        # structural / cosmetic / functional / safety
    severity: Mapped[str] = mapped_column(String(10))        # critical / major / minor
    detection_method: Mapped[str] = mapped_column(String(30))  # dimensional / visual / spc / functional
    description: Mapped[str | None] = mapped_column(Text, nullable=True)


class InspectionPlan(Base):
    """Per-station inspection plan: what to check, how, and how often.
    Formalizes the implicit logic in the quality generator into queryable rows.
    Enables: 'What is the inspection plan for STP-01-PRS?' queries.
    """
    __tablename__ = "inspection_plans"

    plan_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    station_id: Mapped[str] = mapped_column(String(20), ForeignKey("stations.station_id"))
    characteristic_name: Mapped[str] = mapped_column(String(60))
    inspection_type: Mapped[str] = mapped_column(String(20))    # dimensional / visual / spc / functional / sampling
    measurement_method: Mapped[str] = mapped_column(String(40))
    frequency: Mapped[str] = mapped_column(String(20))          # every_unit / first_off / hourly / aql_sample / per_batch
    sample_size_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    spec_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("measurement_specs.spec_id"), nullable=True)
    control_chart_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    responsible_role: Mapped[str] = mapped_column(String(30))   # operator / quality_tech / engineer


class AqlScheme(Base):
    """ISO 2859-1–inspired AQL sampling table.
    Maps lot size range + inspection level to sample size and accept/reject numbers.
    Enables the quality agent to justify accept/reject decisions with a data source.
    """
    __tablename__ = "aql_schemes"

    scheme_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    inspection_level: Mapped[str] = mapped_column(String(20))   # normal / tightened / reduced
    aql_percent: Mapped[float] = mapped_column(Float)
    lot_size_min: Mapped[int] = mapped_column(Integer)
    lot_size_max: Mapped[int] = mapped_column(Integer)
    sample_size: Mapped[int] = mapped_column(Integer)
    accept_number: Mapped[int] = mapped_column(Integer)
    reject_number: Mapped[int] = mapped_column(Integer)
    sample_code: Mapped[str | None] = mapped_column(String(5), nullable=True)  # ISO code letter (E, F, G…)


# ─── Agent Telemetry ──────────────────────────────────────────────────────────


class AgentSession(Base):
    """Rolled-up cost and usage totals per chat session."""
    __tablename__ = "agent_sessions"

    session_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    total_cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    total_input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    total_output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    total_tool_calls: Mapped[int] = mapped_column(Integer, default=0)
    turn_count: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[datetime] = mapped_column(DateTime)
    last_active_at: Mapped[datetime] = mapped_column(DateTime)

    interactions: Mapped[list["AgentInteraction"]] = relationship(back_populates="session")


class AgentInteraction(Base):
    """One row per chat turn — latency, token usage, cost, routing, and error signals."""
    __tablename__ = "agent_interactions"

    interaction_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    session_id: Mapped[str] = mapped_column(String(50), ForeignKey("agent_sessions.session_id"))
    turn_number: Mapped[int] = mapped_column(Integer)
    user_query: Mapped[str] = mapped_column(Text)
    sub_agent_invoked: Mapped[str] = mapped_column(String(50))
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    cache_read_tokens: Mapped[int] = mapped_column(Integer, default=0)
    cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    ttft_ms: Mapped[int] = mapped_column(Integer, default=0)
    total_latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    llm_latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    tool_latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    llm_reentry_count: Mapped[int] = mapped_column(Integer, default=0)
    tool_call_count: Mapped[int] = mapped_column(Integer, default=0)
    context_tokens_used: Mapped[int] = mapped_column(Integer, default=0)
    response_length_chars: Mapped[int] = mapped_column(Integer, default=0)
    asked_clarification: Mapped[bool] = mapped_column(Boolean, default=False)
    had_terminal_error: Mapped[bool] = mapped_column(Boolean, default=False)
    error_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime)

    session: Mapped["AgentSession"] = relationship(back_populates="interactions")
    tool_calls: Mapped[list["AgentToolCall"]] = relationship(back_populates="interaction")


class AgentToolCall(Base):
    """One row per tool call within an interaction — the queryable trajectory."""
    __tablename__ = "agent_tool_calls"

    tool_call_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    interaction_id: Mapped[str] = mapped_column(String(50), ForeignKey("agent_interactions.interaction_id"))
    sequence_position: Mapped[int] = mapped_column(Integer)
    tool_name: Mapped[str] = mapped_column(String(100))
    sub_agent: Mapped[str] = mapped_column(String(50))
    parameters: Mapped[dict] = mapped_column(JSON)
    result_snippet: Mapped[str | None] = mapped_column(Text, nullable=True)
    result_token_count: Mapped[int] = mapped_column(Integer, default=0)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    had_error: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime)

    interaction: Mapped["AgentInteraction"] = relationship(back_populates="tool_calls")
