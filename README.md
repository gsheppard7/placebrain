# PlaceBrain

PlaceBrain is a local web app for a searchable spatial inventory. This milestone is a manual demo: a fictional equipment room, clickable 3D pins, and notes attached to stable object records. It does not reconstruct scenes, run computer vision, or claim that an object is missing.

## Run it

Backend, from `backend/`:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

The API applies Alembic migrations on startup and seeds the demo room once. The SQLite file is `backend/placebrain.db`. Delete that file and start the API again to restore the original seed. Override the database with `DATABASE_URL` if you want PostgreSQL later. Set `SEED_ON_STARTUP=false` to skip the demo data.

Frontend, from `frontend/`:

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. The API allows that origin. To point at another API, set `VITE_API_URL`.

Checks:

```bash
cd backend && source .venv/bin/activate && pytest
cd frontend && npm run build
```

## What you can do

- Open the seeded Riverside equipment room and orbit the procedural room.
- Search by name, category, or description. “camera” finds the depth camera.
- Click a row or a pin. The camera moves to that pin, and the detail panel opens the same record.
- Add an object, place its pin on the floor or by coordinates, and edit the record. Refresh keeps the change.
- Add a note or an `http(s)` documentation link.
- Switch between Baseline inventory and Follow-up check. The depth camera has two positions. The tripod is not observed on the follow-up scan, which is not the same as being missing.
- Create another manual scan. Objects start as not observed in that scan until you record one.
- Optionally preview a local `.glb`. It is not uploaded and is not aligned to the pins.

## API

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/health` | Liveness |
| GET, POST | `/spaces` | List or create spaces |
| GET | `/spaces/{space_id}` | Fetch one space |
| GET, POST | `/spaces/{space_id}/zones` | List or create zones |
| GET, POST | `/spaces/{space_id}/scans` | List or create scans |
| GET, POST | `/spaces/{space_id}/objects` | Search or create inventory objects |
| GET, PATCH | `/objects/{object_id}` | Fetch or edit an object |
| GET, POST | `/objects/{object_id}/observations` | History, or record a location |
| PATCH | `/observations/{observation_id}` | Correct a manual observation |
| GET, POST | `/objects/{object_id}/annotations` | Notes and links |
| GET | `/scans/{scan_id}/assets` | Scene asset manifest |

`GET /spaces/{space_id}/objects?scan_id=` includes `scan_observation` for that scan only. `null` means the object was not observed in that scan. Without `scan_id`, `scan_observation` is always `null` because the API does not invent a current location.

Interactive docs: http://127.0.0.1:8000/docs

## Layout

```text
frontend/   React, TypeScript, Vite, React Three Fiber, Tailwind
backend/    FastAPI, SQLAlchemy, Alembic, SQLite
docs/       Architecture of the visual, semantic, and temporal models
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the coordinate frame and what is intentionally not implemented.
