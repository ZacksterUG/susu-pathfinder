import type { Building } from "../types";
import "./BuildingSelector.css";

interface Props {
  buildings: Building[];
  selected: Building | null;
  onSelect: (b: Building) => void;
}

export default function BuildingSelector({
  buildings,
  selected,
  onSelect,
}: Props) {
  const sorted = [...buildings].sort((a, b) => a.name.localeCompare(b.name));

  return (
    <div className="building-selector">
      <label className="building-selector__label">Корпус</label>
      <select
        value={selected?.id ?? ""}
        onChange={(e) => {
          const b = buildings.find((b) => b.id === e.target.value);
          if (b) onSelect(b);
        }}
      >
        <option value="">— выберите корпус —</option>
        {sorted.map((b) => (
          <option key={b.id} value={b.id}>
            {b.name}
          </option>
        ))}
      </select>
    </div>
  );
}
