from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import (
    ObjectCreate,
    ObjectList,
    ScanCreate,
    ScanList,
    ScanOut,
    SpaceCreate,
    SpaceList,
    SpaceOut,
    ZoneCreate,
    ZoneList,
    ZoneOut,
)
from app.services import (
    create_object,
    create_scan,
    create_space,
    create_zone,
    get_space,
    list_objects,
    list_scans,
    list_spaces,
    list_zones,
    scan_out,
    space_out,
    zone_out,
)
from app.schemas import ObjectOut

router = APIRouter(tags=["spaces"])


@router.get("/spaces", response_model=SpaceList)
def get_spaces(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> SpaceList:
    rows, total = list_spaces(db, limit, offset)
    return SpaceList(items=[space_out(row) for row in rows], total=total, limit=limit, offset=offset)


@router.post("/spaces", response_model=SpaceOut, status_code=201)
def post_space(payload: SpaceCreate, db: Session = Depends(get_db)) -> SpaceOut:
    return space_out(create_space(db, payload))


@router.get("/spaces/{space_id}", response_model=SpaceOut)
def get_space_by_id(space_id: UUID, db: Session = Depends(get_db)) -> SpaceOut:
    return space_out(get_space(db, space_id))


@router.get("/spaces/{space_id}/zones", response_model=ZoneList)
def get_zones(space_id: UUID, db: Session = Depends(get_db)) -> ZoneList:
    rows = list_zones(db, space_id)
    return ZoneList(items=[zone_out(row) for row in rows], total=len(rows))


@router.post("/spaces/{space_id}/zones", response_model=ZoneOut, status_code=201)
def post_zone(space_id: UUID, payload: ZoneCreate, db: Session = Depends(get_db)) -> ZoneOut:
    return zone_out(create_zone(db, space_id, payload))


@router.get("/spaces/{space_id}/scans", response_model=ScanList)
def get_scans(
    space_id: UUID,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> ScanList:
    rows, total = list_scans(db, space_id, limit, offset)
    return ScanList(items=[scan_out(row) for row in rows], total=total, limit=limit, offset=offset)


@router.post("/spaces/{space_id}/scans", response_model=ScanOut, status_code=201)
def post_scan(space_id: UUID, payload: ScanCreate, db: Session = Depends(get_db)) -> ScanOut:
    return scan_out(create_scan(db, space_id, payload))


@router.get("/spaces/{space_id}/objects", response_model=ObjectList)
def get_objects(
    space_id: UUID,
    q: str | None = Query(default=None, max_length=200),
    scan_id: UUID | None = None,
    include_archived: bool = False,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> ObjectList:
    return list_objects(db, space_id, q, scan_id, include_archived, limit, offset)


@router.post("/spaces/{space_id}/objects", response_model=ObjectOut, status_code=201)
def post_object(space_id: UUID, payload: ObjectCreate, response: Response, db: Session = Depends(get_db)) -> ObjectOut:
    obj = create_object(db, space_id, payload)
    response.status_code = 201
    return ObjectOut.model_validate(obj)
