import React from "react";
import "./topbar.css";

export default function Topbar({ sessionTitle }) {
  return (
    <div className="topbar">
      {/* Model selector */}
      <button className="topbar-model" type="button" aria-label="Select model">
        <span className="topbar-model-dot" />
        <span className="topbar-model-name">Aither_v1</span>
        <svg className="topbar-model-chevron" width="11" height="11" viewBox="0 0 24 24" fill="none">
          <path d="M6 9l6 6 6-6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
      </button>

      {/* Center: session title or default */}
      <div className="topbar-status">
        {sessionTitle ? sessionTitle : "New conversation"}
      </div>

      {/* Right actions */}
      <div className="topbar-actions">
        <button className="topbar-pill" type="button" aria-label="Search">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none">
            <circle cx="11" cy="11" r="6" stroke="currentColor" strokeWidth="2"/>
            <path d="M21 21l-4.35-4.35" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
          </svg>
          Search
        </button>
      </div>
    </div>
  );
}