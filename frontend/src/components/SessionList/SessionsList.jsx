import React from "react";
import "./sessionslist.css";

export default function SessionsList({ sessions, activeId, onSelect }) {
  return (
    <div className="sessions-wrap">
      <div className="sessions-title">Chats</div>

      <div className="sessions-list">
        {sessions.map((s) => (
          <button
            key={s.id}
            className={"session-item" + (s.id === activeId ? " active" : "")}
            onClick={() => onSelect?.(s.id)}
            type="button"
          >
            <div className="session-main">
              <div className="session-name">{s.title || "New Session"}</div>
              <div className="session-meta">#{s.id}</div>
            </div>
            <div className="session-shine" />
          </button>
        ))}

        {sessions.length === 0 && (
          <div className="sessions-empty">No chats yet</div>
        )}
      </div>
    </div>
  );
}