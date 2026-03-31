import { memo, useCallback, useState } from "react";
import "./toneselector.css";

const TONES = [
  {
    id: "assertive",
    label: "Assertive",
    gradient: "radial-gradient(circle at 30% 20%, #f0e4f8, #d4b5e9 35%, #a87cc9 80%)",
    glow: "rgba(168, 124, 201, 0.12)",
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
      </svg>
    ),
  },
  {
    id: "tender",
    label: "Tender",
    gradient: "radial-gradient(circle at 30% 20%, #e4f5e7, #b5deba 35%, #7cb88a 80%)",
    glow: "rgba(124, 184, 138, 0.12)",
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M20.84 4.61a5.5 5.5 0 00-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 00-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 000-7.78z" />
      </svg>
    ),
  },
  {
    id: "empathy",
    label: "Empathy",
    gradient: "radial-gradient(circle at 30% 20%, #faf0e4, #e8d0a8 35%, #c9a867 80%)",
    glow: "rgba(201, 168, 103, 0.12)",
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9" />
        <path d="M13.73 21a2 2 0 01-3.46 0" />
      </svg>
    ),
  },
  {
    id: "neutral",
    label: "Neutral",
    gradient: "radial-gradient(circle at 30% 20%, #e9e6f6, #bfaaff 35%, #7c6adf 80%)",
    glow: "rgba(204, 190, 255, 0.12)",
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="10" />
        <path d="M8 14s1.5 2 4 2 4-2 4-2" />
        <line x1="9" y1="9" x2="9.01" y2="9" />
        <line x1="15" y1="9" x2="15.01" y2="9" />
      </svg>
    ),
  },
];

const ToneButton = memo(function ToneButton({ tone, active, onSelect }) {
  const handleClick = useCallback(() => onSelect(tone.id), [onSelect, tone.id]);
  const [hovered, setHovered] = useState(false);

  return (
    <div className="tone-btn-wrap">
      <button
        className={"tone-btn" + (active ? " active" : "")}
        onClick={handleClick}
        onMouseEnter={() => setHovered(true)}
        onMouseLeave={() => setHovered(false)}
        type="button"
      >
        {tone.icon}
      </button>
      {hovered && <div className="tone-tooltip">{tone.label}</div>}
    </div>
  );
});

export { TONES };

export default function ToneSelector({ activeTone, onToneChange }) {
  return (
    <div className="tone-group">
      {TONES.map((t) => (
        <ToneButton
          key={t.id}
          tone={t}
          active={activeTone === t.id}
          onSelect={onToneChange}
        />
      ))}
    </div>
  );
}
