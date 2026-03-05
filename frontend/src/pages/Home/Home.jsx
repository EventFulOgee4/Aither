import React, { useEffect, useRef, useState } from "react";
import "./home.css";

import Sidebar from "../../components/Sidebar/Sidebar";
import Topbar from "../../components/Topbar/Topbar";
import OrbLogo from "../../components/OrbLogo/OrbLogo";
import PromptCard from "../../components/PromptCard/PromptCard";
import ExampleCards from "../../components/ExampleCards/ExampleCards";
import { ensureFreshAccessToken } from "../../api/client";

import {
  createSession,
  getMessages,
  listSessions,
  sendMessage,
} from "../../api/chat";

export default function Home() {
  const [sessions, setSessions] = useState([]);
  const [activeSessionId, setActiveSessionId] = useState(null);

  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);

  const bottomRef = useRef(null);

  // 🔹 SAFE session refresh (handles DRF pagination)
  async function refreshSessions(selectIfEmpty = true) {
    console.log("Fetching sessions...");
    const data = await listSessions();
    console.log("Sessions raw:", data);

    // DRF pagination-safe
    const list = Array.isArray(data) ? data : data?.results ?? [];

    console.log("Sessions list:", list);
    setSessions(list);

    if (selectIfEmpty && !activeSessionId && list.length) {
      setActiveSessionId(list[0].id);
    }

    return list;
  }

  async function loadSession(sessionId) {
    setActiveSessionId(sessionId);
    const msgs = await getMessages(sessionId);
    setMessages(msgs);
  }

    useEffect(() => {
    (async () => {
      try {
        // Make sure access token is fresh before the first API call
        await ensureFreshAccessToken();

        const list = await refreshSessions(true);
        if (list.length) {
          const firstId = list[0].id;
          setActiveSessionId(firstId);
          const msgs = await getMessages(firstId);
          setMessages(msgs);
        }
      } catch (e) {
        console.error(e);
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleNewChat() {
    try {
      const s = await createSession("New Session");
      await refreshSessions(false);
      await loadSession(s.id);
    } catch (e) {
      console.error(e);
      alert("Could not create session. Is backend running?");
    }
  }

  async function handleSend() {
    const text = input.trim();
    if (!text || sending) return;

    setSending(true);
    try {
      // optimistic render
      const tempUser = {
        id: `temp-${Date.now()}`,
        role: "user",
        content: text,
      };
      setMessages((prev) => [...prev, tempUser]);
      setInput("");

      const res = await sendMessage(text, activeSessionId || undefined);

      // refresh from server (includes assistant + emotion)
      await refreshSessions(false);
      await loadSession(res.session.id);
    } catch (e) {
      console.error(e);
      alert("Send failed. Check login token and backend.");
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="home-root">
      <Sidebar
        sessions={sessions}
        activeSessionId={activeSessionId}
        onSelectSession={loadSession}
      />

      <div className="home-main">
        <Topbar onNewChat={handleNewChat} />

        <main className="home-content">
          <OrbLogo />
          <h1 className="headline">you feeling today?</h1>

          {/* Messages */}
          {messages.length > 0 && (
            <div
              style={{
                width: "min(900px, 92vw)",
                margin: "18px auto",
                textAlign: "left",
              }}
            >
              {messages.map((m) => (
                <div
                  key={m.id}
                  style={{
                    marginBottom: 10,
                    display: "flex",
                    justifyContent:
                      m.role === "user" ? "flex-end" : "flex-start",
                  }}
                >
                  <div
                    style={{
                      maxWidth: "80%",
                      padding: "10px 12px",
                      borderRadius: 14,
                      background:
                        m.role === "user"
                          ? "rgba(155,143,230,.25)"
                          : "rgba(255,255,255,.08)",
                      border: "1px solid rgba(255,255,255,.10)",
                      whiteSpace: "pre-wrap",
                    }}
                  >
                    {m.content}
                    {m.role === "assistant" && m.emotion && (
                      <div
                        style={{
                          fontSize: 11,
                          opacity: 0.65,
                          marginTop: 6,
                        }}
                      >
                        emotion: {m.emotion}
                        {m.confidence != null
                          ? ` (${m.confidence})`
                          : ""}
                      </div>
                    )}
                  </div>
                </div>
              ))}
              <div ref={bottomRef} />
            </div>
          )}

          <PromptCard
            value={input}
            onChange={setInput}
            onSend={handleSend}
            disabled={sending}
          />

          <div className="examples-label">
            ASK AITHER ONE OF THE EXAMPLES BELOW
          </div>
          <ExampleCards />
        </main>
      </div>
    </div>
  );
}