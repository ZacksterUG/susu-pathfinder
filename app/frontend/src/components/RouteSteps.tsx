import type { RouteStep } from "../types";
import "./RouteSteps.css";

interface Props {
  steps: RouteStep[];
  current: number;
  onChange: (idx: number) => void;
}

export default function RouteSteps({ steps, current, onChange }: Props) {
  if (steps.length === 0) return null;

  return (
    <div className="route-steps">
      <div className="route-steps__list">
        {steps.map((step, i) => (
          <button
            key={i}
            className={`route-steps__item ${
              i === current ? "route-steps__item--active" : ""
            }`}
            onClick={() => onChange(i)}
          >
            <span className="route-steps__num">{i + 1}</span>
            <span className="route-steps__label">{step.label}</span>
          </button>
        ))}
      </div>
      <div className="route-steps__nav">
        <button
          className="route-steps__nav-btn"
          disabled={current <= 0}
          onClick={() => onChange(current - 1)}
        >
          ← Назад
        </button>
        <span className="route-steps__counter">
          {current + 1} / {steps.length}
        </span>
        <button
          className="route-steps__nav-btn"
          disabled={current >= steps.length - 1}
          onClick={() => onChange(current + 1)}
        >
          Далее →
        </button>
      </div>
    </div>
  );
}
