import React from "react";
import "./sidebar.css";
import SessionsList from "../SessionList/SessionsList";

function Icon({ children, active, title, onClick, disabled = false }) {
  return (
    <button
      className={"icon-btn" + (active ? " active" : "")}
      type="button"
      title={title}
      onClick={onClick}
      disabled={disabled}
    >
      <span className="icon-inner">{children}</span>
    </button>
  );
}

export default function Sidebar({
  sessions,
  activeSessionId,
  onSelectSession,
  onNewChat,
  onDeleteChat,
}) {
  return (
    <aside className="sidebar">
      <div className="sidebar-bg-glow sidebar-glow-1" />
      <div className="sidebar-bg-glow sidebar-glow-2" />

      <div className="sidebar-top">
        <Icon title="Delete current chat" onClick={onDeleteChat} disabled={!activeSessionId}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
            <path
              d="M5 12h14"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </Icon>

        <Icon title="New chat" onClick={onNewChat}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
            <path
              d="M12 5v14"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
            <path
              d="M5 12h14"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </Icon>

        <Icon title="Dashboard">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
            <rect x="3" y="3" width="7" height="7" stroke="currentColor" strokeWidth="2" />
            <rect x="14" y="3" width="7" height="7" stroke="currentColor" strokeWidth="2" />
            <rect x="3" y="14" width="7" height="7" stroke="currentColor" strokeWidth="2" />
          </svg>
        </Icon>
      </div>

      <SessionsList
        sessions={sessions || []}
        activeId={activeSessionId}
        onSelect={onSelectSession}
      />

      <div className="sidebar-bottom">
        <div className="avatar-wrap">
          <div className="avatar" />
        </div>
      </div>
    </aside>
  );
}