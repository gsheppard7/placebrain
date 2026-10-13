import type {
  Annotation,
  InventoryObject,
  ObjectPage,
  Observation,
  Page,
  Scan,
  SceneAsset,
  Space,
  Zone,
} from "./types";

const BASE = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000";

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

function formatDetail(detail: unknown): string {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (!item || typeof item !== "object" || !("msg" in item)) return String(item);
        const record = item as { msg?: unknown; loc?: unknown[] };
        const loc = Array.isArray(record.loc) ? record.loc.filter((part) => part !== "body").map(String).join(".") : "";
        return loc ? `${loc}: ${String(record.msg)}` : String(record.msg);
      })
      .join(" ");
  }
  return "Request failed";
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  });
  if (!response.ok) {
    let message = response.statusText;
    try {
      const body = (await response.json()) as { detail?: unknown };
      message = formatDetail(body.detail);
    } catch {
      // Keep the HTTP status text when the body is not JSON.
    }
    throw new ApiError(response.status, message);
  }
  return (await response.json()) as T;
}

export const api = {
  listSpaces: () => request<Page<Space>>("/spaces?limit=50"),
  listZones: (spaceId: string) => request<{ items: Zone[]; total: number }>(`/spaces/${spaceId}/zones`),
  listScans: (spaceId: string) => request<Page<Scan>>(`/spaces/${spaceId}/scans?limit=50`),
  createScan: (spaceId: string, label: string) =>
    request<Scan>(`/spaces/${spaceId}/scans`, { method: "POST", body: JSON.stringify({ label, status: "manual" }) }),
  listObjects: (spaceId: string, scanId: string, q: string) => {
    const params = new URLSearchParams({ scan_id: scanId, limit: "100" });
    if (q.trim()) params.set("q", q.trim());
    return request<ObjectPage>(`/spaces/${spaceId}/objects?${params.toString()}`);
  },
  createObject: (spaceId: string, body: { name: string; category: string; description?: string; serial_number?: string }) =>
    request<InventoryObject>(`/spaces/${spaceId}/objects`, { method: "POST", body: JSON.stringify(body) }),
  updateObject: (
    objectId: string,
    body: Partial<Pick<InventoryObject, "name" | "category" | "description" | "serial_number">>,
  ) => request<InventoryObject>(`/objects/${objectId}`, { method: "PATCH", body: JSON.stringify(body) }),
  listObservations: (objectId: string) => request<{ items: Observation[] }>(`/objects/${objectId}/observations`),
  createObservation: (
    objectId: string,
    body: { scan_id: string; zone_id?: string | null; x: number; y: number; z: number; source: "manual"; notes?: string },
  ) => request<Observation>(`/objects/${objectId}/observations`, { method: "POST", body: JSON.stringify(body) }),
  updateObservation: (
    observationId: string,
    body: { zone_id?: string | null; x?: number; y?: number; z?: number; notes?: string },
  ) => request<Observation>(`/observations/${observationId}`, { method: "PATCH", body: JSON.stringify(body) }),
  listAnnotations: (objectId: string) => request<{ items: Annotation[] }>(`/objects/${objectId}/annotations`),
  createAnnotation: (objectId: string, body: { title: string; body: string; external_url?: string | null }) =>
    request<Annotation>(`/objects/${objectId}/annotations`, { method: "POST", body: JSON.stringify(body) }),
  listAssets: (scanId: string) => request<{ items: SceneAsset[] }>(`/scans/${scanId}/assets`),
};
