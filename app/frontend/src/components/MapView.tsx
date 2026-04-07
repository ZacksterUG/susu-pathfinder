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
  onTypesChange: (types: string[]) => void;
}

export default function MapView({ buildingId, floor, onTypesChange }: Props) {
  const [rooms, setRooms] = useState<Room[]>([]);
  const [technical, setTechnical] = useState<Technical[]>([]);
  const [entrances, setEntrances] = useState<Entrance[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedObj, setSelectedObj] = useState<{
    label: string;
    color: string;
    x: number;
    y: number;
  } | null>(null);

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

  // Bounding box для viewbox
  const bbox = useMemo(() => {
    const all: { points: { x: number; y: number }[] }[] = [];
    if (floor?.corridor_points) {
      all.push(floor.corridor_points);
    }
    rooms.forEach((r) => r.coordinates && all.push(r.coordinates));
    technical.forEach((t) => t.coordinates && all.push(t.coordinates));
    return getBoundingBox(all);
  }, [rooms, technical, floor]);

  const svgWidth = bbox.maxX - bbox.minX + 40;
  const svgHeight = bbox.maxY - bbox.minY + 40;
  const pad = 20;

  const showTooltip = (label: string, color: string, x: number, y: number) => {
    setSelectedObj({ label, color, x: x - bbox.minX + pad, y: y - bbox.minY + pad });
  };

  const handleObjClick = (
    _e: React.MouseEvent,
    label: string,
    color: string,
    points: { x: number; y: number }[]
  ) => {
    const cx = points.reduce((s, p) => s + p.x, 0) / points.length;
    const cy = points.reduce((s, p) => s + p.y, 0) / points.length;
    showTooltip(label, color, cx, cy);
  };

  // Список всех типов для легенды
  const allTypes = useMemo(() => {
    const t: string[] = [];
    rooms.forEach((r) => r.room_type && t.push(r.room_type));
    technical.forEach((x) => t.push(x.type));
    return t;
  }, [rooms, technical]);

  // Callback для передачи типов наверх
  useEffect(() => {
    onTypesChange(allTypes);
  }, [allTypes, onTypesChange]);

  // Авто-скрытие тултипа через 3 секунды
  useEffect(() => {
    if (!selectedObj) return;
    const timer = setTimeout(() => setSelectedObj(null), 3000);
    return () => clearTimeout(timer);
  }, [selectedObj]);

  // Ширина тултипа по тексту
  const tooltipW = Math.max(selectedObj ? selectedObj.label.length * 7 + 30 : 0, 80);

  if (!floor) {
    return <div className="map-view map-view--empty">Выберите корпус и этаж</div>;
  }

  if (loading) {
    return <div className="map-view map-view--loading">Загрузка...</div>;
  }

  return (
    <div className="map-view">
      <TransformWrapper
        initialScale={1}
        minScale={0.1}
        maxScale={20}
        smooth
        wheel={{ step: 0.0005, smoothStep: 0.0001 }}
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
                        x: p.x - bbox.minX + pad,
                        y: p.y - bbox.minY + pad,
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
                  return (
                    <g
                      key={room.id}
                      className="map-view__room"
                      onClick={(e) =>
                        handleObjClick(
                          e,
                          room.room_type ?? room.name ?? room.number,
                          color,
                          room.coordinates.points
                        )
                      }
                    >
                      <polygon
                        points={pointsToSvgPoints(
                          room.coordinates.points.map((p) => ({
                            x: p.x - bbox.minX + pad,
                            y: p.y - bbox.minY + pad,
                          }))
                        )}
                        fill={color}
                        fillOpacity={0.6}
                        stroke={color}
                        strokeWidth={1.5}
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
                    <g
                      key={t.id}
                      className="map-view__room"
                      onClick={() =>
                        handleObjClick(
                          {} as React.MouseEvent,
                          t.type,
                          color,
                          t.coordinates.points
                        )
                      }
                    >
                      <polygon
                        points={pointsToSvgPoints(
                          t.coordinates.points.map((p) => ({
                            x: p.x - bbox.minX + pad,
                            y: p.y - bbox.minY + pad,
                          }))
                        )}
                        fill={color}
                        fillOpacity={0.6}
                        stroke={color}
                        strokeWidth={1.5}
                      />
                    </g>
                  );
                })}

                {/* Входы */}
                {entrances.map((ent) => {
                  const ex = ent.x - bbox.minX + pad;
                  const ey = ent.y - bbox.minY + pad;
                  return (
                    <g
                      key={ent.object_id}
                      className="map-view__entrance"
                      onClick={() => {
                        const label = `${ent.room_number || ent.object_type} (Вход)`;
                        showTooltip(label, "#e74c3c", ent.x, ent.y);
                      }}
                    >
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

                {/* SVG Тултип */}
                {selectedObj && (
                  <g className="map-view__tooltip-svg">
                    <rect
                      x={selectedObj.x - tooltipW / 2}
                      y={selectedObj.y - 28}
                      width={tooltipW}
                      height={22}
                      rx={4}
                      fill="rgba(0,0,0,0.85)"
                    />
                    <rect
                      x={selectedObj.x - tooltipW / 2 + 6}
                      y={selectedObj.y - 23}
                      width={10}
                      height={12}
                      rx={2}
                      fill={selectedObj.color}
                    />
                    <text
                      x={selectedObj.x - tooltipW / 2 + 22}
                      y={selectedObj.y - 12}
                      fill="#fff"
                      fontSize="11"
                      fontWeight="500"
                    >
                      {selectedObj.label}
                    </text>
                  </g>
                )}
              </svg>
            </TransformComponent>
          </>
        )}
      </TransformWrapper>
    </div>
  );
}
