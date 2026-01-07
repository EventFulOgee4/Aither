import React from "react";
import "./topbar.css";

export default function Topbar() {
  return (
    <div className="topbar">
      <div className="left-pill">
        <span className="pill-text">Aither_v1</span>
        <svg
          className="down"
          width="12"
          height="12"
          viewBox="0 0 24 24"
          fill="none"
        >
          <path
            d="M6 9l6 6 6-6"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </div>

      <div className="right-actions">
        <div className="pill search">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
            <path
              d="M21 21l-4.35-4.35"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
            <circle
              cx="11"
              cy="11"
              r="6"
              stroke="currentColor"
              strokeWidth="2"
            />
          </svg>
          <span>Search</span>
        </div>
        <div className="pill new">+ New Chat</div>
      </div>
    </div>
  );
}
