import type { FormEvent } from "react";
import type { Annotation, InventoryObject, Observation, Zone } from "../types";

function formatWhen(value: string): string {
  return new Date(value).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
}

function sourceLabel(source: string): string {
  if (source === "manual") return "Manual entry";
  if (source === "model") return "Model output";
  return source;
}

export function DetailDrawer({
  object,
  zones,
  scanLabel,
  observations,
  annotations,
  coords,
  note,
  saving,
  onCoords,
  onObject,
  onSaveObject,
  onSavePosition,
  onMovePin,
  onRecord,
  onNote,
  onAddNote,
}: {
  object: InventoryObject | null;
  zones: Zone[];
  scanLabel: string | null;
  observations: Observation[];
  annotations: Annotation[];
  coords: { x: string; y: string; z: string; zoneId: string; notes: string };
  note: { title: string; body: string; external_url: string };
  saving: boolean;
  onCoords: (patch: Partial<{ x: string; y: string; z: string; zoneId: string; notes: string }>) => void;
  onObject: (patch: Partial<Pick<InventoryObject, "name" | "category" | "description" | "serial_number">>) => void;
  onSaveObject: (event: FormEvent) => void;
  onSavePosition: (event: FormEvent) => void;
  onMovePin: () => void;
  onRecord: () => void;
  onNote: (patch: Partial<{ title: string; body: string; external_url: string }>) => void;
  onAddNote: (event: FormEvent) => void;
}) {
  if (!object) {
    return (
      <aside className="flex h-full items-center border-l border-slate-200 bg-white px-6">
        <p className="text-sm leading-6 text-slate-500">Select an equipment row or a pin to see its record.</p>
      </aside>
    );
  }

  const observation = object.scan_observation;

  return (
    <aside className="h-full min-h-0 overflow-y-auto border-l border-slate-200 bg-white">
      <div className="space-y-5 px-4 py-4">
        <div>
          <p className="text-xs font-semibold tracking-wide text-slate-500 uppercase">{object.category}</p>
          <h2 className="text-xl font-semibold text-slate-900">{object.name}</h2>
          <p className="mt-2 text-xs text-slate-500">Stable object identity. A pin is one scan observation, not the object's only location.</p>
        </div>

        {observation ? (
          <div className="rounded-lg border border-teal-200 bg-teal-50 px-3 py-3">
            <p className="text-xs font-semibold tracking-wide text-teal-900 uppercase">Last observed</p>
            <p className="mt-1 text-sm text-teal-950">{formatWhen(observation.observed_at)}</p>
            <p className="mt-1 text-xs text-teal-900">
              {sourceLabel(observation.source)} during {observation.scan_label}
              {observation.zone_name ? ` · ${observation.zone_name}` : ""}
            </p>
          </div>
        ) : (
          <div className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-3" role="status">
            <p className="text-sm font-medium text-amber-950">Not observed in this scan</p>
            <p className="mt-1 text-xs leading-5 text-amber-900">
              {scanLabel ? `${scanLabel} has no observation for this object.` : "Choose a scan to see whether this object was recorded."} This
              does not mean the object is missing from the room.
            </p>
            <button type="button" className="mt-2 text-sm font-medium text-amber-950 underline" onClick={onRecord}>
              Record a manual observation
            </button>
          </div>
        )}

        <form className="space-y-2" onSubmit={onSaveObject}>
          <h3 className="text-sm font-semibold text-slate-800">Record</h3>
          <label className="block text-xs text-slate-600" htmlFor="obj-name">
            Name
          </label>
          <input
            id="obj-name"
            className="w-full rounded-md border border-slate-300 px-2 py-1.5 text-sm"
            value={object.name}
            onChange={(event) => onObject({ name: event.target.value })}
          />
          <label className="block text-xs text-slate-600" htmlFor="obj-category">
            Category
          </label>
          <input
            id="obj-category"
            className="w-full rounded-md border border-slate-300 px-2 py-1.5 text-sm"
            value={object.category}
            onChange={(event) => onObject({ category: event.target.value })}
          />
          <label className="block text-xs text-slate-600" htmlFor="obj-serial">
            Serial number
          </label>
          <input
            id="obj-serial"
            className="w-full rounded-md border border-slate-300 px-2 py-1.5 text-sm"
            value={object.serial_number ?? ""}
            onChange={(event) => onObject({ serial_number: event.target.value })}
          />
          <label className="block text-xs text-slate-600" htmlFor="obj-description">
            Description
          </label>
          <textarea
            id="obj-description"
            className="h-20 w-full rounded-md border border-slate-300 px-2 py-1.5 text-sm"
            value={object.description ?? ""}
            onChange={(event) => onObject({ description: event.target.value })}
          />
          <button type="submit" disabled={saving} className="rounded-md bg-slate-900 px-3 py-1.5 text-sm text-white disabled:opacity-60">
            Save record
          </button>
        </form>

        <form className="space-y-2" onSubmit={onSavePosition}>
          <h3 className="text-sm font-semibold text-slate-800">Location in this scan</h3>
          <p className="text-xs leading-5 text-slate-500">
            Right-handed meters, Y up, origin at the center of the demo floor. {sourceLabel(observation?.source ?? "manual")}.
          </p>
          <div className="grid grid-cols-3 gap-2">
            {(["x", "y", "z"] as const).map((axis) => (
              <label key={axis} className="text-xs text-slate-600">
                {axis.toUpperCase()}
                <input
                  inputMode="decimal"
                  className="mt-1 w-full rounded-md border border-slate-300 px-2 py-1.5 text-sm"
                  value={coords[axis]}
                  onChange={(event) => onCoords({ [axis]: event.target.value })}
                />
              </label>
            ))}
          </div>
          <label className="block text-xs text-slate-600" htmlFor="obs-zone">
            Zone
          </label>
          <select
            id="obs-zone"
            className="w-full rounded-md border border-slate-300 px-2 py-1.5 text-sm"
            value={coords.zoneId}
            onChange={(event) => onCoords({ zoneId: event.target.value })}
          >
            <option value="">Unzoned</option>
            {zones.map((zone) => (
              <option key={zone.id} value={zone.id}>
                {zone.name}
              </option>
            ))}
          </select>
          <label className="block text-xs text-slate-600" htmlFor="obs-notes">
            Observation notes
          </label>
          <textarea
            id="obs-notes"
            className="h-16 w-full rounded-md border border-slate-300 px-2 py-1.5 text-sm"
            value={coords.notes}
            onChange={(event) => onCoords({ notes: event.target.value })}
          />
          <div className="flex gap-2">
            <button type="submit" disabled={saving} className="rounded-md bg-slate-900 px-3 py-1.5 text-sm text-white disabled:opacity-60">
              {observation ? "Save position" : "Save observation"}
            </button>
            <button type="button" className="rounded-md border border-slate-300 px-3 py-1.5 text-sm" onClick={observation ? onMovePin : onRecord}>
              {observation ? "Move pin" : "Click floor to place"}
            </button>
          </div>
        </form>

        <section>
          <h3 className="text-sm font-semibold text-slate-800">Notes and links</h3>
          {annotations.length === 0 && <p className="mt-2 text-sm text-slate-500">No notes yet.</p>}
          <ul className="mt-2 space-y-2">
            {annotations.map((item) => (
              <li key={item.id} className="rounded-md border border-slate-200 px-3 py-2">
                <p className="text-sm font-medium">{item.title}</p>
                <p className="mt-1 text-sm whitespace-pre-wrap text-slate-700">{item.body}</p>
                {item.external_url && (
                  <a className="mt-1 block text-sm text-teal-800 underline" href={item.external_url} target="_blank" rel="noreferrer">
                    {item.external_url}
                  </a>
                )}
              </li>
            ))}
          </ul>
          <form className="mt-3 space-y-2" onSubmit={onAddNote}>
            <input
              aria-label="Note title"
              placeholder="Title"
              className="w-full rounded-md border border-slate-300 px-2 py-1.5 text-sm"
              value={note.title}
              onChange={(event) => onNote({ title: event.target.value })}
            />
            <textarea
              aria-label="Note body"
              placeholder="Note"
              className="h-16 w-full rounded-md border border-slate-300 px-2 py-1.5 text-sm"
              value={note.body}
              onChange={(event) => onNote({ body: event.target.value })}
            />
            <input
              aria-label="Documentation URL"
              placeholder="https://example.com/manual"
              className="w-full rounded-md border border-slate-300 px-2 py-1.5 text-sm"
              value={note.external_url}
              onChange={(event) => onNote({ external_url: event.target.value })}
            />
            <button type="submit" disabled={saving} className="rounded-md border border-slate-300 px-3 py-1.5 text-sm disabled:opacity-60">
              Add note
            </button>
          </form>
        </section>

        <section>
          <h3 className="text-sm font-semibold text-slate-800">Observation history</h3>
          <p className="mt-1 text-xs leading-5 text-slate-500">
            Each row is evidence from one scan. PlaceBrain does not automatically decide that an object moved or disappeared.
          </p>
          {observations.length === 0 && <p className="mt-2 text-sm text-slate-500">No observations yet.</p>}
          <ul className="mt-2 space-y-2">
            {observations.map((item) => (
              <li key={item.id} className="rounded-md bg-slate-50 px-3 py-2 text-sm">
                <p className="font-medium text-slate-900">{item.scan_label}</p>
                <p className="text-slate-600">
                  {formatWhen(item.observed_at)} · {sourceLabel(item.source)}
                </p>
                <p className="text-slate-600">
                  {item.x.toFixed(2)}, {item.y.toFixed(2)}, {item.z.toFixed(2)} m
                  {item.zone_name ? ` · ${item.zone_name}` : ""}
                </p>
                {item.notes && <p className="mt-1 text-slate-700">{item.notes}</p>}
              </li>
            ))}
          </ul>
        </section>
      </div>
    </aside>
  );
}
