import React from "react";
import "./examplecards.css";

function ExampleCard({ text, icon, onClick }) {
  return (
    <button className="example-card" type="button" onClick={onClick}>
      <div className="example-text">{text}</div>
      <div className="example-icon">{icon}</div>
    </button>
  );
}

export default function ExampleCards({ onSelectExample }) {
  const examples = [
    "Ask me reflective questions to understand my core values.",
    "Help me manage stress and calm my mind.",
    "Teach me how to build healthier habits.",
  ];

  return (
    <div className="examples-row">
      <ExampleCard
        text={examples[0]}
        onClick={() => onSelectExample?.(examples[0])}
        icon={
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
            <path
              d="M12 2l3 7h7l-5.7 4.1L20 22l-8-5-8 5 2.7-8.9L1 9h7l3-7z"
              fill="#9b8fe6"
            />
          </svg>
        }
      />

      <ExampleCard
        text={examples[1]}
        onClick={() => onSelectExample?.(examples[1])}
        icon={
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
            <circle cx="12" cy="12" r="8" fill="#d6ccff" />
          </svg>
        }
      />

      <ExampleCard
        text={examples[2]}
        onClick={() => onSelectExample?.(examples[2])}
        icon={
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
            <rect x="3" y="3" width="18" height="18" rx="4" fill="#e9e6f6" />
          </svg>
        }
      />
    </div>
  );
}