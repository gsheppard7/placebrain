from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import (
    AnnotationCreate,
    AnnotationList,
    AnnotationOut,
    ObjectOut,
    ObjectUpdate,
    ObservationCreate,
    ObservationList,
    ObservationOut,
    ObservationUpdate,
)
from app.services import (
    annotation_out,
    create_annotation,
    create_observation,
    get_object,
    list_annotations,
    list_observations,
    update_object,
    update_observation,
)

router = APIRouter(tags=["objects"])


@router.get("/objects/{object_id}", response_model=ObjectOut)
def get_object_by_id(object_id: UUID, db: Session = Depends(get_db)) -> ObjectOut:
    return ObjectOut.model_validate(get_object(db, object_id))


@router.patch("/objects/{object_id}", response_model=ObjectOut)
def patch_object(object_id: UUID, payload: ObjectUpdate, db: Session = Depends(get_db)) -> ObjectOut:
    return ObjectOut.model_validate(update_object(db, object_id, payload))


@router.get("/objects/{object_id}/observations", response_model=ObservationList)
def get_observations(object_id: UUID, db: Session = Depends(get_db)) -> ObservationList:
    return ObservationList(items=list_observations(db, object_id))


@router.post("/objects/{object_id}/observations", response_model=ObservationOut, status_code=201)
def post_observation(object_id: UUID, payload: ObservationCreate, db: Session = Depends(get_db)) -> ObservationOut:
    return create_observation(db, object_id, payload)


@router.patch("/observations/{observation_id}", response_model=ObservationOut)
def patch_observation(
    observation_id: UUID, payload: ObservationUpdate, db: Session = Depends(get_db)
) -> ObservationOut:
    return update_observation(db, observation_id, payload)


@router.get("/objects/{object_id}/annotations", response_model=AnnotationList)
def get_annotations(object_id: UUID, db: Session = Depends(get_db)) -> AnnotationList:
    return AnnotationList(items=[annotation_out(row) for row in list_annotations(db, object_id)])


@router.post("/objects/{object_id}/annotations", response_model=AnnotationOut, status_code=201)
def post_annotation(object_id: UUID, payload: AnnotationCreate, db: Session = Depends(get_db)) -> AnnotationOut:
    return annotation_out(create_annotation(db, object_id, payload))
