import React, { useState } from "react";
import "./promptcard.css";
import { createSession, sendMessage } from "../../api"; // adjust if path different

export default function PromptCard() {
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSend = async () => {
    if (!message.trim() || loading) return;

    setLoading(true);

    try {
      // 1️⃣ Create a new session
      const session = await createSession();

      if (!session?.id) {
        alert("Failed to create session.");
        setLoading(false);
        return;
      }

      // 2️⃣ Send message to backend
      const response = await sendMessage(session.id, message);

      console.log("Backend response:", response);

      // ⚠️ Depending on your serializer, response may differ
      // For now just alert whole object
      alert("Message sent! Check console for AI response.");

    } catch (error) {
      console.error("Error:", error);
      alert("Something went wrong. Are you logged in?");
    }

    setMessage("");
    setLoading(false);
  };

  return (
    <div className="prompt-wrap">
      <div className="prompt-card">
        <div className="input-row">
          <input
            placeholder="Ask Aither a question..."
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") handleSend();
            }}
          />

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

          <button
            className="send"
            onClick={handleSend}
            disabled={loading}
          >
            {loading ? "..." : (
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
            )}
          </button>
        </div>
      </div>
    </div>
  );
}