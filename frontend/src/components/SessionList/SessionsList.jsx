import React from "react";
import "./sessionslist.css";

export default function SessionsList({ sessions, activeId, onSelect }) {
  return (
    <div className="sessions-wrap">
      {sessions.length > 0 && (
        <div className="sessions-section-label">Recent chats</div>
      )}

      {sessions.map((s) => (
        <button
          key={s.id}
          className={"session-item" + (s.id === activeId ? " active" : "")}
          onClick={() => onSelect?.(s.id)}
          type="button"
        >
          <div className="session-main">
            <div className="session-dot" />
            <div className="session-text">
              <div className="session-name">{s.title || "New Session"}</div>
              <div className="session-meta">Session #{s.id}</div>
            </div>
          </div>
          <div className="session-shine" />
        </button>
      ))}

      {sessions.length === 0 && (
        <div className="sessions-empty">
          <svg className="sessions-empty-icon" width="28" height="28" viewBox="0 0 24 24" fill="none">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"
              stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
          No chats yet.
          <br />Start a new conversation.
        </div>
      )}
    </div>
  );
}