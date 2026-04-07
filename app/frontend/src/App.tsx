import { useEffect, useState, useCallback } from "react";
import BuildingSelector from "./components/BuildingSelector";
import FloorSelector from "./components/FloorSelector";
import Legend from "./components/Legend";
import MapView from "./components/MapView";
import RouteModal from "./components/RouteModal";
import { fetchBuildings, fetchFloors } from "./api";
import type { Building, Floor } from "./types";
import "./App.css";

export default function App() {
  const [buildings, setBuildings] = useState<Building[]>([]);
  const [selectedBuilding, setSelectedBuilding] = useState<Building | null>(null);
  const [floors, setFloors] = useState<Floor[]>([]);
  const [selectedFloor, setSelectedFloor] = useState<Floor | null>(null);
  const [legendTypes, setLegendTypes] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [showRoute, setShowRoute] = useState(false);

  // Загрузка корпусов
  useEffect(() => {
    fetchBuildings().then((b) => {
      setBuildings(b);
      setLoading(false);
    });
  }, []);

  // Загрузка этажей при выборе корпуса
  useEffect(() => {
    if (!selectedBuilding) {
      setFloors([]);
      setSelectedFloor(null);
      return;
    }
    fetchFloors(selectedBuilding.id).then((f) => {
      setFloors(f);
      setSelectedFloor(null);
    });
  }, [selectedBuilding]);

  const handleBuildingSelect = useCallback((b: Building) => {
    setSelectedBuilding(b);
  }, []);

  const handleFloorSelect = useCallback((f: Floor) => {
    setSelectedFloor(f);
  }, []);

  if (loading) {
    return <div className="app__loading">Загрузка...</div>;
  }

  return (
    <div className="app">
      {/* Верхняя панель */}
      <header className="app__header">
        <h1 className="app__title">Карта корпусов</h1>
        <button
          className="app__route-btn"
          onClick={() => setShowRoute(true)}
        >
          🧭 Построить маршрут
        </button>
        <div className="app__selectors">
          <BuildingSelector
            buildings={buildings}
            selected={selectedBuilding}
            onSelect={handleBuildingSelect}
          />
          {floors.length > 0 && (
            <FloorSelector
              floors={floors}
              selected={selectedFloor}
              onSelect={handleFloorSelect}
            />
          )}
        </div>
      </header>

      {/* Основная область */}
      <main className="app__main">
        <div className="app__map-container">
          <MapView
            key={selectedFloor?.id ?? "none"}
            buildingId={selectedBuilding?.id ?? ""}
            floor={selectedFloor}
            onTypesChange={setLegendTypes}
          />
        </div>
        {legendTypes.length > 0 && (
          <aside className="app__sidebar">
            <Legend types={legendTypes} />
          </aside>
        )}
      </main>

      {/* Модалка маршрута */}
      {showRoute && (
        <RouteModal
          buildings={buildings}
          onClose={() => setShowRoute(false)}
        />
      )}
    </div>
  );
}
