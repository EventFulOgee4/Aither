import React from "react";
import "./sidebar.css";
import SessionsList from "../SessionList/SessionsList";
import { logout } from "../../api/auth";
import { useNavigate } from "react-router-dom";

function IconBtn({ children, active, title, onClick, disabled = false }) {
  return (
    <button
      className={"icon-btn" + (active ? " active" : "")}
      type="button"
      title={title}
      onClick={onClick}
      disabled={disabled}
      aria-label={title}
    >
      {children}
    </button>
  );
}

export default function Sidebar({
  sessions,
  activeSessionId,
  onSelectSession,
  onNewChat,
  onDeleteChat,
  isOpen,
  onClose,
}) {
  const nav = useNavigate();

  function handleLogout() {
    logout();
    nav("/login");
  }

  function handleSelectSession(id) {
    onSelectSession?.(id);
    onClose?.();
  }

  function handleNewChat() {
    onNewChat?.();
    onClose?.();
  }

  return (
    <>
      {isOpen && (
        <div className="sidebar-backdrop" onClick={onClose} aria-hidden="true" />
      )}

      <aside className={`sidebar${isOpen ? " sidebar-open" : ""}`}>
        <div className="sidebar-bg-glow sidebar-glow-1" />
        <div className="sidebar-bg-glow sidebar-glow-2" />

        <div className="sidebar-brand">
          <div className="sidebar-brand-orb" />
          <span className="sidebar-brand-name">Aither</span>
          <span className="sidebar-brand-version">v1</span>
          <button className="sidebar-close-btn" onClick={onClose} aria-label="Close menu">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
              <path d="M18 6L6 18M6 6l12 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
            </svg>
          </button>
        </div>

        <div className="sidebar-actions">
          <IconBtn title="New chat" onClick={handleNewChat}>
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none">
              <path d="M12 5v14M5 12h14" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
            </svg>
          </IconBtn>

          <IconBtn title="Delete current chat" onClick={onDeleteChat} disabled={!activeSessionId}>
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none">
              <path d="M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </IconBtn>

          <IconBtn title="Dashboard">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none">
              <rect x="3" y="3" width="7" height="7" rx="1.5" stroke="currentColor" strokeWidth="1.8"/>
              <rect x="14" y="3" width="7" height="7" rx="1.5" stroke="currentColor" strokeWidth="1.8"/>
              <rect x="3" y="14" width="7" height="7" rx="1.5" stroke="currentColor" strokeWidth="1.8"/>
              <rect x="14" y="14" width="7" height="7" rx="1.5" stroke="currentColor" strokeWidth="1.8"/>
            </svg>
          </IconBtn>

          <span className="icon-btn-label">
            {sessions.length} {sessions.length === 1 ? "chat" : "chats"}
          </span>
        </div>

        <div className="sidebar-sessions">
          <SessionsList
            sessions={sessions || []}
            activeId={activeSessionId}
            onSelect={handleSelectSession}
          />
        </div>

        <div className="sidebar-bottom">
          <div className="avatar-wrap">
            <div className="avatar" />
          </div>
          <div className="sidebar-user-info">
            <div className="sidebar-user-name">You</div>
            <div className="sidebar-user-role">Personal account</div>
          </div>
          <button className="logout-btn" title="Sign out" onClick={handleLogout}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"/>
              <path d="M16 17l5-5-5-5" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M21 12H9" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"/>
            </svg>
          </button>
        </div>
      </aside>
    </>
  );
}