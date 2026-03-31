import React, { useRef, useEffect, useState, useCallback } from "react";
import "./promptcard.css";

const MAX_CHARS = 2000;

const MODELS = [
  { id: "aither-mini", name: "Aither-mini", available: true },
  { id: "aither-2.1", name: "Aither 2.1", available: false },
];

export default function PromptCard({ value, onChange, onSend, disabled, messages, sessionTitle, model, onModelChange }) {
  const textareaRef = useRef(null);
  const [modelOpen, setModelOpen] = useState(false);
  const [actionsOpen, setActionsOpen] = useState(false);
  const dropdownRef = useRef(null);
  const actionsRef = useRef(null);

  const selectedModel = MODELS.find((m) => m.id === (model || "aither-mini")) || MODELS[0];

  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 200) + "px";
  }, [value]);

  function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      onSend?.();
    }
  }

  useEffect(() => {
    function handleClickOutside(e) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) setModelOpen(false);
      if (actionsRef.current && !actionsRef.current.contains(e.target)) setActionsOpen(false);
    }
    if (modelOpen || actionsOpen) document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [modelOpen, actionsOpen]);

  const handleModelSelect = useCallback((m) => {
    if (!m.available) return;
    onModelChange?.(m.id);
    setModelOpen(false);
  }, [onModelChange]);

  function handleExportPDF() {
    setActionsOpen(false);
    if (!messages?.length) return;

    const title = sessionTitle || "Aither Session";
    const date = new Date().toLocaleDateString([], { year: "numeric", month: "long", day: "numeric" });

    const rows = messages.map((m) => {
      const who = m.role === "user" ? "You" : "Aither";
      const time = m.timestamp
        ? new Date(m.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
        : "";
      const content = (m.content || "")
        .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
        .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
        .replace(/\*(.+?)\*/g, "<em>$1</em>")
        .replace(/\n/g, "<br/>");
      const align = m.role === "user" ? "right" : "left";
      const bg = m.role === "user" ? "#2d1f5e" : "#1a1530";
      return `<div style="display:flex;justify-content:${align};margin-bottom:12px;">
        <div style="max-width:75%;background:${bg};color:#ece8f8;padding:12px 16px;border-radius:16px;font-size:14px;line-height:1.6;">
          <div style="font-size:10px;opacity:0.5;margin-bottom:4px;text-transform:uppercase;letter-spacing:0.06em;">${who}${time ? " · " + time : ""}</div>
          ${content}
        </div>
      </div>`;
    }).join("");

    const html = `<!DOCTYPE html><html><head><meta charset="UTF-8"/><title>${title}</title>
      <style>body{margin:0;padding:40px;background:#08060b;font-family:system-ui,sans-serif}h1{color:#c9bbff;font-size:22px;font-weight:400;margin:0 0 4px}p{color:#9b98a9;font-size:13px;margin:0 0 32px}@media print{body{background:white;padding:20px}h1{color:#3b2f7e}p{color:#666}}</style>
      </head><body><h1>${title}</h1><p>Exported from Aither · ${date}</p>${rows}</body></html>`;

    const win = window.open("", "_blank");
    win.document.write(html);
    win.document.close();
    win.focus();
    setTimeout(() => win.print(), 400);
  }

  const charCount = value.length;
  const isWarning = charCount > MAX_CHARS * 0.85;

  return (
    <div className="prompt-wrap">
      <div className="prompt-card">
        <textarea
          ref={textareaRef}
          className="prompt-textarea"
          placeholder="Ask Aither anything… (Shift+Enter for new line)"
          value={value}
          onChange={(e) => onChange?.(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          rows={1}
          maxLength={MAX_CHARS}
        />

        <div className="prompt-footer">
          <div className="prompt-left-tools">
            <div className="actions-menu" ref={actionsRef}>
              <button
                className="prompt-tool-btn"
                type="button"
                onClick={() => setActionsOpen(!actionsOpen)}
              >
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 5v14M5 12h14" />
                </svg>
              </button>
              {actionsOpen && (
                <div className="actions-dropdown">
                  <button
                    className="actions-option"
                    type="button"
                    onClick={handleExportPDF}
                    disabled={!messages?.length}
                  >
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" />
                      <polyline points="7 10 12 15 17 10" />
                      <line x1="12" y1="15" x2="12" y2="3" />
                    </svg>
                    Export as PDF
                  </button>
                </div>
              )}
            </div>

            <div className="model-selector" ref={dropdownRef}>
              <button
                className="prompt-tool-btn model-trigger"
                type="button"
                onClick={() => setModelOpen(!modelOpen)}
              >
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round">
                  <circle cx="12" cy="12" r="3" />
                  <path d="M12 1v4M12 19v4M4.22 4.22l2.83 2.83M16.95 16.95l2.83 2.83M1 12h4M19 12h4M4.22 19.78l2.83-2.83M16.95 7.05l2.83-2.83" />
                </svg>
                <span>{selectedModel.name}</span>
                <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M6 9l6 6 6-6" />
                </svg>
              </button>

              {modelOpen && (
                <div className="model-dropdown">
                  {MODELS.map((m) => (
                    <button
                      key={m.id}
                      className={"model-option" + (m.id === selectedModel.id ? " selected" : "") + (!m.available ? " unavailable" : "")}
                      type="button"
                      onClick={() => handleModelSelect(m)}
                    >
                      <span className="model-option-name">{m.name}</span>
                      {m.id === selectedModel.id && m.available && (
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                          <polyline points="20 6 9 17 4 12" />
                        </svg>
                      )}
                      {!m.available && (
                        <span className="coming-soon-tag">Coming soon</span>
                      )}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>

          <div className="prompt-right-tools">
            {charCount > 0 && (
              <span className={`prompt-char-count ${isWarning ? "warning" : ""}`}>
                {charCount}/{MAX_CHARS}
              </span>
            )}

            <button className="prompt-mic" type="button" aria-label="Voice input">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
                <rect x="9" y="2" width="6" height="11" rx="3" stroke="currentColor" strokeWidth="1.8"/>
                <path d="M5 10a7 7 0 0 0 14 0" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"/>
                <path d="M12 19v3M9 22h6" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"/>
              </svg>
            </button>

            <button
              className="prompt-send"
              type="button"
              onClick={onSend}
              disabled={disabled || !value.trim()}
              aria-label="Send message"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                <path d="M12 19V5" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round"/>
                <path d="M5 12l7-7 7 7" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
