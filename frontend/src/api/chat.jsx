import { api } from "./client";

// DRF pagination helper
function unwrapList(data) {
  return Array.isArray(data) ? data : data?.results ?? [];
}

// Convert backend message -> UI message shape used in Home.jsx
function toUIMsg(m) {
  return {
    id: m.id,
    role: m.sender === "ai" ? "assistant" : "user",
    content: m.message,
    emotion: m.emotion ?? null,
    confidence: m.confidence ?? null,
    timestamp: m.timestamp ?? null,
  };
}

export async function listSessions() {
  const res = await api.get("/chat/sessions/");
  return unwrapList(res.data);
}

export async function createSession(title = "New Session") {
  const res = await api.post("/chat/sessions/", { title });
  return res.data;
}

export async function deleteSession(sessionId) {
  await api.delete(`/chat/sessions/${sessionId}/`);
}

export async function getMessages(sessionId) {
  const res = await api.get("/chat/messages/", {
    params: { session: sessionId },
  });
  const list = unwrapList(res.data);
  return list.map(toUIMsg);
}

export async function sendMessage(text, sessionId) {
  const res = await api.post("/chat/messages/", {
    session: sessionId,
    message: text,
    sender: "user",
  });

  // ✅ THE FIX: backend returns { user_message: {...}, ai_message: {...} }
  // so we must read res.data.user_message, NOT res.data directly
  const rawUser = res.data.user_message ?? res.data;

  const userMsg = {
    id: rawUser.id,
    role: "user",
    content: rawUser.message ?? rawUser.content,
    emotion: rawUser.emotion ?? null,
    confidence: rawUser.confidence ?? null,
    timestamp: rawUser.timestamp ?? null,
  };

  // Use real AI message from backend if available, otherwise fake it
  const rawAi = res.data.ai_message;

  const fakeReplies = [
    "I understand. Tell me more about that.",
    "That sounds difficult. How long have you felt this way?",
    "I'm here for you. What's been on your mind?",
    "That's really important. Can you expand on that?",
  ];

  const aiMsg = rawAi
    ? {
        id: rawAi.id ?? `ai-${Date.now()}`,
        role: "assistant",
        content: rawAi.message ?? rawAi.content,
        emotion: rawAi.emotion ?? null,
        confidence: rawAi.confidence ?? null,
        timestamp: rawAi.timestamp ?? null,
      }
    : {
        id: `ai-${Date.now()}`,
        role: "assistant",
        content: fakeReplies[Math.floor(Math.random() * fakeReplies.length)],
        timestamp: new Date().toISOString(),
      };

  return {
    session: { id: sessionId },
    user_message: userMsg,
    ai_message: aiMsg,
  };
}