import math
from datetime import datetime
from enum import Enum
from urllib.parse import urlsplit
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ScanStatus(str, Enum):
    manual = "manual"
    imported = "imported"


class ObservationSource(str, Enum):
    manual = "manual"
    model = "model"


class AssetType(str, Enum):
    procedural = "procedural"
    glb = "glb"
    gaussian_splat = "gaussian_splat"


def _stripped(value: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError("must not be blank")
    return cleaned


def _coord(value: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("coordinate must be a number")
    number = float(value)
    if not math.isfinite(number) or abs(number) > 10_000:
        raise ValueError("coordinate must be finite and within ±10000 meters")
    return number


def _http_url(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    if cleaned == "":
        return None
    parsed = urlsplit(cleaned)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("must be an absolute http or https URL")
    return cleaned


class SpaceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=4000)

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, value: str) -> str:
        return _stripped(value)


class SpaceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=4000)

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _stripped(value)


class SpaceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime


class SpaceList(BaseModel):
    items: list[SpaceOut]
    total: int
    limit: int
    offset: int


class ZoneCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    parent_zone_id: UUID | None = None

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, value: str) -> str:
        return _stripped(value)


class ZoneOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    space_id: UUID
    name: str
    parent_zone_id: UUID | None
    created_at: datetime


class ZoneList(BaseModel):
    items: list[ZoneOut]
    total: int


class ScanCreate(BaseModel):
    label: str = Field(min_length=1, max_length=200)
    captured_at: datetime | None = None
    status: ScanStatus = ScanStatus.manual
    notes: str | None = Field(default=None, max_length=4000)

    @field_validator("label")
    @classmethod
    def label_not_blank(cls, value: str) -> str:
        return _stripped(value)


class ScanOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    space_id: UUID
    label: str
    captured_at: datetime
    status: ScanStatus
    notes: str | None
    created_at: datetime


class ScanList(BaseModel):
    items: list[ScanOut]
    total: int
    limit: int
    offset: int


class SceneAssetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    scan_id: UUID
    asset_type: AssetType
    storage_uri: str
    metadata_json: str | None
    alignment_json: str | None
    created_at: datetime


class SceneAssetList(BaseModel):
    items: list[SceneAssetOut]


class ObjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    category: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=4000)
    serial_number: str | None = Field(default=None, max_length=120)

    @field_validator("name", "category")
    @classmethod
    def not_blank(cls, value: str) -> str:
        return _stripped(value)

    @field_validator("serial_number")
    @classmethod
    def serial_strip(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class ObjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    category: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=4000)
    serial_number: str | None = Field(default=None, max_length=120)
    archived_at: datetime | None = None

    @field_validator("name", "category")
    @classmethod
    def not_blank(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _stripped(value)

    @field_validator("serial_number")
    @classmethod
    def serial_strip(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class ObjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    space_id: UUID
    name: str
    category: str
    description: str | None
    serial_number: str | None
    created_at: datetime
    updated_at: datetime
    archived_at: datetime | None


class ObservationCreate(BaseModel):
    scan_id: UUID
    zone_id: UUID | None = None
    x: float
    y: float
    z: float
    observed_at: datetime | None = None
    source: ObservationSource = ObservationSource.manual
    confidence: float | None = Field(default=None, ge=0, le=1)
    notes: str | None = Field(default=None, max_length=4000)

    @field_validator("x", "y", "z")
    @classmethod
    def finite_coord(cls, value: float) -> float:
        return _coord(value)


class ObservationUpdate(BaseModel):
    zone_id: UUID | None = None
    x: float | None = None
    y: float | None = None
    z: float | None = None
    observed_at: datetime | None = None
    source: ObservationSource | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)
    notes: str | None = Field(default=None, max_length=4000)
    clear_zone: bool = False

    @field_validator("x", "y", "z")
    @classmethod
    def finite_coord(cls, value: float | None) -> float | None:
        if value is None:
            return None
        return _coord(value)


class ObservationOut(BaseModel):
    id: UUID
    object_id: UUID
    scan_id: UUID
    scan_label: str
    zone_id: UUID | None
    zone_name: str | None
    x: float
    y: float
    z: float
    observed_at: datetime
    source: ObservationSource
    confidence: float | None
    notes: str | None


class ObservationList(BaseModel):
    items: list[ObservationOut]


class ObjectListItem(ObjectOut):
    scan_observation: ObservationOut | None = None


class ObjectList(BaseModel):
    items: list[ObjectListItem]
    total: int
    limit: int
    offset: int
    scan_id: UUID | None = None


class AnnotationCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    body: str = Field(min_length=1, max_length=8000)
    external_url: str | None = Field(default=None, max_length=2000)

    @field_validator("title", "body")
    @classmethod
    def not_blank(cls, value: str) -> str:
        return _stripped(value)

    @field_validator("external_url")
    @classmethod
    def url_ok(cls, value: str | None) -> str | None:
        return _http_url(value)


class AnnotationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    object_id: UUID
    title: str
    body: str
    external_url: str | None
    created_at: datetime
    updated_at: datetime


class AnnotationList(BaseModel):
    items: list[AnnotationOut]
