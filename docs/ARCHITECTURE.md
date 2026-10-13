# Architecture

PlaceBrain keeps three representations separate. A picture of a room is not an object, and an object is not a single coordinate.

## Visual

A `SceneAsset` belongs to one `Scan`. Milestone 1 renders `procedural` (the built-in demo room) and can preview a user-chosen `glb` in the browser. `gaussian_splat` is an allowed asset type so later scans can point at a splat, but this version does not train, store, or render one.

`storage_uri` is a pointer, not an identity. `alignment_json` is reserved for a later transform from that scan's frame into the space frame. Seeded assets leave it null. The app must not describe an imported scene as aligned unless that field is actually set.

The demo room frame is explicit: right-handed, Y up, meters, origin at the center of the floor. X is to the right, Z is toward the viewer when looking from the open side of the room. Walls sit near X = ±5 and Z = −4.

## Semantic

An `InventoryObject` is the stable identity inside a `Space`. Name, category, description, and serial number live here. Notes and links live on `Annotation`, also attached to the object, which is the start of GhostLayer. Annotations do not belong to a scan.

Zones (workbench, shelf, floor, cabinet) are named regions in the same space. They can later be nested through `parent_zone_id`.

The object table has no authoritative position column.

## Temporal

A `Scan` is one capture or manual pass of a space, not a new space. An `ObjectObservation` says: this object was seen in this scan, in this zone, at this scene-local `(x, y, z)`, at this time, from this source (`manual` or `model`), with optional confidence.

The viewer shows the latest observation for the selected scan. If there is none, the object stays in the inventory and the UI says it was not observed in that scan. Several observations of one object are history, not a computed move. SpaceGit, later, can store an alignment on the scene asset and compare observations across scans. That comparison is not implemented.

Creating a scan also creates a procedural scene asset so the scan has a visual manifest. New scans do not copy observations.

## Same-space rule

Scans, zones, and objects that are linked must belong to one space. The API rejects an observation that mixes a scan or zone from another space.

## Not implemented

- Video upload, photogrammetry, or Gaussian splat training
- Segmentation, automatic localization, and scene matching
- Embeddings, retrieval, and an assistant that answers from manuals
- Automatic change detection or absence claims
- Accounts, multi-tenant isolation, billing, cloud jobs, and device control
- Persisting an uploaded GLB; the file picker is a local preview

`model` observations and `confidence` exist so a future pipeline can write evidence without becoming the source of identity. The seeded room uses `manual` only.
