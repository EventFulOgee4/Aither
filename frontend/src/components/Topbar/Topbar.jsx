import React from "react";
import "./topbar.css";

export default function Topbar({ sessionTitle, messages = [], onThemeToggle, isDark, onMenuOpen }) {
  function handleExportPDF() {
    if (!messages.length) return;

    // Build a clean printable HTML page
    const title = sessionTitle || "Aither Session";
    const date = new Date().toLocaleDateString([], {
      year: "numeric", month: "long", day: "numeric"
    });

    const rows = messages.map((m) => {
      const who = m.role === "user" ? "You" : "Aither";
      const time = m.timestamp
        ? new Date(m.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
        : "";
      const content = (m.content || "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
        .replace(/\*(.+?)\*/g, "<em>$1</em>")
        .replace(/\n/g, "<br/>");

      const align = m.role === "user" ? "right" : "left";
      const bg    = m.role === "user" ? "#2d1f5e" : "#1a1530";
      const color = "#ece8f8";

      return `
        <div style="display:flex; justify-content:${align}; margin-bottom:12px;">
          <div style="max-width:75%; background:${bg}; color:${color}; padding:12px 16px;
                      border-radius:16px; font-size:14px; line-height:1.6;">
            <div style="font-size:10px; opacity:0.5; margin-bottom:4px; text-transform:uppercase;
                        letter-spacing:0.06em;">${who} ${time ? "· " + time : ""}</div>
            ${content}
          </div>
        </div>`;
    }).join("");

    const html = `<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8"/>
  <title>${title}</title>
  <style>
    body { margin: 0; padding: 40px; background: #08060b; font-family: system-ui, sans-serif; }
    h1   { color: #c9bbff; font-size: 22px; font-weight: 400; margin: 0 0 4px; }
    p    { color: #9b98a9; font-size: 13px; margin: 0 0 32px; }
    @media print {
      body { background: white; padding: 20px; }
      h1   { color: #3b2f7e; }
      p    { color: #666; }
    }
  </style>
</head>
<body>
  <h1>${title}</h1>
  <p>Exported from Aither · ${date}</p>
  ${rows}
</body>
</html>`;

    const win = window.open("", "_blank");
    win.document.write(html);
    win.document.close();
    win.focus();
    setTimeout(() => {
      win.print();
    }, 400);
  }

  return (
    <div className="topbar">
      {/* Hamburger — mobile only */}
      <button
        className="topbar-hamburger"
        type="button"
        onClick={onMenuOpen}
        aria-label="Open menu"
      >
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
          <path d="M3 6h18M3 12h18M3 18h18" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
        </svg>
      </button>

      {/* Model selector */}
      <button className="topbar-model" type="button" aria-label="Select model">
        <span className="topbar-model-dot" />
        <span className="topbar-model-name">Aither_v1</span>
        <svg className="topbar-model-chevron" width="11" height="11" viewBox="0 0 24 24" fill="none">
          <path d="M6 9l6 6 6-6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
      </button>

      {/* Center: session title */}
      <div className="topbar-status">
        {sessionTitle || "New conversation"}
      </div>

      {/* Right actions */}
      <div className="topbar-actions">

        {/* Theme toggle */}
        <button
          className="topbar-pill"
          type="button"
          onClick={onThemeToggle}
          aria-label="Toggle theme"
          title={isDark ? "Switch to light mode" : "Switch to dark mode"}
        >
          {isDark ? (
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none">
              <circle cx="12" cy="12" r="5" stroke="currentColor" strokeWidth="2"/>
              <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"
                stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
            </svg>
          ) : (
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none">
              <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"
                stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          )}
        </button>

        {/* Export PDF */}
        <button
          className="topbar-pill"
          type="button"
          onClick={handleExportPDF}
          aria-label="Export chat as PDF"
          title="Export chat as PDF"
          disabled={!messages.length}
        >
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            <polyline points="7 10 12 15 17 10" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            <line x1="12" y1="15" x2="12" y2="3" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
          </svg>
          Export
        </button>

        {/* Search */}
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