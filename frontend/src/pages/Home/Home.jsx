import React, { useEffect, useRef, useState, useCallback, useMemo } from "react";
import "./home.css";

import Sidebar from "../../components/Sidebar/Sidebar";
import Topbar from "../../components/Topbar/Topbar";
import OrbLogo from "../../components/OrbLogo/OrbLogo";
import PromptCard from "../../components/PromptCard/PromptCard";
import ExampleCards from "../../components/ExampleCards/ExampleCards";
import MoodCheckIn from "../../components/MoodCheckIn/MoodCheckIn";
import ToneSelector, { TONES } from "../../components/ToneSelector/ToneSelector";
import ContextMeter from "../../components/ContextMeter/ContextMeter";
import Thinking from "../../components/Thinking/Thinking";
import { ensureFreshAccessToken } from "../../api/client";
import { logMood } from "../../api/mood";

import {
  createSession,
  deleteSession,
  getMessages,
  listSessions,
  sendMessageStream,
} from "../../api/chat";

const TONE_PROMPTS = {
  assertive:
    "\n\n[Tone: Respond in an assertive, direct, and confident manner. Be clear and straightforward with your guidance. Encourage the user to take decisive action.]",
  tender:
    "\n\n[Tone: Respond in a tender, gentle, and nurturing manner. Be soft and caring with your words. Make the user feel safe and comforted.]",
  empathy:
    "\n\n[Tone: Respond with deep empathy and emotional understanding. Validate the user's feelings. Reflect their emotions back to them and show that you truly understand their experience.]",
  neutral: "",
};

// ── Markdown renderer ─────────────────────────────────────────────────────
function renderMarkdown(text) {
  if (!text) return "";

  // Escape HTML
  let escaped = text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");

  // Process line by line for block elements
  const lines = escaped.split("\n");
  const output = [];
  let inUl = false;
  let inOl = false;
  let paraBuffer = [];

  function flushPara() {
    if (paraBuffer.length) {
      const inner = paraBuffer.join(" ").trim();
      if (inner) output.push(`<p>${inner}</p>`);
      paraBuffer = [];
    }
  }

  function closeList() {
    if (inUl) { output.push("</ul>"); inUl = false; }
    if (inOl) { output.push("</ol>"); inOl = false; }
  }

  function inlineFormat(line) {
    return line
      .replace(/\*\*\*(.+?)\*\*\*/g, "<strong><em>$1</em></strong>")
      .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
      .replace(/\*(.+?)\*/g, "<em>$1</em>")
      .replace(/`(.+?)`/g, "<code>$1</code>");
  }

  for (let i = 0; i < lines.length; i++) {
    const raw = lines[i];
    const line = raw.trim();

    // Horizontal rule
    if (/^---+$/.test(line) || /^===+$/.test(line)) {
      flushPara(); closeList();
      output.push("<hr/>");
      continue;
    }

    // Headings
    const hMatch = line.match(/^(#{1,3})\s+(.+)$/);
    if (hMatch) {
      flushPara(); closeList();
      const level = Math.min(hMatch[1].length, 3);
      output.push(`<h${level}>${inlineFormat(hMatch[2])}</h${level}>`);
      continue;
    }

    // Unordered list
    const ulMatch = line.match(/^[-*•]\s+(.+)$/);
    if (ulMatch) {
      flushPara();
      if (!inUl) { if (inOl) { output.push("</ol>"); inOl = false; } output.push("<ul>"); inUl = true; }
      output.push(`<li>${inlineFormat(ulMatch[1])}</li>`);
      continue;
    }

    // Ordered list
    const olMatch = line.match(/^\d+\.\s+(.+)$/);
    if (olMatch) {
      flushPara();
      if (!inOl) { if (inUl) { output.push("</ul>"); inUl = false; } output.push("<ol>"); inOl = true; }
      output.push(`<li>${inlineFormat(olMatch[1])}</li>`);
      continue;
    }

    // Empty line — flush paragraph
    if (line === "") {
      flushPara(); closeList();
      continue;
    }

    // Normal text — close any open list, buffer for paragraph
    closeList();
    paraBuffer.push(inlineFormat(line));
  }

  flushPara();
  closeList();

  return output.join("\n");
}

function MessageContent({ content }) {
  return (
    <div
      className="message-content"
      dangerouslySetInnerHTML={{ __html: renderMarkdown(content) }}
    />
  );
}

// ── Timestamp formatter ───────────────────────────────────────────────────
function formatTime(timestamp) {
  if (!timestamp) return "";
  try {
    const date = new Date(timestamp);
    const now = new Date();
    const isToday = date.toDateString() === now.toDateString();
    if (isToday) {
      return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    }
    return (
      date.toLocaleDateString([], { month: "short", day: "numeric" }) +
      " · " +
      date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
    );
  } catch {
    return "";
  }
}

// ── Home component ────────────────────────────────────────────────────────
export default function Home() {
  const [sessions, setSessions]           = useState([]);
  const [activeSessionId, setActiveSessionId] = useState(null);
  const [messages, setMessages]           = useState([]);
  const [input, setInput]                 = useState("");
  const [sending, setSending]             = useState(false);
  const [isDark, setIsDark]               = useState(true);
  const [sidebarOpen, setSidebarOpen]     = useState(false);
  const [activeTone, setActiveTone]       = useState("neutral");
  const [activeModel, setActiveModel]     = useState("aither-mini");

  const [moodCheckInVisible, setMoodCheckInVisible] = useState(false);
  const aiResponseCountRef = useRef(0);

  const scrollRef      = useRef(null);
  const bottomRef      = useRef(null);
  const cancelStreamRef = useRef(null);

  const activeSession = sessions.find((s) => s.id === activeSessionId);
  const currentTone = useMemo(
    () => TONES.find((t) => t.id === activeTone) || TONES[3],
    [activeTone]
  );

  // ── Theme ────────────────────────────────────────────────────────────────
  useEffect(() => {
    const saved = localStorage.getItem("theme");
    const dark = saved ? saved === "dark" : true;
    setIsDark(dark);
    document.documentElement.setAttribute("data-theme", dark ? "dark" : "light");
  }, []);

  function toggleTheme() {
    const next = !isDark;
    setIsDark(next);
    const val = next ? "dark" : "light";
    document.documentElement.setAttribute("data-theme", val);
    localStorage.setItem("theme", val);
  }

  // ── Scroll ───────────────────────────────────────────────────────────────
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
    setMoodCheckInVisible(false);
    aiResponseCountRef.current = 0;
    const msgs = await getMessages(sessionId);
    setMessages(msgs);
  }

  // ── Init ─────────────────────────────────────────────────────────────────
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

  useEffect(() => {
    scrollToBottom(messages.length <= 2 ? "instant" : "smooth");
  }, [messages, sending]);

  // ── Mood ─────────────────────────────────────────────────────────────────
  async function handleLogMood(mood, intensity) {
    try {
      await logMood(mood, intensity, "");
    } catch (e) {
      console.error("Mood log failed:", e);
    }
  }

  // ── Chat handlers ─────────────────────────────────────────────────────────
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

    cancelStreamRef.current?.();
    setMoodCheckInVisible(false);
    setSending(true);
    setInput("");

    const tempUserId  = `temp-user-${Date.now()}`;
    const streamingId = `streaming-${Date.now()}`;
    const now = new Date().toISOString();

    setMessages((prev) => [
      ...prev,
      { id: tempUserId, role: "user", content: text, timestamp: now },
    ]);

    let sessionId = activeSessionId;
    if (!sessionId) {
      try {
        const newSession = await createSession("New Session");
        sessionId = newSession.id;
        setActiveSessionId(sessionId);
        await refreshSessions(false);
      } catch (e) {
        console.error(e);
        setMessages((prev) => prev.filter((m) => m.id !== tempUserId));
        setSending(false);
        alert("Could not create session.");
        return;
      }
    }

    setMessages((prev) => [
      ...prev,
      { id: streamingId, role: "assistant", content: "", streaming: true, timestamp: now },
    ]);

    const textWithTone = text + (TONE_PROMPTS[activeTone] || "");
    cancelStreamRef.current = sendMessageStream(textWithTone, sessionId, {
      onMeta: (meta) => {
        if (meta.session_title && meta.session_title !== "New Session") {
          setSessions((prev) =>
            prev.map((s) =>
              s.id === meta.session_id ? { ...s, title: meta.session_title } : s
            )
          );
        }
        if (meta.user_message_id) {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === tempUserId ? { ...m, id: meta.user_message_id } : m
            )
          );
        }
      },

      onChunk: (chunk) => {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === streamingId ? { ...m, content: m.content + chunk } : m
          )
        );
        scrollToBottom("smooth");
      },

      onDone: async (done) => {
        const aiTimestamp = new Date().toISOString();
        setMessages((prev) =>
          prev.map((m) =>
            m.id === streamingId
              ? { ...m, id: done.ai_message_id ?? m.id, streaming: false, timestamp: aiTimestamp }
              : m
          )
        );
        setSending(false);
        cancelStreamRef.current = null;

        // Mood check-in every 3rd AI response
        aiResponseCountRef.current += 1;
        if (aiResponseCountRef.current % 3 === 0) {
          setMoodCheckInVisible(true);
        }

        await refreshSessions(false);
      },

      onError: (err) => {
        console.error("Stream error:", err);
        setMessages((prev) =>
          prev.filter((m) => m.id !== streamingId && m.id !== tempUserId)
        );
        setSending(false);
        alert("Send failed. Check your login token and backend.");
      },
    });
  }

  const hasMessages = messages.length > 0;

  return (
    <div className="home-root">
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
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />

      <div className="home-main">
        <Topbar
          sessionTitle={activeSession?.title}
          messages={messages}
          onThemeToggle={toggleTheme}
          isDark={isDark}
          onMenuOpen={() => setSidebarOpen(true)}
        />

        <div className="home-scroll" ref={scrollRef}>
          <div className="home-content">

            <div className={`hero-block${hasMessages ? " hero-compact" : ""}`}>
              <OrbLogo sending={sending} compact={hasMessages} toneGradient={currentTone.gradient} />
              <div className="hero-text">
                <h1 className="headline">
                  {hasMessages ? "Aither" : "How are you feeling today?"}
                </h1>
                {!hasMessages && (
                  <p className="subheadline">Talk, reflect, and grow with Aither.</p>
                )}
              </div>
            </div>

            {!hasMessages && (
              <ToneSelector activeTone={activeTone} onToneChange={setActiveTone} />
            )}

            {hasMessages && (
              <div className="messages-wrap">
                {messages.map((m) => (
                  <div
                    key={m.id}
                    className={`message-row ${m.role === "user" ? "user-row" : "assistant-row"}`}
                  >
                    <div className="message-group">
                      <div
                        className={`message-bubble ${
                          m.role === "user" ? "user-bubble" : "assistant-bubble"
                        } ${m.streaming ? "streaming" : ""}`}
                      >
                        {m.role === "user" ? (
                          <span>{m.content}</span>
                        ) : (
                          <MessageContent content={m.content} />
                        )}
                        {m.streaming && <span className="streaming-cursor" />}
                        {m.role === "assistant" && m.emotion && (
                          <div className="message-meta">
                            <span className="emotion-tag">
                              {m.emotion}
                              {m.confidence != null ? ` · ${m.confidence}` : ""}
                            </span>
                          </div>
                        )}
                      </div>

                      {m.timestamp && !m.streaming && (
                        <div className={`message-time ${m.role === "user" ? "time-right" : "time-left"}`}>
                          {formatTime(m.timestamp)}
                        </div>
                      )}
                    </div>
                  </div>
                ))}

                {moodCheckInVisible && (
                  <div className="message-row assistant-row">
                    <div className="message-group">
                      <MoodCheckIn
                        onLog={handleLogMood}
                        onDismiss={() => setMoodCheckInVisible(false)}
                      />
                    </div>
                  </div>
                )}

                {sending && (
                  <div className="message-row assistant-row">
                    <div className="message-group">
                      <Thinking />
                    </div>
                  </div>
                )}

                <div className="scroll-anchor" ref={bottomRef} />
              </div>
            )}

            {!hasMessages && (
              <div className="examples-section">
                <div className="examples-label">Try asking</div>
                <ExampleCards onSelectExample={(text) => setInput(text)} />
              </div>
            )}

            <div style={{ flex: 1, minHeight: 24 }} />
          </div>
        </div>

        <div className="prompt-area">
          <ContextMeter messageCount={messages.length} />
          <PromptCard
            value={input}
            onChange={setInput}
            onSend={() => handleSend()}
            disabled={sending}
            messages={messages}
            sessionTitle={activeSession?.title}
            model={activeModel}
            onModelChange={setActiveModel}
          />
        </div>
      </div>
    </div>
  );
}