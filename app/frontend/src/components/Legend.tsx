import { TYPE_COLORS } from "../utils";
import "./Legend.css";

/** Уникальные типы, которые есть в текущем наборе */
interface Props {
  types: string[];
}

export default function Legend({ types }: Props) {
  const unique = [...new Set(types)].sort();

  return (
    <div className="legend">
      <h4 className="legend__title">Легенда</h4>
      <div className="legend__items">
        {unique.map((t) => (
          <div key={t} className="legend__item">
            <span
              className="legend__color"
              style={{ backgroundColor: TYPE_COLORS[t] || "#999" }}
            />
            <span className="legend__label">{t}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
