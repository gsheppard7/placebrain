export type ScanStatus = "manual" | "imported";
export type ObservationSource = "manual" | "model";
export type AssetType = "procedural" | "glb" | "gaussian_splat";

export interface Space {
  id: string;
  name: string;
  description: string | null;
  created_at: string;
  updated_at: string;
}

export interface Zone {
  id: string;
  space_id: string;
  name: string;
  parent_zone_id: string | null;
  created_at: string;
}

export interface Scan {
  id: string;
  space_id: string;
  label: string;
  captured_at: string;
  status: ScanStatus;
  notes: string | null;
  created_at: string;
}

export interface SceneAsset {
  id: string;
  scan_id: string;
  asset_type: AssetType;
  storage_uri: string;
  metadata_json: string | null;
  alignment_json: string | null;
  created_at: string;
}

export interface Observation {
  id: string;
  object_id: string;
  scan_id: string;
  scan_label: string;
  zone_id: string | null;
  zone_name: string | null;
  x: number;
  y: number;
  z: number;
  observed_at: string;
  source: ObservationSource;
  confidence: number | null;
  notes: string | null;
}

export interface InventoryObject {
  id: string;
  space_id: string;
  name: string;
  category: string;
  description: string | null;
  serial_number: string | null;
  created_at: string;
  updated_at: string;
  archived_at: string | null;
  scan_observation: Observation | null;
}

export interface Annotation {
  id: string;
  object_id: string;
  title: string;
  body: string;
  external_url: string | null;
  created_at: string;
  updated_at: string;
}

export interface Page<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

export interface ObjectPage extends Page<InventoryObject> {
  scan_id: string | null;
}
