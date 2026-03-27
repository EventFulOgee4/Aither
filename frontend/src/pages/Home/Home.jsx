import React, { useEffect, useRef, useState, useCallback } from "react";
import "./home.css";

import Sidebar from "../../components/Sidebar/Sidebar";
import Topbar from "../../components/Topbar/Topbar";
import OrbLogo from "../../components/OrbLogo/OrbLogo";
import PromptCard from "../../components/PromptCard/PromptCard";
import ExampleCards from "../../components/ExampleCards/ExampleCards";
import { ensureFreshAccessToken } from "../../api/client";

import {
  createSession,
  deleteSession,
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

  const scrollRef = useRef(null);
  const bottomRef = useRef(null);

  const activeSession = sessions.find((s) => s.id === activeSessionId);

  // ── Helpers ──────────────────────────────────────
  const scrollToBottom = useCallback((behavior = "smooth") => {
    bottomRef.current?.scrollIntoView({ behavior });
  }, []);

  async function refreshSessions(selectIfEmpty = true) {
    const data = await listSessions();
    const list = Array.isArray(data) ? data : data?.results ?? [];
    setSessions(list);
    if (selectIfEmpty && !activeSessionId && list.length) {
      setActiveSessionId(list[0].id);
    }
    return list;
  }

  async function loadSession(sessionId) {
    if (!sessionId) {
      setActiveSessionId(null);
      setMessages([]);
      return;
    }
    setActiveSessionId(sessionId);
    const msgs = await getMessages(sessionId);
    setMessages(msgs);
  }

  // ── Init ──────────────────────────────────────────
  useEffect(() => {
    (async () => {
      try {
        await ensureFreshAccessToken();
        const list = await refreshSessions(true);
        if (list.length && list[0]?.id) {
          const firstId = list[0].id;
          setActiveSessionId(firstId);
          const msgs = await getMessages(firstId);
          setMessages(msgs);
        }
      } catch (e) {
        console.error(e);
      }
    })();
  }, []);

  // Auto-scroll when messages change
  useEffect(() => {
    scrollToBottom(messages.length <= 2 ? "instant" : "smooth");
  }, [messages, sending]);

  // ── Handlers ─────────────────────────────────────
  async function handleNewChat() {
    try {
      const s = await createSession("New Session");
      await refreshSessions(false);
      await loadSession(s.id);
    } catch (e) {
      console.error(e);
      alert("Could not create session. Is the backend running?");
    }
  }

  async function handleDeleteChat() {
    if (!activeSessionId) return;
    if (!window.confirm("Delete this chat?")) return;

    try {
      const deletingId = activeSessionId;
      await deleteSession(deletingId);
      const updated = await listSessions();
      setSessions(updated);
      const remaining = updated.filter((s) => s.id !== deletingId);
      if (remaining.length > 0) {
        await loadSession(remaining[0].id);
      } else {
        setActiveSessionId(null);
        setMessages([]);
      }
    } catch (e) {
      console.error(e);
      alert("Could not delete chat.");
    }
  }

  async function handleSend(prefilledText) {
    const text = (prefilledText ?? input).trim();
    if (!text || sending) return;

    setSending(true);
    const tempId = `temp-${Date.now()}`;
    const tempUser = { id: tempId, role: "user", content: text };

    try {
      setMessages((prev) => [...prev, tempUser]);
      setInput("");

      let sessionId = activeSessionId;
      if (!sessionId) {
        const newSession = await createSession("New Session");
        sessionId = newSession.id;
        setActiveSessionId(sessionId);
      }

      const res = await sendMessage(text, sessionId);

      const toMsg = (m, fallbackRole) => m ? {
        id: m.id,
        role: m.sender === "ai" ? "assistant" : "user",
        content: m.message,
        emotion: m.emotion ?? null,
        confidence: m.confidence ?? null,
        timestamp: m.timestamp ?? null,
      } : null;

      const realUserMsg = toMsg(res.user_message);
      const aiMsg = toMsg(res.ai_message);
      const returnedSessionId = res.session?.id ?? sessionId;

      setActiveSessionId(returnedSessionId);
      setMessages((prev) => {
        const without = prev.filter((m) => m.id !== tempId);
        return [...without, ...[realUserMsg, aiMsg].filter(Boolean)];
      });

      await refreshSessions(false);
    } catch (e) {
      console.error(e);
      setMessages((prev) => prev.filter((m) => m.id !== tempId));
      alert("Send failed. Check your login token and backend.");
    } finally {
      setSending(false);
    }
  }

  const hasMessages = messages.length > 0;

  return (
    <div className="home-root">
      {/* Background */}
      <div className="animated-bg">
        <div className="bg-blob blob-1" />
        <div className="bg-blob blob-2" />
        <div className="bg-blob blob-3" />
        <div className="bg-grid" />
      </div>

      <Sidebar
        sessions={sessions}
        activeSessionId={activeSessionId}
        onSelectSession={loadSession}
        onNewChat={handleNewChat}
        onDeleteChat={handleDeleteChat}
      />

      <div className="home-main">
        <Topbar sessionTitle={activeSession?.title} />

        {/* Scrollable area */}
        <div className="home-scroll" ref={scrollRef}>
          <div className="home-content">

            {/* Hero / compact header */}
            <div className={`hero-block${hasMessages ? " hero-compact" : ""}`}>
              <OrbLogo sending={sending} compact={hasMessages} />
              <div className="hero-text">
                <h1 className="headline">
                  {hasMessages ? "Aither" : "How are you feeling today?"}
                </h1>
                {!hasMessages && (
                  <p className="subheadline">Talk, reflect, and grow with Aither.</p>
                )}
              </div>
            </div>

            {/* Messages */}
            {hasMessages && (
              <div className="messages-wrap">
                {messages.map((m) => (
                  <div
                    key={m.id}
                    className={`message-row ${m.role === "user" ? "user-row" : "assistant-row"}`}
                  >
                    <div className="message-group">
                      <div className={`message-bubble ${m.role === "user" ? "user-bubble" : "assistant-bubble"}`}>
                        {m.content}
                        {m.role === "assistant" && m.emotion && (
                          <div className="message-meta">
                            <span className="emotion-tag">
                              {m.emotion}
                              {m.confidence != null ? ` · ${m.confidence}` : ""}
                            </span>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}

                {sending && (
                  <div className="message-row assistant-row">
                    <div className="message-group">
                      <div className="message-bubble assistant-bubble thinking-bubble">
                        <span className="thinking-dot" />
                        <span className="thinking-dot" />
                        <span className="thinking-dot" />
                      </div>
                    </div>
                  </div>
                )}

                <div className="scroll-anchor" ref={bottomRef} />
              </div>
            )}

            {/* Empty state */}
            {!hasMessages && (
              <div className="examples-section">
                <div className="examples-label">Try asking</div>
                <ExampleCards
                  onSelectExample={(text) => {
                    setInput(text);
                    // Optionally send immediately:
                    // handleSend(text);
                  }}
                />
              </div>
            )}

            {/* Spacer so content doesn't hide behind fixed prompt */}
            <div style={{ flex: 1, minHeight: 24 }} />
          </div>
        </div>

        {/* Sticky prompt at bottom */}
        <div className="prompt-area">
          <PromptCard
            value={input}
            onChange={setInput}
            onSend={() => handleSend()}
            disabled={sending}
          />
        </div>
      </div>
    </div>
  );
}