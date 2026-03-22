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

export async function getMessages(sessionId) {
  const res = await api.get("/chat/messages/", {
    params: { session: sessionId },
  });

  const list = unwrapList(res.data);
  return list.map(toUIMsg);
}

export async function sendMessage(text, sessionId) {
  // Backend expects: { session: <id>, message: <text> }
  const res = await api.post("/chat/messages/", {
    session: sessionId,
    message: text,
    sender: "user", // REQUIRED after serializer fix
  });

  // Your backend create() returns:
  // { user_message: {...}, ai_message: {...} }
  // We’ll also return a session object so Home.jsx can do res.session.id
  // If your backend does NOT return session in the response, we add it.
  const userMsg = toUIMsg(res.data);

   // Fake AI response (for demo)
  const fakeReplies = [
  "I understand. Tell me more about that.",
  "That sounds difficult. How long have you felt this way?",
  "I'm here for you. What’s been on your mind?",
  "That’s really important. Can you expand on that?",
];

const aiMsg = {
  id: Date.now(),
  role: "assistant",
  content: fakeReplies[Math.floor(Math.random() * fakeReplies.length)],
  timestamp: new Date().toISOString(),
};

  return {
    session: { id: sessionId },
    //user_message: res.data.user_message,
    //ai_message: res.data.ai_message,
    user_message: userMsg,
    ai_message: aiMsg,
  };
}
