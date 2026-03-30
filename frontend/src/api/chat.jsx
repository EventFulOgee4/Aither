import { api } from "./client";

const BASE_URL = "http://127.0.0.1:8000/api";

// DRF pagination helper
function unwrapList(data) {
  return Array.isArray(data) ? data : data?.results ?? [];
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
  return list.map((m) => ({
    id: m.id,
    role: m.sender === "ai" ? "assistant" : "user",
    content: m.message,
    emotion: m.emotion ?? null,
    confidence: m.confidence ?? null,
    timestamp: m.timestamp ?? null,
  }));
}

export async function sendMessage(text, sessionId) {
  const res = await api.post("/chat/messages/", {
    session: sessionId,
    message: text,
    sender: "user",
  });

  const rawUser = res.data.user_message ?? res.data;
  const rawAi = res.data.ai_message;

  const userMsg = {
    id: rawUser.id,
    role: "user",
    content: rawUser.message ?? rawUser.content,
    emotion: rawUser.emotion ?? null,
    confidence: rawUser.confidence ?? null,
    timestamp: rawUser.timestamp ?? null,
  };

  const aiMsg = rawAi
    ? {
        id: rawAi.id ?? `ai-${Date.now()}`,
        role: "assistant",
        content: rawAi.message ?? rawAi.content,
        emotion: rawAi.emotion ?? null,
        confidence: rawAi.confidence ?? null,
        timestamp: rawAi.timestamp ?? null,
      }
    : null;

  return {
    session: res.data.session ?? { id: sessionId },
    user_message: userMsg,
    ai_message: aiMsg,
  };
}

/**
 * sendMessageStream — uses SSE streaming endpoint.
 *
 * Calls onChunk(text) for each streamed token.
 * Calls onMeta({ session_id, session_title, user_message_id }) once at start.
 * Calls onDone({ ai_message_id }) once at end.
 * Returns a cancel function.
 */
export function sendMessageStream(text, sessionId, { onChunk, onMeta, onDone, onError }) {
  const token = localStorage.getItem("access");

  const ctrl = new AbortController();

  (async () => {
    try {
      const res = await fetch(`${BASE_URL}/chat/stream/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ session: sessionId, message: text }),
        signal: ctrl.signal,
      });

      if (!res.ok) {
        const err = await res.text();
        onError?.(new Error(`HTTP ${res.status}: ${err}`));
        return;
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop(); // keep incomplete line

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          const raw = line.slice(6).trim();
          if (!raw) continue;

          try {
            const parsed = JSON.parse(raw);
            if (parsed.type === "meta") onMeta?.(parsed);
            else if (parsed.type === "chunk") onChunk?.(parsed.text);
            else if (parsed.type === "done") onDone?.(parsed);
          } catch {
            // ignore malformed chunks
          }
        }
      }
    } catch (e) {
      if (e.name !== "AbortError") onError?.(e);
    }
  })();

  return () => ctrl.abort();
}