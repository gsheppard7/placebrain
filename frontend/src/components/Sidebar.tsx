import type { FormEvent } from "react";
import type { InventoryObject, Scan, Space } from "../types";

function sourceMark(object: InventoryObject): string {
  if (!object.scan_observation) return "Not observed in this scan";
  return object.scan_observation.source === "manual" ? "Manual pin" : "Model observation";
}

export function Sidebar({
  space,
  scans,
  scanId,
  query,
  objects,
  selectedId,
  loading,
  listLoading,
  error,
  adding,
  draft,
  zones,
  newObject,
  scanDraft,
  onQuery,
  onScan,
  onSelect,
  onRetry,
  onToggleAdd,
  onNewObject,
  onDraft,
  onCreateObject,
  onPlaceNew,
  onToggleScanDraft,
  onScanDraft,
  onCreateScan,
}: {
  space: Space | null;
  scans: Scan[];
  scanId: string | null;
  query: string;
  objects: InventoryObject[];
  selectedId: string | null;
  loading: boolean;
  listLoading: boolean;
  error: string | null;
  adding: boolean;
  draft: { x: number; y: number; z: number; zoneId: string };
  zones: { id: string; name: string }[];
  newObject: { name: string; category: string; description: string };
  scanDraft: string | null;
  onQuery: (value: string) => void;
  onScan: (scanId: string) => void;
  onSelect: (id: string) => void;
  onRetry: () => void;
  onToggleAdd: () => void;
  onNewObject: (patch: Partial<{ name: string; category: string; description: string }>) => void;
  onDraft: (patch: Partial<{ x: number; y: number; z: number; zoneId: string }>) => void;
  onCreateObject: () => void;
  onPlaceNew: () => void;
  onToggleScanDraft: () => void;
  onScanDraft: (value: string) => void;
  onCreateScan: (event: FormEvent) => void;
}) {
  const groups = new Map<string, InventoryObject[]>();
  for (const item of objects) {
    const list = groups.get(item.category) ?? [];
    list.push(item);
    groups.set(item.category, list);
  }

  return (
    <aside className="flex h-full min-h-0 flex-col border-r border-slate-200 bg-white">
      <div className="border-b border-slate-200 px-4 py-4">
        <p className="text-xs font-semibold tracking-wide text-teal-800 uppercase">PlaceBrain</p>
        <h1 className="mt-1 text-lg leading-snug font-semibold text-slate-900">{space?.name ?? "Equipment room"}</h1>
        <p className="mt-2 text-xs leading-5 text-slate-500">
          Demo inventory with manually entered locations. Nothing in this view is a computer-vision result.
        </p>
      </div>

      <div className="space-y-3 border-b border-slate-200 px-4 py-3">
        <label className="block text-xs font-medium text-slate-600" htmlFor="scan">
          Scan
        </label>
        <select
          id="scan"
          className="w-full rounded-md border border-slate-300 bg-white px-2 py-2 text-sm"
          value={scanId ?? ""}
          onChange={(event) => onScan(event.target.value)}
          disabled={!scans.length}
        >
          {scans.map((scan) => (
            <option key={scan.id} value={scan.id}>
              {scan.label} · {scan.status}
            </option>
          ))}
        </select>
        {scanDraft === null ? (
          <button type="button" className="text-sm font-medium text-teal-800" onClick={onToggleScanDraft}>
            New manual scan
          </button>
        ) : (
          <form className="flex gap-2" onSubmit={onCreateScan}>
            <input
              className="min-w-0 flex-1 rounded-md border border-slate-300 px-2 py-1.5 text-sm"
              value={scanDraft}
              onChange={(event) => onScanDraft(event.target.value)}
              placeholder="Scan label"
              aria-label="New scan label"
            />
            <button type="submit" className="rounded-md bg-slate-900 px-2 py-1.5 text-sm text-white">
              Add
            </button>
          </form>
        )}
        <label className="block text-xs font-medium text-slate-600" htmlFor="search">
          Search equipment
        </label>
        <input
          id="search"
          type="search"
          value={query}
          onChange={(event) => onQuery(event.target.value)}
          placeholder="Name, category, description"
          className="w-full rounded-md border border-slate-300 px-2 py-2 text-sm"
        />
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto px-2 py-2">
        {loading && <p className="px-2 py-3 text-sm text-slate-500">Loading the equipment room…</p>}
        {error && (
          <div className="m-2 rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-800" role="alert">
            <p>{error}</p>
            <button type="button" className="mt-2 font-medium underline" onClick={onRetry}>
              Retry
            </button>
          </div>
        )}
        {!loading && !error && listLoading && <p className="px-2 py-3 text-sm text-slate-500">Updating the list…</p>}
        {!loading && !error && !listLoading && objects.length === 0 && (
          <p className="px-2 py-3 text-sm text-slate-500">
            {query.trim() ? "No equipment matches that search." : "No inventory objects in this space yet."}
          </p>
        )}
        {[...groups.entries()].map(([category, items]) => (
          <section key={category} className="mb-3">
            <h2 className="px-2 py-1 text-xs font-semibold tracking-wide text-slate-500 uppercase">{category}</h2>
            <ul>
              {items.map((item) => {
                const observed = Boolean(item.scan_observation);
                const selected = item.id === selectedId;
                return (
                  <li key={item.id}>
                    <button
                      type="button"
                      onClick={() => onSelect(item.id)}
                      className={`w-full rounded-md px-2 py-2 text-left ${selected ? "bg-teal-50 ring-1 ring-teal-700" : "hover:bg-slate-50"}`}
                    >
                      <span className="block text-sm font-medium text-slate-900">{item.name}</span>
                      <span className={`mt-0.5 block text-xs ${observed ? "text-slate-500" : "text-amber-800"}`}>
                        {sourceMark(item)}
                      </span>
                    </button>
                  </li>
                );
              })}
            </ul>
          </section>
        ))}
      </div>

      <div className="border-t border-slate-200 p-3">
        <button
          type="button"
          onClick={onToggleAdd}
          className="w-full rounded-md bg-teal-800 px-3 py-2 text-sm font-medium text-white"
        >
          {adding ? "Close add form" : "Add object"}
        </button>
        {adding && (
          <form
            className="mt-3 space-y-2"
            onSubmit={(event) => {
              event.preventDefault();
              onCreateObject();
            }}
          >
            <input
              required
              aria-label="Object name"
              placeholder="Name"
              className="w-full rounded-md border border-slate-300 px-2 py-1.5 text-sm"
              value={newObject.name}
              onChange={(event) => onNewObject({ name: event.target.value })}
            />
            <input
              required
              aria-label="Category"
              placeholder="Category"
              className="w-full rounded-md border border-slate-300 px-2 py-1.5 text-sm"
              value={newObject.category}
              onChange={(event) => onNewObject({ category: event.target.value })}
            />
            <textarea
              aria-label="Description"
              placeholder="Description"
              className="h-16 w-full rounded-md border border-slate-300 px-2 py-1.5 text-sm"
              value={newObject.description}
              onChange={(event) => onNewObject({ description: event.target.value })}
            />
            <label className="block text-xs text-slate-600" htmlFor="new-zone">
              Zone
            </label>
            <select
              id="new-zone"
              className="w-full rounded-md border border-slate-300 px-2 py-1.5 text-sm"
              value={draft.zoneId}
              onChange={(event) => onDraft({ zoneId: event.target.value })}
            >
              <option value="">Unzoned</option>
              {zones.map((zone) => (
                <option key={zone.id} value={zone.id}>
                  {zone.name}
                </option>
              ))}
            </select>
            <div className="grid grid-cols-3 gap-2">
              {(["x", "y", "z"] as const).map((axis) => (
                <label key={axis} className="text-xs text-slate-600">
                  {axis.toUpperCase()}
                  <input
                    inputMode="decimal"
                    aria-label={`New object ${axis}`}
                    className="mt-1 w-full rounded-md border border-slate-300 px-2 py-1.5 text-sm"
                    value={Number.isFinite(draft[axis]) ? draft[axis] : 0}
                    onChange={(event) => {
                      const value = Number(event.target.value);
                      if (Number.isFinite(value)) onDraft({ [axis]: value });
                    }}
                  />
                </label>
              ))}
            </div>
            <div className="flex gap-2">
              <button type="button" className="flex-1 rounded-md border border-slate-300 px-2 py-1.5 text-sm" onClick={onPlaceNew}>
                Place on floor
              </button>
              <button type="submit" className="flex-1 rounded-md bg-slate-900 px-2 py-1.5 text-sm text-white">
                Save
              </button>
            </div>
          </form>
        )}
      </div>
    </aside>
  );
}
