import React from "react";
import "./examplecards.css";

const EXAMPLES = [
  {
    text: "Ask me reflective questions to understand my core values.",
    icon: (
      <svg width="17" height="17" viewBox="0 0 24 24" fill="none">
        <path d="M12 2l2.4 7.4H22l-6.2 4.5 2.4 7.4L12 17l-6.2 4.3 2.4-7.4L2 9.4h7.6L12 2z"
          fill="rgba(157,135,245,0.7)" stroke="rgba(157,135,245,0.4)" strokeWidth="0.5"/>
      </svg>
    ),
  },
  {
    text: "Help me manage stress and calm my mind.",
    icon: (
      <svg width="17" height="17" viewBox="0 0 24 24" fill="none">
        <circle cx="12" cy="12" r="9" fill="rgba(140,180,255,0.25)" stroke="rgba(140,180,255,0.5)" strokeWidth="1.2"/>
        <circle cx="12" cy="12" r="5" fill="rgba(140,180,255,0.35)"/>
        <circle cx="12" cy="12" r="2" fill="rgba(200,220,255,0.7)"/>
      </svg>
    ),
  },
  {
    text: "Teach me how to build healthier habits.",
    icon: (
      <svg width="17" height="17" viewBox="0 0 24 24" fill="none">
        <path d="M12 22c5.5 0 10-4.5 10-10S17.5 2 12 2 2 6.5 2 12s4.5 10 10 10z"
          fill="rgba(180, 230, 175, 0.2)" stroke="rgba(140, 210, 135, 0.5)" strokeWidth="1.2"/>
        <path d="M8 12l3 3 5-5" stroke="rgba(140,210,135,0.85)" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
      </svg>
    ),
  },
];

export default function ExampleCards({ onSelectExample }) {
  return (
    <div className="examples-row">
      {EXAMPLES.map((ex, i) => (
        <button
          key={i}
          className="example-card"
          type="button"
          onClick={() => onSelectExample?.(ex.text)}
        >
          <div className="example-text">{ex.text}</div>
          <div className="example-icon">{ex.icon}</div>
        </button>
      ))}
    </div>
  );
}