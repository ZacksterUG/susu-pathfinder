import { useState, useEffect, useMemo, useCallback } from "react";
import type {
  Building,
  Floor,
  Room,
  PathResponse,
  RouteStep,
} from "../types";
import * as api from "../api";
import RouteMap from "./RouteMap";
import RouteSteps from "./RouteSteps";
import "./RouteModal.css";

interface Props {
  buildings: Building[];
  onClose: () => void;
}

export default function RouteModal({ buildings, onClose }: Props) {
  // Point A
  const [aBuilding, setABuilding] = useState<Building | null>(null);
  const [aFloors, setAFloors] = useState<Floor[]>([]);
  const [aFloor, setAFloor] = useState<Floor | null>(null);
  const [aRooms, setARooms] = useState<Room[]>([]);
  const [aRoom, setARoom] = useState<Room | null>(null);

  // Point B
  const [bBuilding, setBBuilding] = useState<Building | null>(null);
  const [bFloors, setBFloors] = useState<Floor[]>([]);
  const [bFloor, setBFloor] = useState<Floor | null>(null);
  const [bRooms, setBRooms] = useState<Room[]>([]);
  const [bRoom, setBRoom] = useState<Room | null>(null);

  // Route
  const [pathResult, setPathResult] = useState<PathResponse | null>(null);
  const [pathError, setPathError] = useState<string | null>(null);
  const [currentStep, setCurrentStep] = useState(0);
  const [buildingRoute, setBuildingRoute] = useState(false);

  // Load floors for A
  useEffect(() => {
    if (!aBuilding) {
      setAFloors([]);
      setAFloor(null);
      setARooms([]);
      setARoom(null);
      return;
    }
    api.fetchFloors(aBuilding.id).then((f) => {
      setAFloors(f);
      setAFloor(null);
      setARooms([]);
      setARoom(null);
    });
  }, [aBuilding]);

  // Load rooms for A floor
  useEffect(() => {
    if (!aBuilding || !aFloor) {
      setARooms([]);
      setARoom(null);
      return;
    }
    api
      .fetchRooms(aBuilding.id, aFloor.floor_number)
      .then((r) => setARooms(r.filter((x) => x.coordinates)));
  }, [aBuilding, aFloor]);

  // Load floors for B
  useEffect(() => {
    if (!bBuilding) {
      setBFloors([]);
      setBFloor(null);
      setBRooms([]);
      setBRoom(null);
      return;
    }
    api.fetchFloors(bBuilding.id).then((f) => {
      setBFloors(f);
      setBFloor(null);
      setBRooms([]);
      setBRoom(null);
    });
  }, [bBuilding]);

  // Load rooms for B floor
  useEffect(() => {
    if (!bBuilding || !bFloor) {
      setBRooms([]);
      setBRoom(null);
      return;
    }
    api
      .fetchRooms(bBuilding.id, bFloor.floor_number)
      .then((r) => setBRooms(r.filter((x) => x.coordinates)));
  }, [bBuilding, bFloor]);

  // Build route steps from path response
  const steps = useMemo<RouteStep[]>(() => {
    if (!pathResult || !pathResult.found) return [];
    const s: RouteStep[] = [];
    const path = pathResult.path;

    for (let i = 0; i < path.length; i++) {
      const seg = path[i];
      s.push({
        label: `Этаж ${seg.floor_number}`,
        type: "walk",
        floor_number: seg.floor_number,
        nodes: seg.nodes,
      });
      // Transition after this segment
      if (i < (pathResult.floor_transitions?.length || 0)) {
        const tr = pathResult.floor_transitions![i];
        s.push({
          label: `Переход ${tr[0]} → ${tr[1]}`,
          type: "transition",
          floor_number: tr[1],
          nodes: [],
        });
      }
    }
    return s;
  }, [pathResult]);

  // Current floor to display on map
  const currentFloorData = useMemo(() => {
    if (!steps.length || !aBuilding) return null;
    const step = steps[currentStep];
    if (!step) return null;
    return (
      aFloors.find((f) => f.floor_number === step.floor_number) ||
      bFloors.find((f) => f.floor_number === step.floor_number) ||
      null
    );
  }, [steps, currentStep, aBuilding, aFloors, bFloors]);

  const currentRoutePath = useMemo(() => {
    if (!steps.length) return undefined;
    const step = steps[currentStep];
    return step.type === "walk" ? step.nodes : undefined;
  }, [steps, currentStep]);

  const handleBuild = useCallback(async () => {
    if (!aRoom || !bRoom) return;

    setBuildingRoute(true);
    setPathResult(null);
    setPathError(null);
    setCurrentStep(0);

    try {
      const result = await api.findPath(
        aBuilding!.id,
        aRoom.id,
        bRoom.id
      );
      setPathResult(result);
      if (!result.found) {
        setPathError(result.error || "Путь не найден");
      }
    } catch {
      setPathError("Ошибка при запросе к серверу");
    } finally {
      setBuildingRoute(false);
    }
  }, [aRoom, bRoom, aBuilding]);

  const canBuild =
    aBuilding && aFloor && aRoom && bBuilding && bFloor && bRoom;
  const sameBuilding = aBuilding?.id === bBuilding?.id;

  return (
    <div className="route-modal__overlay" onClick={onClose}>
      <div className="route-modal" onClick={(e) => e.stopPropagation()}>
        <div className="route-modal__header">
          <h2 className="route-modal__title">Построить маршрут</h2>
          <button className="route-modal__close" onClick={onClose}>
            ✕
          </button>
        </div>

        <div className="route-modal__body">
          {/* Forms */}
          <div className="route-modal__forms">
            <div className="route-modal__form">
              <h3 className="route-modal__form-title">Откуда</h3>
              <select
                value={aBuilding?.id ?? ""}
                onChange={(e) => {
                  const b = buildings.find((x) => x.id === e.target.value);
                  setABuilding(b ?? null);
                }}
              >
                <option value="">— корпус —</option>
                {buildings.map((b) => (
                  <option key={b.id} value={b.id}>
                    {b.name}
                  </option>
                ))}
              </select>
              <select
                value={aFloor?.id ?? ""}
                disabled={!aBuilding}
                onChange={(e) => {
                  const f = aFloors.find((x) => x.id === e.target.value);
                  setAFloor(f ?? null);
                }}
              >
                <option value="">— этаж —</option>
                {[...aFloors]
                  .sort(
                    (a, b) =>
                      Number(a.floor_number) - Number(b.floor_number)
                  )
                  .map((f) => (
                    <option key={f.id} value={f.id}>
                      {f.floor_number}
                    </option>
                  ))}
              </select>
              <select
                value={aRoom?.id ?? ""}
                disabled={!aFloor}
                onChange={(e) => {
                  const r = aRooms.find((x) => x.id === e.target.value);
                  setARoom(r ?? null);
                }}
              >
                <option value="">— кабинет —</option>
                {aRooms.map((r) => (
                  <option key={r.id} value={r.id}>
                    №{r.number}
                  </option>
                ))}
              </select>
            </div>

            <div className="route-modal__form">
              <h3 className="route-modal__form-title">Куда</h3>
              <select
                value={bBuilding?.id ?? ""}
                onChange={(e) => {
                  const b = buildings.find((x) => x.id === e.target.value);
                  setBBuilding(b ?? null);
                }}
              >
                <option value="">— корпус —</option>
                {buildings.map((b) => (
                  <option key={b.id} value={b.id}>
                    {b.name}
                  </option>
                ))}
              </select>
              <select
                value={bFloor?.id ?? ""}
                disabled={!bBuilding}
                onChange={(e) => {
                  const f = bFloors.find((x) => x.id === e.target.value);
                  setBFloor(f ?? null);
                }}
              >
                <option value="">— этаж —</option>
                {[...bFloors]
                  .sort(
                    (a, b) =>
                      Number(a.floor_number) - Number(b.floor_number)
                  )
                  .map((f) => (
                    <option key={f.id} value={f.id}>
                      {f.floor_number}
                    </option>
                  ))}
              </select>
              <select
                value={bRoom?.id ?? ""}
                disabled={!bFloor}
                onChange={(e) => {
                  const r = bRooms.find((x) => x.id === e.target.value);
                  setBRoom(r ?? null);
                }}
              >
                <option value="">— кабинет —</option>
                {bRooms.map((r) => (
                  <option key={r.id} value={r.id}>
                    №{r.number}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {!sameBuilding && (
            <p className="route-modal__warning">
              ⚠ Комнаты в разных корпусах — путь не может быть построен
            </p>
          )}

          <button
            className="route-modal__build-btn"
            disabled={!canBuild || !sameBuilding || buildingRoute}
            onClick={handleBuild}
          >
            {buildingRoute ? "Построение..." : "Построить"}
          </button>

          {pathError && (
            <p className="route-modal__error">{pathError}</p>
          )}

          {/* Route map */}
          {pathResult?.found && (
            <div className="route-modal__result">
              <RouteMap
                buildingId={aBuilding!.id}
                floor={currentFloorData}
                routePath={currentRoutePath}
                startRoom={aRoom}
                endRoom={bRoom}
              />
              <RouteSteps
                steps={steps}
                current={currentStep}
                onChange={setCurrentStep}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
