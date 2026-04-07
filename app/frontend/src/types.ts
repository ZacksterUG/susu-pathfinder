export interface Building {
  id: string;
  name: string;
  short_name: string | null;
}

export interface Floor {
  id: string;
  building_id: string;
  floor_number: string;
  corridor_points: { points: { x: number; y: number }[] } | null;
}

export interface Room {
  id: string;
  building_id: string;
  floor_number: string;
  number: string;
  name: string | null;
  room_type: string | null;
  coordinates: { points: { x: number; y: number }[] } | null;
}

export interface Technical {
  id: string;
  building_id: string;
  floor_number: string;
  name: string | null;
  type: string;
  coordinates: { points: { x: number; y: number }[] } | null;
  has_entrance: boolean;
  linked: string[];
}

export interface Entrance {
  object_id: string;
  object_type: string;
  building_id: string;
  floor_number: string;
  x: number;
  y: number;
  room_number: string | null;
}

export interface Grid {
  building_id: string;
  floor_number: string;
  cell_size: number;
  nodes: { x: number; y: number }[];
  edges: { from: number; to: number; weight: number }[];
  entrance_connections: Record<string, unknown>[];
}

export type TechnicalType =
  | "Лестница"
  | "Лифт"
  | "Туалет"
  | "Охрана"
  | "Подсобное"
  | "Гардероб"
  | "Пункт питания";

// ─── Route ───────────────────────────────────────────────────

export interface PathSegment {
  floor_number: string;
  nodes: { x: number; y: number }[];
}

export interface PathResponse {
  found: boolean;
  path: PathSegment[];
  total_length: number;
  floor_transitions: [string, string][];
  error: string | null;
}

export interface RouteStep {
  label: string;
  type: "walk" | "transition";
  floor_number: string;
  nodes: { x: number; y: number }[];
}
