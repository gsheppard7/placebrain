# PlaceBrain — Initial Cursor Agent Prompt

Paste the entire prompt below into Cursor Agent in a new project folder (or an existing PlaceBrain repo).

---

You are my senior full-stack engineering partner. We are starting **PlaceBrain**, a product that turns physical storage areas, university makerspaces, and engineering labs into **searchable, interactive 3D spatial inventories**.

Longer-term platform architecture:
- **PlaceBrain core:** persistent spaces, equipment identities, 3D locations, scan observations, searchable spatial inventory.
- **GhostLayer:** attach notes, manuals, links, and eventually an AI assistant to individual physical objects.
- **SpaceGit:** align repeat scans, match persistent object identities, and display confirmed or suspected physical changes over time.

**IMPORTANT: Build ONLY the first vertical slice right now.** We need a real application that is usable with manual data and a simple 3D scene. Do not jump ahead to Gaussian-splat training, automated segmentation, RAG, computer vision pipelines, robotics, microservices, authentication, billing, or AWS deployment. Create extension points for those future capabilities, but do not pretend they already work.

## Milestone 1 objective

Deliver a locally runnable web app in which I can:
1. Open a seeded demo university equipment room in an interactive 3D viewer.
2. See several visible 3D equipment pins, with a list of the corresponding inventory records.
3. Search equipment by name, category, or description; click a result to select its pin and focus the camera on its position.
4. Click a pin to see an object detail panel showing name, category, zone, description, last-observed time, scan reference, and source of location data.
5. Add and edit an inventory object; manually place or move its pin in the 3D space; persist the changes to the backend.
6. Add a note or documentation URL to an object and reopen it after refresh (the beginning of GhostLayer).
7. Create a second scan record for the same space and record a new observation of the same stable object ID without replacing the object. Show scan-specific observations in a simple history panel. This establishes the data model for future SpaceGit; no automatic comparison yet.
8. Optionally load a **user-provided .glb** scene asset instead of the procedural demo room if that can be done cleanly in this milestone. Do not let this optional feature block the core acceptance criteria. Do not implement raw-video reconstruction yet.

## Preferred technologies

- Frontend: **React + TypeScript + Vite**, React Three Fiber / Three.js and Drei for the 3D viewer; Tailwind for a clean modern UI (if it works smoothly in this repo).
- Backend: **Python + FastAPI + Pydantic v2 + SQLAlchemy 2.x + Alembic**.
- Database: **SQLite by default in local development**, with DATABASE_URL configurable so PostgreSQL can be used later. No managed cloud dependencies in milestone 1.
- Tests: **pytest** for critical API/database behavior; use a lightweight frontend test setup if feasible.
- Package management: npm for frontend; Python venv + requirements.txt or pyproject.toml for backend, whichever is simplest and reproducible.
- Data access: typed HTTP API (no hardcoded frontend inventory state beyond temporary loading skeletons); use a typed frontend API client.

If there is already code in this repository, **inspect it first, propose how to integrate, and avoid rewriting or deleting unrelated files**. If it's empty, create a clear monorepo structure with `/frontend`, `/backend`, and `/docs`.

## Core domain model — do this carefully

Use UUID primary keys and timestamps. Define real database tables and Alembic migrations, not just JSON mock storage.

- **Space**: id, name, description, created_at, updated_at. One physical site or room for now.
- **Zone**: id, space_id, name, optional parent_zone_id. Represents shelf, cabinet, workbench, or storage section.
- **Scan**: id, space_id, label, captured_at, status (`manual` or `imported` for now), optional notes. Represents a particular observation/capture of a space, not an entire new space.
- **SceneAsset**: id, scan_id, asset_type (`procedural` or `glb` now; reserve the ability to add `gaussian_splat` later), storage_uri, optional metadata_json and alignment/transform metadata. The rendering format must NOT determine the semantic object identity.
- **InventoryObject**: id, space_id, name, category, description, optional serial_number, created_at, updated_at, archived_at. This is the stable logical identity across scans. Do NOT store only one authoritative `position` field on this table.
- **ObjectObservation**: id, object_id, scan_id, zone_id (nullable), x, y, z (scene-local meters), observed_at, source (`manual` or `model`), confidence (nullable), notes. Multiple scans may observe the same object; each observation points to one persistent object. An observation is evidence of a location at a particular time, not a guarantee of current location.
- **Annotation**: id, object_id, title, body, optional external_url, created_at, updated_at.

Keep a clear **coordinate-system convention**: right-handed scene coordinates, Y up, meters where known, and positions relative to a space/scene reference frame. Document how transformations between scans would be stored later. For a demo procedural room, use an explicit local origin. Do not claim imported scenes have been aligned unless an alignment is actually supplied.

Use schema relationships and foreign keys; enforce that scans, objects, and zones tied together are from the same space. Keep validation strict (length limits, sensible enums, safe URLs, finite coordinates). The frontend should always retrieve the currently selected scan's latest observation for each object and should not show an object as definitely present when there is no observation for that scan.

## API — minimum endpoints

You can refine names for REST consistency, but document them and implement the essential operations:

- GET /health
- GET /spaces, POST /spaces, GET /spaces/{space_id}
- GET /spaces/{space_id}/zones
- GET /spaces/{space_id}/scans, POST /spaces/{space_id}/scans
- GET /spaces/{space_id}/objects?q=..., POST /spaces/{space_id}/objects
- GET /objects/{object_id}, PATCH /objects/{object_id}
- GET /objects/{object_id}/observations, POST /objects/{object_id}/observations
- GET /objects/{object_id}/annotations, POST /objects/{object_id}/annotations
- GET /scans/{scan_id}/assets (returns scene asset manifest)

Use clear response schemas, meaningful status codes, CORS restricted to the local frontend origin, and predictable validation errors. Implement pagination or sensible limits for list endpoints if inexpensive.

## Frontend UI / UX

Create a professional, simple interface suitable for a real product demo, not a giant dashboard with empty charts.

- Left sidebar: space title, selectable scan, equipment search, grouped inventory list, and an Add Object action.
- Main area: large interactive 3D canvas with a small procedural room (floor, walls, storage shelves/workbench) and clickable location pins. Support orbit, pan, and zoom. Camera centers smoothly on selected inventory pin; selecting a search result highlights it.
- Right detail drawer: editable object fields, zone, recorded coordinates, observation source/scan/time, and annotations. Include an obvious `last observed` indicator.
- A simple action for manual pin placement: click a point on the floor or reposition with numeric coordinates. Keep position handling coherent with the room coordinate frame.
- Add accessible empty/loading/error states; design for desktop first but keep layout usable on a small laptop.
- UI must clearly distinguish **demo/manually entered data** from computer-vision observations. No AI badges or "live tracking" claims at this stage.

Seed a realistic *fictional* engineering equipment room with ~8 objects (e.g., oscilloscope, depth camera, soldering station, LiDAR sensor, toolbox, tripod, multimeter, robotic arm kit). Include at least two scans for one stable object with different positions so the history view demonstrates the data model. Seed data must be idempotent and use generic fictional lab labels.

## Implementation sequence

1. Inspect repo and write a concise plan and proposed file tree. If this is a new repo, initialize it.
2. Implement database schema + Alembic migration + idempotent seed data.
3. Implement FastAPI endpoints and typed response models, then run API tests.
4. Build frontend layout and API client.
5. Build procedural 3D room, interactive pins, search selection and camera focusing.
6. Connect create/edit/position/annotation workflows to actual persisted API data.
7. Add scan switcher and scan-specific observation history.
8. Add a useful README and `/docs/ARCHITECTURE.md` describing the three representations (visual, semantic, temporal) and what remains unimplemented.
9. Run backend tests and frontend build/typecheck; fix failures. Report any skipped checks honestly.

## Acceptance criteria / definition of done

- I can launch everything locally with documented commands (ideally one easy command per app).
- Reloading the browser does not erase changes to an object or its annotations.
- Clicking an equipment row focuses and highlights its 3D pin; clicking a pin selects the same object record.
- A search such as "camera" finds the seeded depth camera.
- I can add a new object and manual observation with real persisted coordinates.
- The same persistent object appears in two scans with separate observation timestamps/positions.
- Missing observations are displayed as **not observed in this scan**, not automatically "missing from the room".
- API tests pass and the frontend build succeeds (or you clearly disclose precise blockers).
- No paid service, API key, GPU, or robotics hardware is necessary for this milestone.

## Non-goals — explicitly defer

- Uploading videos and reconstructing Gaussian splats from scratch.
- Automatic 3D object segmentation, scene matching, or location inference.
- LLM answers, vector databases, document RAG, and autonomous AI agents.
- Automatic change detection and absence claims.
- Multi-tenant security, production deployment, cloud jobs, billing, and physical device control.

## Engineering quality bar

Keep code modular but not overengineered. Write understandable interfaces with type annotations, migrations, simple tests, input validation, and a clear README. Avoid placeholder endpoints disguised as working features. Prefer a fully working small product slice over a large codebase of mocks. Do not generate fake scan data from any private Georgia Tech facility.

**Start now by inspecting the repo, laying out your implementation plan, and then building Milestone 1. At the end, give me exact commands to run it, a checklist of implemented features, test results, and the next 3 recommended engineering tasks.**
