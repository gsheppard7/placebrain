from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.database import new_id, utcnow
from app.errors import DomainError
from app.models import (
    Annotation,
    AssetType,
    InventoryObject,
    ObjectObservation,
    Scan,
    SceneAsset,
    Space,
    Zone,
)
from app.schemas import (
    AnnotationCreate,
    AnnotationOut,
    ObjectCreate,
    ObjectList,
    ObjectListItem,
    ObjectUpdate,
    ObservationCreate,
    ObservationOut,
    ObservationUpdate,
    ScanCreate,
    ScanOut,
    SceneAssetOut,
    SpaceCreate,
    SpaceOut,
    ZoneCreate,
    ZoneOut,
)


def _space_or_404(db: Session, space_id: UUID) -> Space:
    space = db.get(Space, str(space_id))
    if space is None:
        raise DomainError("Space not found", 404)
    return space


def _object_or_404(db: Session, object_id: UUID) -> InventoryObject:
    obj = db.get(InventoryObject, str(object_id))
    if obj is None:
        raise DomainError("Object not found", 404)
    return obj


def _scan_or_404(db: Session, scan_id: UUID) -> Scan:
    scan = db.get(Scan, str(scan_id))
    if scan is None:
        raise DomainError("Scan not found", 404)
    return scan


def _require_same_space(label: str, expected: str, actual: str) -> None:
    if expected != actual:
        raise DomainError(f"{label} belongs to a different space")


def observation_out(obs: ObjectObservation) -> ObservationOut:
    return ObservationOut(
        id=obs.id,
        object_id=obs.object_id,
        scan_id=obs.scan_id,
        scan_label=obs.scan.label,
        zone_id=obs.zone_id,
        zone_name=obs.zone.name if obs.zone is not None else None,
        x=obs.x,
        y=obs.y,
        z=obs.z,
        observed_at=obs.observed_at,
        source=obs.source,
        confidence=obs.confidence,
        notes=obs.notes,
    )


def _load_observation(db: Session, observation_id: str) -> ObjectObservation | None:
    return db.scalar(
        select(ObjectObservation)
        .options(joinedload(ObjectObservation.scan), joinedload(ObjectObservation.zone))
        .where(ObjectObservation.id == observation_id)
    )


def list_spaces(db: Session, limit: int, offset: int) -> tuple[list[Space], int]:
    total = db.scalar(select(func.count()).select_from(Space)) or 0
    rows = db.scalars(select(Space).order_by(Space.created_at).limit(limit).offset(offset)).all()
    return list(rows), total


def create_space(db: Session, payload: SpaceCreate) -> Space:
    now = utcnow()
    space = Space(name=payload.name, description=payload.description, created_at=now, updated_at=now)
    db.add(space)
    db.commit()
    db.refresh(space)
    return space


def get_space(db: Session, space_id: UUID) -> Space:
    return _space_or_404(db, space_id)


def list_zones(db: Session, space_id: UUID) -> list[Zone]:
    _space_or_404(db, space_id)
    return list(
        db.scalars(select(Zone).where(Zone.space_id == str(space_id)).order_by(Zone.name)).all()
    )


def _assert_zone_parent(db: Session, space_id: str, parent_id: UUID | None, zone_id: str | None = None) -> None:
    if parent_id is None:
        return
    parent = db.get(Zone, str(parent_id))
    if parent is None or parent.space_id != space_id:
        raise DomainError("Parent zone is not in this space")
    if zone_id is not None and parent.id == zone_id:
        raise DomainError("Zone cannot be its own parent")
    seen: set[str] = set()
    current: Zone | None = parent
    while current is not None:
        if current.id in seen or (zone_id is not None and current.id == zone_id):
            raise DomainError("Zone parent cycle")
        seen.add(current.id)
        current = db.get(Zone, current.parent_zone_id) if current.parent_zone_id else None


def create_zone(db: Session, space_id: UUID, payload: ZoneCreate) -> Zone:
    space = _space_or_404(db, space_id)
    _assert_zone_parent(db, space.id, payload.parent_zone_id)
    zone = Zone(
        space_id=space.id,
        name=payload.name,
        parent_zone_id=str(payload.parent_zone_id) if payload.parent_zone_id else None,
        created_at=utcnow(),
    )
    db.add(zone)
    db.commit()
    db.refresh(zone)
    return zone


def list_scans(db: Session, space_id: UUID, limit: int, offset: int) -> tuple[list[Scan], int]:
    _space_or_404(db, space_id)
    filters = Scan.space_id == str(space_id)
    total = db.scalar(select(func.count()).select_from(Scan).where(filters)) or 0
    rows = db.scalars(
        select(Scan).where(filters).order_by(Scan.captured_at.desc()).limit(limit).offset(offset)
    ).all()
    return list(rows), total


def create_scan(db: Session, space_id: UUID, payload: ScanCreate) -> Scan:
    space = _space_or_404(db, space_id)
    now = utcnow()
    scan = Scan(
        space_id=space.id,
        label=payload.label,
        captured_at=payload.captured_at or now,
        status=payload.status.value,
        notes=payload.notes,
        created_at=now,
    )
    db.add(scan)
    db.flush()
    db.add(
        SceneAsset(
            scan_id=scan.id,
            asset_type=AssetType.procedural.value,
            storage_uri="procedural://demo-room-v1",
            metadata_json=(
                '{"frame":"demo-room-v1","units":"meters","up":"Y","handedness":"right",'
                '"note":"Procedural room attached because no imported scene was provided. alignment_json is null."}'
            ),
            alignment_json=None,
            created_at=now,
        )
    )
    db.commit()
    db.refresh(scan)
    return scan


def list_assets(db: Session, scan_id: UUID) -> list[SceneAsset]:
    _scan_or_404(db, scan_id)
    return list(
        db.scalars(select(SceneAsset).where(SceneAsset.scan_id == str(scan_id)).order_by(SceneAsset.created_at)).all()
    )


def _like_pattern(query: str) -> str:
    escaped = query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


def list_objects(
    db: Session,
    space_id: UUID,
    q: str | None,
    scan_id: UUID | None,
    include_archived: bool,
    limit: int,
    offset: int,
) -> ObjectList:
    _space_or_404(db, space_id)
    scan: Scan | None = None
    if scan_id is not None:
        scan = _scan_or_404(db, scan_id)
        _require_same_space("Scan", str(space_id), scan.space_id)

    filters = [InventoryObject.space_id == str(space_id)]
    if not include_archived:
        filters.append(InventoryObject.archived_at.is_(None))
    if q and q.strip():
        pattern = _like_pattern(q.strip())
        filters.append(
            or_(
                InventoryObject.name.ilike(pattern, escape="\\"),
                InventoryObject.category.ilike(pattern, escape="\\"),
                InventoryObject.description.ilike(pattern, escape="\\"),
            )
        )
    total = db.scalar(select(func.count()).select_from(InventoryObject).where(*filters)) or 0
    rows = list(
        db.scalars(
            select(InventoryObject)
            .where(*filters)
            .order_by(InventoryObject.category, InventoryObject.name)
            .limit(limit)
            .offset(offset)
        ).all()
    )
    latest: dict[str, ObjectObservation] = {}
    if scan is not None and rows:
        ids = [row.id for row in rows]
        observations = db.scalars(
            select(ObjectObservation)
            .options(joinedload(ObjectObservation.scan), joinedload(ObjectObservation.zone))
            .where(ObjectObservation.scan_id == scan.id, ObjectObservation.object_id.in_(ids))
        ).all()
        for obs in observations:
            current = latest.get(obs.object_id)
            if current is None or (obs.observed_at, obs.id) > (current.observed_at, current.id):
                latest[obs.object_id] = obs

    items = [
        ObjectListItem(
            id=row.id,
            space_id=row.space_id,
            name=row.name,
            category=row.category,
            description=row.description,
            serial_number=row.serial_number,
            created_at=row.created_at,
            updated_at=row.updated_at,
            archived_at=row.archived_at,
            scan_observation=observation_out(latest[row.id]) if row.id in latest else None,
        )
        for row in rows
    ]
    return ObjectList(items=items, total=total, limit=limit, offset=offset, scan_id=scan_id)


def create_object(db: Session, space_id: UUID, payload: ObjectCreate) -> InventoryObject:
    space = _space_or_404(db, space_id)
    now = utcnow()
    obj = InventoryObject(
        space_id=space.id,
        name=payload.name,
        category=payload.category,
        description=payload.description,
        serial_number=payload.serial_number,
        created_at=now,
        updated_at=now,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def get_object(db: Session, object_id: UUID) -> InventoryObject:
    return _object_or_404(db, object_id)


def update_object(db: Session, object_id: UUID, payload: ObjectUpdate) -> InventoryObject:
    obj = _object_or_404(db, object_id)
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(obj, key, value)
    obj.updated_at = utcnow()
    db.commit()
    db.refresh(obj)
    return obj


def _zone_for_space(db: Session, space_id: str, zone_id: UUID | None) -> str | None:
    if zone_id is None:
        return None
    zone = db.get(Zone, str(zone_id))
    if zone is None:
        raise DomainError("Zone not found", 404)
    _require_same_space("Zone", space_id, zone.space_id)
    return zone.id


def list_observations(db: Session, object_id: UUID) -> list[ObservationOut]:
    _object_or_404(db, object_id)
    rows = db.scalars(
        select(ObjectObservation)
        .options(joinedload(ObjectObservation.scan), joinedload(ObjectObservation.zone))
        .where(ObjectObservation.object_id == str(object_id))
        .order_by(ObjectObservation.observed_at.desc(), ObjectObservation.id.desc())
    ).all()
    return [observation_out(row) for row in rows]


def create_observation(db: Session, object_id: UUID, payload: ObservationCreate) -> ObservationOut:
    obj = _object_or_404(db, object_id)
    scan = _scan_or_404(db, payload.scan_id)
    _require_same_space("Scan", obj.space_id, scan.space_id)
    zone_id = _zone_for_space(db, obj.space_id, payload.zone_id)
    obs = ObjectObservation(
        id=new_id(),
        object_id=obj.id,
        scan_id=scan.id,
        zone_id=zone_id,
        x=payload.x,
        y=payload.y,
        z=payload.z,
        observed_at=payload.observed_at or utcnow(),
        source=payload.source.value,
        confidence=payload.confidence,
        notes=payload.notes,
    )
    db.add(obs)
    db.commit()
    loaded = _load_observation(db, obs.id)
    assert loaded is not None
    return observation_out(loaded)


def update_observation(db: Session, observation_id: UUID, payload: ObservationUpdate) -> ObservationOut:
    obs = _load_observation(db, str(observation_id))
    if obs is None:
        raise DomainError("Observation not found", 404)
    data = payload.model_dump(exclude_unset=True)
    clear_zone = data.pop("clear_zone", False)
    obj = db.get(InventoryObject, obs.object_id)
    if obj is None:
        raise DomainError("Object not found", 404)
    if "zone_id" in data or clear_zone:
        zone_value = None if clear_zone else data.get("zone_id")
        obs.zone_id = _zone_for_space(db, obj.space_id, zone_value)
    for key in ("x", "y", "z", "observed_at", "confidence", "notes"):
        if key in data:
            setattr(obs, key, data[key])
    if "source" in data and data["source"] is not None:
        obs.source = data["source"].value
    db.commit()
    loaded = _load_observation(db, obs.id)
    assert loaded is not None
    return observation_out(loaded)


def list_annotations(db: Session, object_id: UUID) -> list[Annotation]:
    _object_or_404(db, object_id)
    return list(
        db.scalars(
            select(Annotation)
            .where(Annotation.object_id == str(object_id))
            .order_by(Annotation.created_at.desc())
        ).all()
    )


def create_annotation(db: Session, object_id: UUID, payload: AnnotationCreate) -> Annotation:
    obj = _object_or_404(db, object_id)
    now = utcnow()
    note = Annotation(
        object_id=obj.id,
        title=payload.title,
        body=payload.body,
        external_url=payload.external_url,
        created_at=now,
        updated_at=now,
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


def space_out(space: Space) -> SpaceOut:
    return SpaceOut.model_validate(space)


def zone_out(zone: Zone) -> ZoneOut:
    return ZoneOut.model_validate(zone)


def scan_out(scan: Scan) -> ScanOut:
    return ScanOut.model_validate(scan)


def asset_out(asset: SceneAsset) -> SceneAssetOut:
    return SceneAssetOut.model_validate(asset)


def annotation_out(note: Annotation) -> AnnotationOut:
    return AnnotationOut.model_validate(note)
