import json
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models import (
    Annotation,
    AssetType,
    InventoryObject,
    ObjectObservation,
    ObservationSource,
    Scan,
    ScanStatus,
    SceneAsset,
    Space,
    Zone,
)

SPACE_ID = "a1000000-0000-4000-8000-000000000001"
ZONE_BENCH = "a2000000-0000-4000-8000-000000000001"
ZONE_SHELF = "a2000000-0000-4000-8000-000000000002"
ZONE_FLOOR = "a2000000-0000-4000-8000-000000000003"
ZONE_CABINET = "a2000000-0000-4000-8000-000000000004"
SCAN_BASELINE = "a3000000-0000-4000-8000-000000000001"
SCAN_FOLLOWUP = "a3000000-0000-4000-8000-000000000002"
OBJ_SCOPE = "a4000000-0000-4000-8000-000000000001"
OBJ_CAMERA = "a4000000-0000-4000-8000-000000000002"
OBJ_SOLDER = "a4000000-0000-4000-8000-000000000003"
OBJ_LIDAR = "a4000000-0000-4000-8000-000000000004"
OBJ_TOOLBOX = "a4000000-0000-4000-8000-000000000005"
OBJ_TRIPOD = "a4000000-0000-4000-8000-000000000006"
OBJ_METER = "a4000000-0000-4000-8000-000000000007"
OBJ_ARM = "a4000000-0000-4000-8000-000000000008"

BASELINE_AT = datetime(2026, 3, 2, 15, 0, tzinfo=timezone.utc)
FOLLOWUP_AT = datetime(2026, 4, 18, 11, 30, tzinfo=timezone.utc)
CREATED_AT = datetime(2026, 3, 1, 12, 0, tzinfo=timezone.utc)

ROOM_METADATA = {
    "frame": "demo-room-v1",
    "units": "meters",
    "up": "Y",
    "handedness": "right",
    "origin": "center of the floor",
    "note": "Procedural demo room. alignment_json is null because no scan alignment was supplied.",
}


def _obs(
    db: Session,
    *,
    obs_id: str,
    object_id: str,
    scan_id: str,
    zone_id: str,
    x: float,
    y: float,
    z: float,
    observed_at: datetime,
    notes: str | None = None,
) -> None:
    db.add(
        ObjectObservation(
            id=obs_id,
            object_id=object_id,
            scan_id=scan_id,
            zone_id=zone_id,
            x=x,
            y=y,
            z=z,
            observed_at=observed_at,
            source=ObservationSource.manual.value,
            confidence=None,
            notes=notes,
        )
    )


def seed(db: Session) -> bool:
    """Insert the fictional demo room once. Returns True when new rows were written."""
    if db.get(Space, SPACE_ID) is not None:
        return False

    db.add(
        Space(
            id=SPACE_ID,
            name="Riverside Engineering Lab — Equipment Room",
            description=(
                "Fictional university equipment room used to demonstrate PlaceBrain. "
                "Locations are manual demo entries, not computer-vision results, and "
                "this room is not a real facility."
            ),
            created_at=CREATED_AT,
            updated_at=CREATED_AT,
        )
    )
    for zone_id, name in (
        (ZONE_BENCH, "Main workbench"),
        (ZONE_SHELF, "Wall shelf"),
        (ZONE_FLOOR, "Open floor"),
        (ZONE_CABINET, "Supply cabinet"),
    ):
        db.add(
            Zone(
                id=zone_id,
                space_id=SPACE_ID,
                name=name,
                parent_zone_id=None,
                created_at=CREATED_AT,
            )
        )

    db.add(
        Scan(
            id=SCAN_BASELINE,
            space_id=SPACE_ID,
            label="Baseline inventory",
            captured_at=BASELINE_AT,
            status=ScanStatus.manual.value,
            notes="First manual walkthrough of the demo room.",
            created_at=BASELINE_AT,
        )
    )
    db.add(
        Scan(
            id=SCAN_FOLLOWUP,
            space_id=SPACE_ID,
            label="Follow-up check",
            captured_at=FOLLOWUP_AT,
            status=ScanStatus.manual.value,
            notes="Second manual pass. The depth camera was moved. The tripod was not observed.",
            created_at=FOLLOWUP_AT,
        )
    )
    for scan_id, created_at in ((SCAN_BASELINE, BASELINE_AT), (SCAN_FOLLOWUP, FOLLOWUP_AT)):
        db.add(
            SceneAsset(
                scan_id=scan_id,
                asset_type=AssetType.procedural.value,
                storage_uri="procedural://demo-room-v1",
                metadata_json=json.dumps(ROOM_METADATA),
                alignment_json=None,
                created_at=created_at,
            )
        )

    objects = [
        (
            OBJ_SCOPE,
            "Bench oscilloscope",
            "Test equipment",
            "Four-channel bench oscilloscope for electronics debugging.",
            "SN-DEMO-1001",
        ),
        (
            OBJ_CAMERA,
            "Depth camera",
            "Imaging",
            "Structured-light depth camera used for bench capture experiments.",
            "SN-DEMO-1002",
        ),
        (
            OBJ_SOLDER,
            "Soldering station",
            "Tools",
            "Temperature-controlled soldering station with a fume extractor nearby.",
            "SN-DEMO-1003",
        ),
        (
            OBJ_LIDAR,
            "LiDAR sensor",
            "Imaging",
            "Compact spinning LiDAR unit stored on the wall shelf between experiments.",
            "SN-DEMO-1004",
        ),
        (
            OBJ_TOOLBOX,
            "Field toolbox",
            "Tools",
            "Rolling toolbox with hand tools for fixture assembly.",
            "SN-DEMO-1005",
        ),
        (
            OBJ_TRIPOD,
            "Camera tripod",
            "Imaging",
            "Aluminum tripod kept on the open floor when it is not in a setup.",
            "SN-DEMO-1006",
        ),
        (
            OBJ_METER,
            "Digital multimeter",
            "Test equipment",
            "Handheld multimeter that usually stays on the main workbench.",
            "SN-DEMO-1007",
        ),
        (
            OBJ_ARM,
            "Robotic arm kit",
            "Robotics",
            "Desktop robotic arm kit in its storage case, awaiting a lab session.",
            "SN-DEMO-1008",
        ),
    ]
    for object_id, name, category, description, serial in objects:
        db.add(
            InventoryObject(
                id=object_id,
                space_id=SPACE_ID,
                name=name,
                category=category,
                description=description,
                serial_number=serial,
                created_at=CREATED_AT,
                updated_at=CREATED_AT,
                archived_at=None,
            )
        )

    # Stable positions shared by both scans, except the depth camera (moved) and tripod (follow-up absent).
    shared = [
        ("b5000000-0000-4000-8000-000000000001", OBJ_SCOPE, ZONE_BENCH, -0.9, 0.98, -2.2, None),
        ("b5000000-0000-4000-8000-000000000003", OBJ_SOLDER, ZONE_BENCH, 0.9, 0.98, -2.2, None),
        ("b5000000-0000-4000-8000-000000000004", OBJ_LIDAR, ZONE_SHELF, -4.15, 0.86, 1.2, None),
        ("b5000000-0000-4000-8000-000000000005", OBJ_TOOLBOX, ZONE_FLOOR, 2.2, 0.22, 1.6, None),
        ("b5000000-0000-4000-8000-000000000006", OBJ_TRIPOD, ZONE_FLOOR, 3.0, 0.2, 0.2, None),
        ("b5000000-0000-4000-8000-000000000007", OBJ_METER, ZONE_BENCH, 0.05, 0.98, -2.05, None),
        ("b5000000-0000-4000-8000-000000000008", OBJ_ARM, ZONE_CABINET, 3.3, 0.35, -2.4, None),
    ]
    for obs_id, object_id, zone_id, x, y, z, notes in shared:
        _obs(
            db,
            obs_id=obs_id,
            object_id=object_id,
            scan_id=SCAN_BASELINE,
            zone_id=zone_id,
            x=x,
            y=y,
            z=z,
            observed_at=BASELINE_AT,
            notes=notes,
        )

    followup_shared = [
        ("b5000000-0000-4000-8000-000000000011", OBJ_SCOPE, ZONE_BENCH, -0.9, 0.98, -2.2),
        ("b5000000-0000-4000-8000-000000000013", OBJ_SOLDER, ZONE_BENCH, 0.9, 0.98, -2.2),
        ("b5000000-0000-4000-8000-000000000014", OBJ_LIDAR, ZONE_SHELF, -4.15, 0.86, 1.2),
        ("b5000000-0000-4000-8000-000000000015", OBJ_TOOLBOX, ZONE_FLOOR, 2.2, 0.22, 1.6),
        ("b5000000-0000-4000-8000-000000000017", OBJ_METER, ZONE_BENCH, 0.05, 0.98, -2.05),
        ("b5000000-0000-4000-8000-000000000018", OBJ_ARM, ZONE_CABINET, 3.3, 0.35, -2.4),
    ]
    for obs_id, object_id, zone_id, x, y, z in followup_shared:
        _obs(
            db,
            obs_id=obs_id,
            object_id=object_id,
            scan_id=SCAN_FOLLOWUP,
            zone_id=zone_id,
            x=x,
            y=y,
            z=z,
            observed_at=FOLLOWUP_AT,
            notes=None,
        )

    _obs(
        db,
        obs_id="b5000000-0000-4000-8000-000000000002",
        object_id=OBJ_CAMERA,
        scan_id=SCAN_BASELINE,
        zone_id=ZONE_SHELF,
        x=-4.15,
        y=1.36,
        z=-0.8,
        observed_at=BASELINE_AT,
        notes="Upper shelf, left bay.",
    )
    _obs(
        db,
        obs_id="b5000000-0000-4000-8000-000000000012",
        object_id=OBJ_CAMERA,
        scan_id=SCAN_FOLLOWUP,
        zone_id=ZONE_SHELF,
        x=-4.15,
        y=1.36,
        z=0.9,
        observed_at=FOLLOWUP_AT,
        notes="Moved along the upper shelf to the right-hand bay. Manual entry, not an inferred change.",
    )

    db.add(
        Annotation(
            object_id=OBJ_CAMERA,
            title="Quick start",
            body="Fictional demo note. Connect over USB 3 and keep the camera indoors on a stable shelf.",
            external_url="https://example.com/docs/depth-camera",
            created_at=BASELINE_AT,
            updated_at=BASELINE_AT,
        )
    )
    db.add(
        Annotation(
            object_id=OBJ_SCOPE,
            title="Bench position",
            body="Usually lives on the left side of the main workbench, next to the multimeter.",
            external_url=None,
            created_at=BASELINE_AT,
            updated_at=BASELINE_AT,
        )
    )
    db.commit()
    return True
