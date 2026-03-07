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

  const bottomRef = useRef(null);

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
        } else {
          setActiveSessionId(null);
          setMessages([]);
        }
      } catch (e) {
        console.error(e);
      }
    })();
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, sending]);

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

  async function handleDeleteChat() {
    if (!activeSessionId) return;

    const confirmed = window.confirm("Delete this chat?");
    if (!confirmed) return;

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

    const tempUser = {
      id: `temp-${Date.now()}`,
      role: "user",
      content: text,
    };

    try {
      setMessages((prev) => [...prev, tempUser]);
      setInput("");

      const res = await sendMessage(text, activeSessionId || undefined);

      const realUserMsg = res.user_message
        ? {
            id: res.user_message.id,
            role: res.user_message.sender === "ai" ? "assistant" : "user",
            content: res.user_message.message,
            emotion: res.user_message.emotion ?? null,
            confidence: res.user_message.confidence ?? null,
            timestamp: res.user_message.timestamp ?? null,
          }
        : null;

      const aiMsg = res.ai_message
        ? {
            id: res.ai_message.id,
            role: res.ai_message.sender === "ai" ? "assistant" : "user",
            content: res.ai_message.message,
            emotion: res.ai_message.emotion ?? null,
            confidence: res.ai_message.confidence ?? null,
            timestamp: res.ai_message.timestamp ?? null,
          }
        : null;

      const returnedSessionId = res.session?.id ?? activeSessionId ?? null;
      setActiveSessionId(returnedSessionId);

      setMessages((prev) => {
        const withoutTemp = prev.filter((m) => m.id !== tempUser.id);
        const next = [...withoutTemp];

        if (realUserMsg) next.push(realUserMsg);
        if (aiMsg) next.push(aiMsg);

        return next;
      });

      await refreshSessions(false);
    } catch (e) {
      console.error(e);
      setMessages((prev) => prev.filter((m) => m.id !== tempUser.id));
      alert("Send failed. Check login token and backend.");
    } finally {
      setSending(false);
    }
  }

  const hasMessages = messages.length > 0;

  return (
    <div className="home-root">
      <Sidebar
        sessions={sessions}
        activeSessionId={activeSessionId}
        onSelectSession={loadSession}
        onNewChat={handleNewChat}
        onDeleteChat={handleDeleteChat}
      />

      <div className="home-main">
        <Topbar />

        <main
          className={`home-content ${hasMessages ? "chat-active" : "empty-state"}`}
        >
          <div className="animated-bg">
            <div className="bg-blob blob-1" />
            <div className="bg-blob blob-2" />
            <div className="bg-blob blob-3" />
            <div className="bg-grid" />
          </div>

          <div className="ambient-glow ambient-glow-1" />
          <div className="ambient-glow ambient-glow-2" />

          <div className={`hero-block ${hasMessages ? "hero-compact" : ""}`}>
            <OrbLogo sending={sending} compact={hasMessages} />
            <h1 className="headline">How are you feeling today?</h1>
            {!hasMessages && (
              <p className="subheadline">
                Talk, reflect, and grow with Aither.
              </p>
            )}
          </div>

          {hasMessages && (
            <div className="messages-wrap">
              {messages.map((m) => (
                <div
                  key={m.id}
                  className={`message-row ${
                    m.role === "user" ? "user-row" : "assistant-row"
                  }`}
                >
                  <div
                    className={`message-bubble ${
                      m.role === "user" ? "user-bubble" : "assistant-bubble"
                    }`}
                  >
                    <div>{m.content}</div>

                    {m.role === "assistant" && m.emotion && (
                      <div className="message-meta">
                        emotion: {m.emotion}
                        {m.confidence != null ? ` (${m.confidence})` : ""}
                      </div>
                    )}
                  </div>
                </div>
              ))}

              {sending && (
                <div className="message-row assistant-row">
                  <div className="message-bubble assistant-bubble thinking-bubble">
                    <span className="thinking-dot" />
                    <span className="thinking-dot" />
                    <span className="thinking-dot" />
                  </div>
                </div>
              )}

              <div ref={bottomRef} />
            </div>
          )}

          <PromptCard
            value={input}
            onChange={setInput}
            onSend={() => handleSend()}
            disabled={sending}
          />

          {!hasMessages && (
            <>
              <div className="examples-label">
                ASK AITHER ONE OF THE EXAMPLES BELOW
              </div>
              <ExampleCards
                onSelectExample={(text) => {
                  setInput(text);
                }}
              />
            </>
          )}
        </main>
      </div>
    </div>
  );
}