import { useEffect, useMemo, useState, type FormEvent } from "react";
import { api, ApiError } from "./api";
import { DetailDrawer } from "./components/DetailDrawer";
import { Scene, type PinData } from "./components/Scene";
import { Sidebar } from "./components/Sidebar";
import type { Annotation, InventoryObject, Observation, Scan, SceneAsset, Space, Zone } from "./types";

type Placement = "new" | "move" | "record" | null;

interface ObjectEdit {
  name: string;
  category: string;
  description: string;
  serial_number: string;
}

interface Coords {
  x: string;
  y: string;
  z: string;
  zoneId: string;
  notes: string;
}

const emptyCoords: Coords = { x: "0", y: "0.15", z: "0", zoneId: "", notes: "" };

function message(error: unknown): string {
  if (error instanceof ApiError) return error.message;
  if (error instanceof Error) return error.message;
  return "Something went wrong";
}

function clampToRoom(x: number, z: number): { x: number; z: number } {
  return {
    x: Math.min(4.7, Math.max(-4.7, x)),
    z: Math.min(3.7, Math.max(-3.7, z)),
  };
}

function parseCoord(value: string): number | null {
  const number = Number(value);
  if (!Number.isFinite(number) || Math.abs(number) > 10000) return null;
  return number;
}

export default function App() {
  const [reloadKey, setReloadKey] = useState(0);
  const [space, setSpace] = useState<Space | null>(null);
  const [zones, setZones] = useState<Zone[]>([]);
  const [scans, setScans] = useState<Scan[]>([]);
  const [scanId, setScanId] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [debouncedQuery, setDebouncedQuery] = useState("");
  const [objects, setObjects] = useState<InventoryObject[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [observations, setObservations] = useState<Observation[]>([]);
  const [annotations, setAnnotations] = useState<Annotation[]>([]);
  const [assets, setAssets] = useState<SceneAsset[]>([]);
  const [loading, setLoading] = useState(true);
  const [listLoading, setListLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [placement, setPlacement] = useState<Placement>(null);
  const [adding, setAdding] = useState(false);
  const [newObject, setNewObject] = useState({ name: "", category: "", description: "" });
  const [draft, setDraft] = useState({ x: 0, y: 0.15, z: 0.5, zoneId: "" });
  const [edit, setEdit] = useState<ObjectEdit | null>(null);
  const [coords, setCoords] = useState<Coords>(emptyCoords);
  const [note, setNote] = useState({ title: "", body: "", external_url: "" });
  const [scanDraft, setScanDraft] = useState<string | null>(null);
  const [glbUrl, setGlbUrl] = useState<string | null>(null);
  const [glbNotice, setGlbNotice] = useState<string | null>(null);
  const [detailKey, setDetailKey] = useState(0);

  const selected = objects.find((item) => item.id === selectedId) ?? null;
  const scan = scans.find((item) => item.id === scanId) ?? null;

  useEffect(() => {
    const handle = window.setTimeout(() => setDebouncedQuery(query), 200);
    return () => window.clearTimeout(handle);
  }, [query]);

  useEffect(() => {
    let cancelled = false;
    async function boot() {
      try {
        setLoading(true);
        setError(null);
        const spaces = await api.listSpaces();
        if (cancelled) return;
        const first = spaces.items[0];
        if (!first) {
          setError("No space is available. Start the API so it can seed the demo room.");
          return;
        }
        const [zonePage, scanPage] = await Promise.all([api.listZones(first.id), api.listScans(first.id)]);
        if (cancelled) return;
        setSpace(first);
        setZones(zonePage.items);
        setScans(scanPage.items);
        setScanId((current) => current ?? scanPage.items[0]?.id ?? null);
      } catch (caught) {
        if (!cancelled) setError(message(caught));
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    void boot();
    return () => {
      cancelled = true;
    };
  }, [reloadKey]);

  useEffect(() => {
    if (!space || !scanId) return;
    let cancelled = false;
    setListLoading(true);
    Promise.all([api.listObjects(space.id, scanId, debouncedQuery), api.listAssets(scanId)])
      .then(([page, assetPage]) => {
        if (cancelled) return;
        setObjects(page.items);
        setAssets(assetPage.items);
      })
      .catch((caught) => {
        if (!cancelled) setError(message(caught));
      })
      .finally(() => {
        if (!cancelled) setListLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [space, scanId, debouncedQuery, detailKey]);

  useEffect(() => {
    if (!selectedId) {
      setObservations([]);
      setAnnotations([]);
      return;
    }
    let cancelled = false;
    Promise.all([api.listObservations(selectedId), api.listAnnotations(selectedId)])
      .then(([observationPage, annotationPage]) => {
        if (cancelled) return;
        setObservations(observationPage.items);
        setAnnotations(annotationPage.items);
      })
      .catch((caught) => {
        if (!cancelled) setActionError(message(caught));
      });
    return () => {
      cancelled = true;
    };
  }, [selectedId, detailKey]);

  const selectedKey = selected
    ? `${selected.id}:${selected.updated_at}:${selected.scan_observation?.id ?? "none"}:${selected.scan_observation?.x ?? ""}:${selected.scan_observation?.y ?? ""}:${selected.scan_observation?.z ?? ""}`
    : "";
  const [syncedKey, setSyncedKey] = useState("");
  if (selectedKey !== syncedKey) {
    setSyncedKey(selectedKey);
    if (!selected) {
      setEdit(null);
    } else {
      setEdit({
        name: selected.name,
        category: selected.category,
        description: selected.description ?? "",
        serial_number: selected.serial_number ?? "",
      });
      const observation = selected.scan_observation;
      setCoords({
        x: observation ? String(observation.x) : "0",
        y: observation ? String(observation.y) : "0.15",
        z: observation ? String(observation.z) : "0",
        zoneId: observation?.zone_id ?? "",
        notes: observation?.notes ?? "",
      });
      setNote({ title: "", body: "", external_url: "" });
    }
  }

  const shown = useMemo(() => {
    if (!selected || !edit) return null;
    return {
      ...selected,
      name: edit.name,
      category: edit.category,
      description: edit.description,
      serial_number: edit.serial_number,
    };
  }, [selected, edit]);

  const pins: PinData[] = objects.flatMap((item) =>
    item.scan_observation
      ? [{ id: item.id, name: item.name, position: [item.scan_observation.x, item.scan_observation.y, item.scan_observation.z] as [number, number, number] }]
      : [],
  );
  const focus = selected?.scan_observation
    ? ([selected.scan_observation.x, selected.scan_observation.y, selected.scan_observation.z] as [number, number, number])
    : null;
  const focusKey = focus ? `${selectedId}:${focus.join(":")}` : null;

  async function refreshScans(nextScanId?: string) {
    if (!space) return;
    const scanPage = await api.listScans(space.id);
    setScans(scanPage.items);
    if (nextScanId) setScanId(nextScanId);
  }

  async function saveObservation(next: { x: number; y: number; z: number }, zoneId = coords.zoneId, notes = coords.notes) {
    if (!selected || !scanId) return;
    const payload = {
      x: next.x,
      y: next.y,
      z: next.z,
      zone_id: zoneId || null,
      notes,
    };
    if (selected.scan_observation) {
      await api.updateObservation(selected.scan_observation.id, payload);
    } else {
      await api.createObservation(selected.id, { ...payload, scan_id: scanId, source: "manual" });
    }
    setDetailKey((value) => value + 1);
  }

  async function onFloor(point: { x: number; z: number }) {
    if (!placement) return;
    const clamped = clampToRoom(point.x, point.z);
    if (placement === "new") {
      setDraft((current) => ({ ...current, x: clamped.x, z: clamped.z }));
      return;
    }
    const y = parseCoord(coords.y) ?? 0.15;
    setCoords((current) => ({ ...current, x: String(clamped.x), y: String(y), z: String(clamped.z) }));
    try {
      setSaving(true);
      setActionError(null);
      await saveObservation({ x: clamped.x, y, z: clamped.z });
      setPlacement(null);
    } catch (caught) {
      setActionError(message(caught));
    } finally {
      setSaving(false);
    }
  }

  async function onCreateObject() {
    if (!space || !scanId) return;
    try {
      setSaving(true);
      setActionError(null);
      const created = await api.createObject(space.id, {
        name: newObject.name,
        category: newObject.category,
        description: newObject.description || undefined,
      });
      await api.createObservation(created.id, {
        scan_id: scanId,
        zone_id: draft.zoneId || null,
        x: draft.x,
        y: draft.y,
        z: draft.z,
        source: "manual",
      });
      setNewObject({ name: "", category: "", description: "" });
      setAdding(false);
      setPlacement(null);
      setSelectedId(created.id);
      setDetailKey((value) => value + 1);
    } catch (caught) {
      setActionError(message(caught));
    } finally {
      setSaving(false);
    }
  }

  async function onSaveObject(event: FormEvent) {
    event.preventDefault();
    if (!selected || !edit) return;
    try {
      setSaving(true);
      setActionError(null);
      await api.updateObject(selected.id, {
        name: edit.name,
        category: edit.category,
        description: edit.description,
        serial_number: edit.serial_number,
      });
      setDetailKey((value) => value + 1);
    } catch (caught) {
      setActionError(message(caught));
    } finally {
      setSaving(false);
    }
  }

  async function onSavePosition(event: FormEvent) {
    event.preventDefault();
    const x = parseCoord(coords.x);
    const y = parseCoord(coords.y);
    const z = parseCoord(coords.z);
    if (x === null || y === null || z === null) {
      setActionError("Coordinates must be finite numbers within ±10000 meters.");
      return;
    }
    try {
      setSaving(true);
      setActionError(null);
      await saveObservation({ x, y, z });
      setPlacement(null);
    } catch (caught) {
      setActionError(message(caught));
    } finally {
      setSaving(false);
    }
  }

  async function onAddNote(event: FormEvent) {
    event.preventDefault();
    if (!selected) return;
    try {
      setSaving(true);
      setActionError(null);
      await api.createAnnotation(selected.id, {
        title: note.title,
        body: note.body,
        external_url: note.external_url.trim() || null,
      });
      setNote({ title: "", body: "", external_url: "" });
      setDetailKey((value) => value + 1);
    } catch (caught) {
      setActionError(message(caught));
    } finally {
      setSaving(false);
    }
  }

  async function onCreateScan(event: FormEvent) {
    event.preventDefault();
    if (!space || !scanDraft?.trim()) return;
    try {
      setSaving(true);
      setActionError(null);
      const created = await api.createScan(space.id, scanDraft.trim());
      setScanDraft(null);
      await refreshScans(created.id);
      setSelectedId(null);
    } catch (caught) {
      setActionError(message(caught));
    } finally {
      setSaving(false);
    }
  }

  function onGlbFile(file: File | null) {
    setGlbNotice(null);
    setGlbUrl((current) => {
      if (current) URL.revokeObjectURL(current);
      return file ? URL.createObjectURL(file) : null;
    });
  }

  const splatReserved = assets.some((asset) => asset.asset_type === "gaussian_splat");

  return (
    <div className="h-screen min-w-[1040px] overflow-auto bg-slate-100">
    <div className="grid h-full min-h-[640px] grid-cols-[280px_minmax(420px,1fr)_340px]">
      <Sidebar
        space={space}
        scans={scans}
        scanId={scanId}
        query={query}
        objects={objects}
        selectedId={selectedId}
        loading={loading}
        listLoading={listLoading}
        error={error}
        adding={adding}
        draft={draft}
        zones={zones}
        newObject={newObject}
        scanDraft={scanDraft}
        onQuery={setQuery}
        onScan={(id) => {
          setScanId(id);
          setPlacement(null);
        }}
        onSelect={(id) => {
          setSelectedId(id);
          setPlacement(null);
        }}
        onRetry={() => setReloadKey((value) => value + 1)}
        onToggleAdd={() => {
          setAdding((value) => !value);
          setPlacement(null);
        }}
        onNewObject={(patch) => setNewObject((current) => ({ ...current, ...patch }))}
        onDraft={(patch) => setDraft((current) => ({ ...current, ...patch }))}
        onCreateObject={() => void onCreateObject()}
        onPlaceNew={() => setPlacement("new")}
        onToggleScanDraft={() => setScanDraft((current) => (current === null ? "" : null))}
        onScanDraft={setScanDraft}
        onCreateScan={(event) => void onCreateScan(event)}
      />

      <main className="relative min-w-0">
        <Scene
          pins={pins}
          selectedId={selectedId}
          focusKey={focusKey}
          focus={focus}
          placing={placement !== null}
          draft={placement === "new" ? draft : null}
          glbUrl={glbUrl}
          onSelect={setSelectedId}
          onFloor={(point) => void onFloor(point)}
          onGlbError={() => {
            onGlbFile(null);
            setGlbNotice("That GLB could not be previewed. The procedural room is showing again.");
          }}
        />
        <div className="pointer-events-none absolute inset-0">
          <div className="pointer-events-auto absolute top-3 left-3 max-w-sm rounded-lg bg-white/95 px-3 py-2 text-xs leading-5 text-slate-700 shadow">
            <p className="font-medium text-slate-900">Demo room · manual locations</p>
            <p>Y up, meters, origin at the floor center. Imported scenes are not aligned unless an alignment is stored.</p>
            {splatReserved && <p className="mt-1 text-amber-800">A Gaussian splat asset is reserved and is not rendered.</p>}
            {glbNotice && <p className="mt-1 text-amber-800">{glbNotice}</p>}
          </div>
          <div className="pointer-events-auto absolute top-3 right-3 flex gap-2">
            <label className="cursor-pointer rounded-md bg-white/95 px-3 py-2 text-xs font-medium text-slate-800 shadow">
              Preview GLB
              <input
                type="file"
                accept=".glb,model/gltf-binary"
                className="hidden"
                onChange={(event) => onGlbFile(event.target.files?.[0] ?? null)}
              />
            </label>
            {glbUrl && (
              <button type="button" className="rounded-md bg-white/95 px-3 py-2 text-xs font-medium shadow" onClick={() => onGlbFile(null)}>
                Use demo room
              </button>
            )}
          </div>
          {glbUrl && (
            <p className="absolute right-3 bottom-16 max-w-xs rounded-md bg-white/95 px-3 py-2 text-xs text-slate-700 shadow">
              Local GLB preview only. The file is not uploaded, and its coordinates are not aligned to these pins.
            </p>
          )}
          {placement && (
            <div className="pointer-events-auto absolute inset-x-0 bottom-4 flex justify-center">
              <div className="flex items-center gap-3 rounded-full bg-slate-900 px-4 py-2 text-sm text-white shadow">
                <span>Click the floor to set X and Z. Height stays editable.</span>
                <button type="button" className="rounded-full bg-white/15 px-2 py-1 text-xs" onClick={() => setPlacement(null)}>
                  Cancel
                </button>
              </div>
            </div>
          )}
          {actionError && (
            <div className="pointer-events-auto absolute bottom-4 left-3 max-w-sm rounded-md bg-red-50 px-3 py-2 text-sm text-red-800 shadow" role="alert">
              {actionError}
            </div>
          )}
        </div>
      </main>

      <DetailDrawer
        object={shown}
        zones={zones}
        scanLabel={scan?.label ?? null}
        observations={observations}
        annotations={annotations}
        coords={coords}
        note={note}
        saving={saving}
        onCoords={(patch) => setCoords((current) => ({ ...current, ...patch }))}
        onObject={(patch) =>
          setEdit((current) =>
            current
              ? {
                  ...current,
                  ...patch,
                  description: patch.description ?? current.description,
                  serial_number: patch.serial_number ?? current.serial_number,
                }
              : current,
          )
        }
        onSaveObject={(event) => void onSaveObject(event)}
        onSavePosition={(event) => void onSavePosition(event)}
        onMovePin={() => setPlacement("move")}
        onRecord={() => setPlacement("record")}
        onNote={(patch) => setNote((current) => ({ ...current, ...patch }))}
        onAddNote={(event) => void onAddNote(event)}
      />
    </div>
    </div>
  );
}
