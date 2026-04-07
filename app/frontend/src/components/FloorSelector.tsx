import type { Floor } from "../types";
import "./FloorSelector.css";

interface Props {
  floors: Floor[];
  selected: Floor | null;
  onSelect: (f: Floor) => void;
}

export default function FloorSelector({ floors, selected, onSelect }: Props) {
  const sorted = [...floors].sort(
    (a, b) => Number(a.floor_number) - Number(b.floor_number)
  );

  return (
    <div className="floor-selector">
      <label className="floor-selector__label">Этаж</label>
      <div className="floor-selector__buttons">
        {sorted.map((f) => (
          <button
            key={f.id}
            className={`floor-selector__btn ${
              selected?.id === f.id ? "floor-selector__btn--active" : ""
            }`}
            onClick={() => onSelect(f)}
          >
            {f.floor_number}
          </button>
        ))}
      </div>
    </div>
  );
}
