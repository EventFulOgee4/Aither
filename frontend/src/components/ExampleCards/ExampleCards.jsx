import React from "react";
import "./examplecards.css";

function ExampleCard({ text, icon }) {
  return (
    <div className="example-card">
      <div className="example-text">{text}</div>
      <div className="example-icon">{icon}</div>
    </div>
  );
}

export default function ExampleCards() {
  return (
    <div className="examples-row">
      <ExampleCard
        text="Ask me reflective questions to understand my core values."
        icon={
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
            <path
              d="M12 2l3 7h7l-5.7 4.1L20 22l-8-5-8 5 2.7-8.9L1 9h7l3-7z"
              stroke="currentColor"
              strokeWidth="0"
              fill="#9b8fe6"
            />
          </svg>
        }
      />
      <ExampleCard
        text="Help me manage stress and calm my mind."
        icon={
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
            <circle cx="12" cy="12" r="8" fill="#d6ccff" />
          </svg>
        }
      />
      <ExampleCard
        text="Teach me how to build healthier habits."
        icon={
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
            <rect x="3" y="3" width="18" height="18" rx="4" fill="#e9e6f6" />
          </svg>
        }
      />
    </div>
  );
}
