import React from "react";
import "./sidebar.css";
import SessionsList from "../SessionList/SessionsList";

function Icon({ children, active }) {
  return (
    <button className={"icon-btn" + (active ? " active" : "")} type="button">
      {children}
    </button>
  );
}

export default function Sidebar({ sessions, activeSessionId, onSelectSession }) {
  return (
    <aside className="sidebar">
      <div className="sidebar-top">
        <Icon>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
            <path d="M3 12h18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </Icon>

        <Icon>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
            <path d="M12 5v14" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
            <path d="M5 12h14" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </Icon>

        <Icon>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
            <rect x="3" y="3" width="7" height="7" stroke="currentColor" strokeWidth="2" />
            <rect x="14" y="3" width="7" height="7" stroke="currentColor" strokeWidth="2" />
            <rect x="3" y="14" width="7" height="7" stroke="currentColor" strokeWidth="2" />
          </svg>
        </Icon>
      </div>

      {/* Sessions list */}
      <SessionsList
        sessions={sessions || []}
        activeId={activeSessionId}
        onSelect={onSelectSession}
      />

      <div className="sidebar-bottom">
        <div className="avatar" />
      </div>
    </aside>
  );
}