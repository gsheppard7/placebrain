from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import SceneAssetList
from app.services import asset_out, list_assets

router = APIRouter(tags=["scans"])


@router.get("/scans/{scan_id}/assets", response_model=SceneAssetList)
def get_scan_assets(scan_id: UUID, db: Session = Depends(get_db)) -> SceneAssetList:
    return SceneAssetList(items=[asset_out(row) for row in list_assets(db, scan_id)])
