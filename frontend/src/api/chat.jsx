import { api } from "./client";

export async function listSessions() {
  const res = await api.get("/chat/sessions/");
  return res.data;
}

export async function createSession(title = "New Session") {
  const res = await api.post("/chat/sessions/", { title });
  return res.data;
}

export async function getMessages(sessionId) {
  const res = await api.get(`/chat/sessions/${sessionId}/messages/`);
  return res.data;
}

export async function sendMessage(message, sessionId) {
  const payload = { message };
  if (sessionId) payload.session_id = sessionId;
  const res = await api.post("/chat/message/", payload);
  return res.data;
}