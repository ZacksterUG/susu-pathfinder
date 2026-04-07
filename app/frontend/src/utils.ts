import type { TechnicalType } from "./types";

/** Цвета для типов объектов на карте */
export const TYPE_COLORS: Record<TechnicalType | string, string> = {
  "Лестница": "#4a90d9",
  "Лифт": "#e67e22",
  "Туалет": "#1abc9c",
  "Охрана": "#e74c3c",
  "Подсобное": "#95a5a6",
  "Гардероб": "#9b59b6",
  "Пункт питания": "#f39c12",
  "Учебная аудитория": "#3498db",
  "Учебная лаборатория": "#2ecc71",
  "Компьютерный класс": "#1abc9c",
  "Административное помещение": "#8e44ad",
  "Помещение административно-хозяйственной части": "#7f8c8d",
  "Научная лаборатория": "#27ae60",
};

/** Цвет коридора */
export const CORRIDOR_COLOR = "rgba(200, 200, 200, 0.3)";

/** Цвет фона карты */
export const MAP_BG = "#f8f9fa";

/** Получить цвет по типу объекта */
export function getColorForType(type: string): string {
  return TYPE_COLORS[type] || "#999";
}

/** Преобразовать полигон в SVG points string */
export function pointsToSvgPoints(
  points: { x: number; y: number }[]
): string {
  return points.map((p) => `${p.x},${p.y}`).join(" ");
}

/** Вычислить bounding box набора полигонов */
export function getBoundingBox(
  polygons: { points: { x: number; y: number }[] }[]
): { minX: number; minY: number; maxX: number; maxY: number } {
  let minX = Infinity,
    minY = Infinity,
    maxX = -Infinity,
    maxY = -Infinity;
  for (const poly of polygons) {
    for (const p of poly.points) {
      if (p.x < minX) minX = p.x;
      if (p.y < minY) minY = p.y;
      if (p.x > maxX) maxX = p.x;
      if (p.y > maxY) maxY = p.y;
    }
  }
  if (!isFinite(minX)) {
    minX = 0;
    minY = 0;
    maxX = 1000;
    maxY = 1000;
  }
  return { minX, minY, maxX, maxY };
}
