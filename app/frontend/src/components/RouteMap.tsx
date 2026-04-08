import { useEffect, useState, useMemo } from "react";
import { TransformWrapper, TransformComponent } from "react-zoom-pan-pinch";
import type { Room, Technical, Entrance, Floor } from "../types";
import * as api from "../api";
import {
  getColorForType,
  pointsToSvgPoints,
  getBoundingBox,
  MAP_BG,
} from "../utils";
import "./MapView.css";

interface Props {
  buildingId: string;
  floor: Floor | null;
  routePath?: { x: number; y: number }[];
  startRoom?: Room | null;
  endRoom?: Room | null;
}

export default function RouteMap({
  buildingId,
  floor,
  routePath,
  startRoom,
  endRoom,
}: Props) {
  const [rooms, setRooms] = useState<Room[]>([]);
  const [technical, setTechnical] = useState<Technical[]>([]);
  const [entrances, setEntrances] = useState<Entrance[]>([]);
  const [loading, setLoading] = useState(false);

  const fn = floor?.floor_number;

  useEffect(() => {
    if (!buildingId || !fn) {
      setRooms([]);
      setTechnical([]);
      setEntrances([]);
      return;
    }

    let cancelled = false;
    setLoading(true);

    Promise.all([
      api.fetchRooms(buildingId, fn),
      api.fetchTechnical(buildingId, fn),
      api.fetchEntrances(buildingId, fn),
    ]).then(([r, t, e]) => {
      if (!cancelled) {
        setRooms(r);
        setTechnical(t);
        setEntrances(e);
        setLoading(false);
      }
    });

    return () => {
      cancelled = true;
    };
  }, [buildingId, fn]);

  const bbox = useMemo(() => {
    const all: { points: { x: number; y: number }[] }[] = [];
    if (floor?.corridor_points) {
      all.push(floor.corridor_points);
    }
    rooms.forEach((r) => r.coordinates && all.push(r.coordinates));
    technical.forEach((t) => t.coordinates && all.push(t.coordinates));
    if (routePath && routePath.length > 0) {
      all.push({ points: routePath });
    }
    return getBoundingBox(all);
  }, [rooms, technical, floor, routePath]);

  const svgWidth = bbox.maxX - bbox.minX + 40;
  const svgHeight = bbox.maxY - bbox.minY + 40;
  const pad = 20;

  if (!floor) {
    return (
      <div className="map-view map-view--empty">
        Выберите этажи для построения маршрута
      </div>
    );
  }

  if (loading) {
    return <div className="map-view map-view--loading">Загрузка...</div>;
  }

  // Helper to transform coords
  const tx = (x: number) => x - bbox.minX + pad;
  const ty = (y: number) => y - bbox.minY + pad;

  return (
    <div className="map-view">
      <TransformWrapper
        initialScale={1}
        minScale={0.1}
        maxScale={20}
        smooth
        wheel={{ step: 0.0005 }}
        panning={{ activationKeys: [], velocityDisabled: true }}
        doubleClick={{ disabled: true }}
        limitToBounds={false}
        centerOnInit
      >
        {({ zoomIn, zoomOut, resetTransform }) => (
          <>
            <div className="map-view__controls">
              <button onClick={() => zoomIn()}>+</button>
              <button onClick={() => zoomOut()}>−</button>
              <button onClick={() => resetTransform()}>⟲</button>
            </div>
            <TransformComponent
              wrapperStyle={{
                width: "100%",
                height: "100%",
                position: "relative",
              }}
            >
              <svg
                viewBox={`${-pad} ${-pad} ${svgWidth} ${svgHeight}`}
                width="100%"
                height="100%"
                style={{ backgroundColor: MAP_BG }}
              >
                {/* Коридор */}
                {floor?.corridor_points && (
                  <polygon
                    points={pointsToSvgPoints(
                      floor.corridor_points.points.map((p) => ({
                        x: tx(p.x),
                        y: ty(p.y),
                      }))
                    )}
                    fill="rgba(170, 170, 170, 0.5)"
                    stroke="rgba(180, 180, 180, 0.6)"
                    strokeWidth={1.5}
                    strokeDasharray="4 2"
                    style={{ pointerEvents: "none" }}
                  />
                )}

                {/* Комнаты */}
                {rooms.map((room) => {
                  if (!room.coordinates?.points.length) return null;
                  const color = getColorForType(room.room_type ?? "");
                  const isStart = startRoom?.id === room.id;
                  const isEnd = endRoom?.id === room.id;
                  return (
                    <g key={room.id}>
                      <polygon
                        points={pointsToSvgPoints(
                          room.coordinates.points.map((p) => ({
                            x: tx(p.x),
                            y: ty(p.y),
                          }))
                        )}
                        fill={isStart ? "#2ecc71" : isEnd ? "#e74c3c" : color}
                        fillOpacity={isStart || isEnd ? 0.8 : 0.6}
                        stroke={isStart ? "#27ae60" : isEnd ? "#c0392b" : color}
                        strokeWidth={isStart || isEnd ? 2.5 : 1.5}
                      />
                      {svgWidth > 200 && (
                        <text
                          x={
                            room.coordinates.points.reduce((s, p) => s + p.x, 0) /
                              room.coordinates.points.length -
                            bbox.minX +
                            pad
                          }
                          y={
                            room.coordinates.points.reduce((s, p) => s + p.y, 0) /
                              room.coordinates.points.length -
                            bbox.minY +
                            pad
                          }
                          textAnchor="middle"
                          dominantBaseline="central"
                          fontSize="11"
                          fill="#333"
                        >
                          {room.number}
                        </text>
                      )}
                    </g>
                  );
                })}

                {/* Тех. помещения */}
                {technical.map((t) => {
                  if (!t.coordinates?.points.length) return null;
                  const color = getColorForType(t.type);
                  return (
                    <polygon
                      key={t.id}
                      points={pointsToSvgPoints(
                        t.coordinates.points.map((p) => ({
                          x: tx(p.x),
                          y: ty(p.y),
                        }))
                      )}
                      fill={color}
                      fillOpacity={0.6}
                      stroke={color}
                      strokeWidth={1.5}
                    />
                  );
                })}

                {/* Входы */}
                {entrances.map((ent) => {
                  const ex = tx(ent.x);
                  const ey = ty(ent.y);
                  return (
                    <g key={ent.object_id}>
                      <circle
                        cx={ex}
                        cy={ey}
                        r={6}
                        fill="#e74c3c"
                        stroke="#fff"
                        strokeWidth={2}
                      />
                    </g>
                  );
                })}

                {/* Маршрут */}
                {routePath && routePath.length > 1 && (
                  <polyline
                    points={pointsToSvgPoints(
                      routePath.map((p) => ({ x: tx(p.x), y: ty(p.y) }))
                    )}
                    fill="none"
                    stroke="#3498db"
                    strokeWidth={3}
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeDasharray="8 4"
                  />
                )}
              </svg>
            </TransformComponent>
          </>
        )}
      </TransformWrapper>
    </div>
  );
}
