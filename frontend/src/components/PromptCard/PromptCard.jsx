import React, { useRef, useEffect } from "react";
import "./promptcard.css";

const MAX_CHARS = 2000;

export default function PromptCard({ value, onChange, onSend, disabled }) {
  const textareaRef = useRef(null);

  // Auto-resize textarea
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
            <button className="prompt-tool-btn" type="button">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none">
                <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"
                  stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
              Attach
            </button>
            <button className="prompt-tool-btn" type="button">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none">
                <circle cx="12" cy="12" r="3" stroke="currentColor" strokeWidth="1.8"/>
                <path d="M12 1v4M12 19v4M4.22 4.22l2.83 2.83M16.95 16.95l2.83 2.83M1 12h4M19 12h4M4.22 19.78l2.83-2.83M16.95 7.05l2.83-2.83"
                  stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"/>
              </svg>
              Tone
            </button>
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