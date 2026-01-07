import React from "react";
import "./promptcard.css";

export default function PromptCard() {
  return (
    <div className="prompt-wrap">
      <div className="prompt-card">
        <div className="input-row">
          <input placeholder="Ask Aither a question..." />
          <button className="mic">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
              <path
                d="M12 1v11"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              <path
                d="M8 11a4 4 0 0 0 8 0"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </button>
        </div>

        <div className="controls-row">
          <div className="left-controls">
            <button className="small">Attach</button>
            <button className="small">Tone</button>
          </div>
          <button className="send">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
              <path
                d="M22 2L11 13"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              <path
                d="M22 2l-7 20-4-9-9-4 20-7z"
                stroke="currentColor"
                strokeWidth="0"
              />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}
