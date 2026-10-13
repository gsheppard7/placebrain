import enum

from sqlalchemy import CheckConstraint, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import UTCDateTime, Base, new_id, utcnow


class ScanStatus(str, enum.Enum):
    manual = "manual"
    imported = "imported"


class ObservationSource(str, enum.Enum):
    manual = "manual"
    model = "model"


class AssetType(str, enum.Enum):
    procedural = "procedural"
    glb = "glb"
    gaussian_splat = "gaussian_splat"


class Space(Base):
    __tablename__ = "spaces"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[object] = mapped_column(UTCDateTime, default=utcnow, nullable=False)
    updated_at: Mapped[object] = mapped_column(UTCDateTime, default=utcnow, nullable=False)

    zones: Mapped[list["Zone"]] = relationship(back_populates="space")
    scans: Mapped[list["Scan"]] = relationship(back_populates="space")
    objects: Mapped[list["InventoryObject"]] = relationship(back_populates="space")


class Zone(Base):
    __tablename__ = "zones"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    space_id: Mapped[str] = mapped_column(ForeignKey("spaces.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    parent_zone_id: Mapped[str | None] = mapped_column(ForeignKey("zones.id"), nullable=True)
    created_at: Mapped[object] = mapped_column(UTCDateTime, default=utcnow, nullable=False)

    space: Mapped[Space] = relationship(back_populates="zones")
    parent: Mapped["Zone | None"] = relationship(remote_side=[id], back_populates="children")
    children: Mapped[list["Zone"]] = relationship(back_populates="parent")


class Scan(Base):
    __tablename__ = "scans"
    __table_args__ = (CheckConstraint("status in ('manual', 'imported')", name="ck_scans_status"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    space_id: Mapped[str] = mapped_column(ForeignKey("spaces.id"), nullable=False, index=True)
    label: Mapped[str] = mapped_column(String(200), nullable=False)
    captured_at: Mapped[object] = mapped_column(UTCDateTime, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default=ScanStatus.manual.value)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[object] = mapped_column(UTCDateTime, default=utcnow, nullable=False)

    space: Mapped[Space] = relationship(back_populates="scans")
    assets: Mapped[list["SceneAsset"]] = relationship(back_populates="scan")


class SceneAsset(Base):
    __tablename__ = "scene_assets"
    __table_args__ = (
        CheckConstraint(
            "asset_type in ('procedural', 'glb', 'gaussian_splat')",
            name="ck_scene_assets_type",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    scan_id: Mapped[str] = mapped_column(ForeignKey("scans.id"), nullable=False, index=True)
    asset_type: Mapped[str] = mapped_column(String(32), nullable=False)
    storage_uri: Mapped[str] = mapped_column(String(1000), nullable=False)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    alignment_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[object] = mapped_column(UTCDateTime, default=utcnow, nullable=False)

    scan: Mapped[Scan] = relationship(back_populates="assets")


class InventoryObject(Base):
    __tablename__ = "inventory_objects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    space_id: Mapped[str] = mapped_column(ForeignKey("spaces.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    serial_number: Mapped[str | None] = mapped_column(String(120), nullable=True)
    created_at: Mapped[object] = mapped_column(UTCDateTime, default=utcnow, nullable=False)
    updated_at: Mapped[object] = mapped_column(UTCDateTime, default=utcnow, nullable=False)
    archived_at: Mapped[object | None] = mapped_column(UTCDateTime, nullable=True)

    space: Mapped[Space] = relationship(back_populates="objects")
    observations: Mapped[list["ObjectObservation"]] = relationship(back_populates="object")
    annotations: Mapped[list["Annotation"]] = relationship(back_populates="object")


class ObjectObservation(Base):
    __tablename__ = "object_observations"
    __table_args__ = (CheckConstraint("source in ('manual', 'model')", name="ck_observations_source"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    object_id: Mapped[str] = mapped_column(ForeignKey("inventory_objects.id"), nullable=False, index=True)
    scan_id: Mapped[str] = mapped_column(ForeignKey("scans.id"), nullable=False, index=True)
    zone_id: Mapped[str | None] = mapped_column(ForeignKey("zones.id"), nullable=True)
    x: Mapped[float] = mapped_column(Float, nullable=False)
    y: Mapped[float] = mapped_column(Float, nullable=False)
    z: Mapped[float] = mapped_column(Float, nullable=False)
    observed_at: Mapped[object] = mapped_column(UTCDateTime, nullable=False)
    source: Mapped[str] = mapped_column(String(32), nullable=False, default=ObservationSource.manual.value)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    object: Mapped[InventoryObject] = relationship(back_populates="observations")
    scan: Mapped[Scan] = relationship()
    zone: Mapped[Zone | None] = relationship()


class Annotation(Base):
    __tablename__ = "annotations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    object_id: Mapped[str] = mapped_column(ForeignKey("inventory_objects.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    external_url: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    created_at: Mapped[object] = mapped_column(UTCDateTime, default=utcnow, nullable=False)
    updated_at: Mapped[object] = mapped_column(UTCDateTime, default=utcnow, nullable=False)

    object: Mapped[InventoryObject] = relationship(back_populates="annotations")
