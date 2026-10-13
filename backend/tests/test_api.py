from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.seed import OBJ_CAMERA, OBJ_TRIPOD, SCAN_BASELINE, SCAN_FOLLOWUP, SPACE_ID, seed

BACKEND_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def client(tmp_path, monkeypatch):
    url = "sqlite:///" + str(tmp_path / "api.db")
    monkeypatch.setenv("DATABASE_URL", url)
    monkeypatch.setenv("SEED_ON_STARTUP", "false")
    monkeypatch.chdir(BACKEND_ROOT)
    from app.main import app

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def seeded(tmp_path, monkeypatch):
    url = "sqlite:///" + str(tmp_path / "seeded.db")
    monkeypatch.setenv("DATABASE_URL", url)
    monkeypatch.setenv("SEED_ON_STARTUP", "true")
    monkeypatch.chdir(BACKEND_ROOT)
    from app.main import app

    with TestClient(app) as test_client:
        yield test_client


def test_health(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_space_object_observation_and_annotation_round_trip(client: TestClient):
    space = client.post("/spaces", json={"name": "Bench lab", "description": "Temporary"}).json()
    zone = client.post(f"/spaces/{space['id']}/zones", json={"name": "Shelf"}).json()
    scan = client.post(f"/spaces/{space['id']}/scans", json={"label": "Morning pass"}).json()
    created = client.post(
        f"/spaces/{space['id']}/objects",
        json={"name": "Caliper", "category": "Tools", "description": "Digital caliper", "serial_number": "SN-1"},
    )
    assert created.status_code == 201
    obj = created.json()

    patched = client.patch(f"/objects/{obj['id']}", json={"description": "Digital caliper, 150 mm"})
    assert patched.status_code == 200
    assert patched.json()["description"] == "Digital caliper, 150 mm"
    assert client.get(f"/objects/{obj['id']}").json()["name"] == "Caliper"

    observation = client.post(
        f"/objects/{obj['id']}/observations",
        json={"scan_id": scan["id"], "zone_id": zone["id"], "x": 1.25, "y": 0.9, "z": -0.4, "source": "manual"},
    )
    assert observation.status_code == 201
    obs = observation.json()
    moved = client.patch(f"/observations/{obs['id']}", json={"x": 1.5, "y": 0.9, "z": -0.2})
    assert moved.status_code == 200

    listed = client.get(f"/spaces/{space['id']}/objects", params={"scan_id": scan["id"]})
    assert listed.status_code == 200
    body = listed.json()
    assert body["scan_id"] == scan["id"]
    assert body["items"][0]["scan_observation"]["x"] == 1.5

    note = client.post(
        f"/objects/{obj['id']}/annotations",
        json={"title": "Manual", "body": "Keep it in the case.", "external_url": "https://example.com/caliper"},
    )
    assert note.status_code == 201
    notes = client.get(f"/objects/{obj['id']}/annotations")
    assert notes.json()["items"][0]["external_url"] == "https://example.com/caliper"

    assets = client.get(f"/scans/{scan['id']}/assets")
    assert assets.status_code == 200
    asset = assets.json()["items"][0]
    assert asset["asset_type"] == "procedural"
    assert asset["alignment_json"] is None


def test_search_validation_and_cross_space_rules(client: TestClient):
    space = client.post("/spaces", json={"name": "Room A"}).json()
    other = client.post("/spaces", json={"name": "Room B"}).json()
    scan_a = client.post(f"/spaces/{space['id']}/scans", json={"label": "A"}).json()
    scan_b = client.post(f"/spaces/{other['id']}/scans", json={"label": "B"}).json()
    zone_b = client.post(f"/spaces/{other['id']}/zones", json={"name": "Other shelf"}).json()
    obj = client.post(
        f"/spaces/{space['id']}/objects",
        json={"name": "Depth camera", "category": "Imaging", "description": "Structured-light camera"},
    ).json()

    found = client.get(f"/spaces/{space['id']}/objects", params={"q": "camera", "scan_id": scan_a["id"]})
    assert any(item["name"] == "Depth camera" for item in found.json()["items"])
    assert found.json()["items"][0]["scan_observation"] is None

    blank = client.post(f"/spaces/{space['id']}/objects", json={"name": "  ", "category": "Tools"})
    assert blank.status_code == 422
    huge = client.post(
        f"/objects/{obj['id']}/observations",
        json={"scan_id": scan_a["id"], "x": 1e20, "y": 0, "z": 0},
    )
    assert huge.status_code == 422
    bad_url = client.post(
        f"/objects/{obj['id']}/annotations",
        json={"title": "Bad", "body": "nope", "external_url": "javascript:alert(1)"},
    )
    assert bad_url.status_code == 422

    cross_scan = client.post(
        f"/objects/{obj['id']}/observations",
        json={"scan_id": scan_b["id"], "x": 0, "y": 0, "z": 0},
    )
    assert cross_scan.status_code == 400
    cross_zone = client.post(
        f"/objects/{obj['id']}/observations",
        json={"scan_id": scan_a["id"], "zone_id": zone_b["id"], "x": 0, "y": 0, "z": 0},
    )
    assert cross_zone.status_code == 400
    missing = client.get("/spaces/00000000-0000-4000-8000-000000000099")
    assert missing.status_code == 404


def test_seed_is_idempotent_and_models_scan_history(seeded: TestClient):
    from app.database import SessionLocal

    assert SessionLocal is not None
    db = SessionLocal()
    try:
        assert seed(db) is False
    finally:
        db.close()

    objects = seeded.get(f"/spaces/{SPACE_ID}/objects", params={"limit": 100}).json()
    assert objects["total"] == 8
    assert objects["scan_id"] is None
    assert all(item["scan_observation"] is None for item in objects["items"])

    baseline = seeded.get(
        f"/spaces/{SPACE_ID}/objects", params={"q": "camera", "scan_id": SCAN_BASELINE, "limit": 100}
    ).json()
    names = {item["name"] for item in baseline["items"]}
    assert "Depth camera" in names

    followup = seeded.get(
        f"/spaces/{SPACE_ID}/objects", params={"scan_id": SCAN_FOLLOWUP, "limit": 100}
    ).json()["items"]
    tripod = next(item for item in followup if item["id"] == OBJ_TRIPOD)
    camera = next(item for item in followup if item["id"] == OBJ_CAMERA)
    assert tripod["scan_observation"] is None
    assert camera["scan_observation"]["source"] == "manual"
    assert camera["scan_observation"]["z"] == 0.9

    history = seeded.get(f"/objects/{OBJ_CAMERA}/observations").json()["items"]
    positions = {(item["x"], item["y"], item["z"]) for item in history}
    assert (-4.15, 1.36, -0.8) in positions
    assert (-4.15, 1.36, 0.9) in positions
    assert len({item["observed_at"] for item in history}) == 2

    notes = seeded.get(f"/objects/{OBJ_CAMERA}/annotations").json()["items"]
    assert notes[0]["external_url"] == "https://example.com/docs/depth-camera"

    assets = seeded.get(f"/scans/{SCAN_BASELINE}/assets").json()["items"]
    assert assets[0]["asset_type"] == "procedural"
    assert assets[0]["alignment_json"] is None


def test_archive_hides_object_from_default_list(client: TestClient):
    space = client.post("/spaces", json={"name": "Archive room"}).json()
    obj = client.post(f"/spaces/{space['id']}/objects", json={"name": "Old meter", "category": "Test equipment"}).json()
    hidden = client.patch(f"/objects/{obj['id']}", json={"archived_at": "2026-05-01T00:00:00Z"})
    assert hidden.status_code == 200
    listed = client.get(f"/spaces/{space['id']}/objects").json()
    assert listed["total"] == 0
    included = client.get(f"/spaces/{space['id']}/objects", params={"include_archived": True}).json()
    assert included["total"] == 1
