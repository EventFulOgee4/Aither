import { useState } from "react";
import Shimmer from "../Shimmer/Shimmer";
import "./thinking.css";

export default function Thinking() {
  const [expanded, setExpanded] = useState(true);

  return (
    <div className="thinking-wrap">
      <button
        className="thinking-trigger"
        onClick={() => setExpanded(!expanded)}
        type="button"
      >
        <span className="thinking-brain">🧠</span>
        <Shimmer duration={1.8} spread={2}>Thinking...</Shimmer>
        <svg
          className={"thinking-chevron" + (expanded ? " open" : "")}
          width="12"
          height="12"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M6 9l6 6 6-6" />
        </svg>
      </button>
      {expanded && (
        <div className="thinking-content">
          <div className="thinking-dots">
            <span /><span /><span />
          </div>
        </div>
      )}
    </div>
  );
}
