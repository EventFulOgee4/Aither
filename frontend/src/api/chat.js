import { api, BASE_URL, ensureFreshAccessToken } from "./client.js";

// DRF pagination helper
function unwrapList(data) {
  return Array.isArray(data) ? data : data?.results ?? [];
}

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

async function fetchAll(path, params = {}) {
  const items = [];
  let page = 1;
  while (true) {
    const { data } = await api.get(path, { params: { ...params, page } });
    items.push(...unwrapList(data));
    if (!data.next) return items;
    page += 1;
  }
}

export async function listSessions() {
  return fetchAll("/chat/sessions/");
}

export async function createSession(title = "New Session") {
  const res = await api.post("/chat/sessions/", { title });
  return res.data;
}

export async function deleteSession(sessionId) {
  await api.delete(`/chat/sessions/${sessionId}/`);
}

export async function getMessages(sessionId) {
  return (await fetchAll("/chat/messages/", { session: sessionId })).map(toUIMsg);
}

export async function sendMessage(text, sessionId) {
  const res = await api.post("/chat/messages/", {
    session: sessionId,
    message: text,
    sender: "user",
  });

  const rawUser = res.data.user_message ?? res.data;
  const userMsg = {
    id: rawUser.id,
    role: "user",
    content: rawUser.message ?? rawUser.content,
    emotion: rawUser.emotion ?? null,
    confidence: rawUser.confidence ?? null,
    timestamp: rawUser.timestamp ?? null,
  };

  const rawAi = res.data.ai_message;
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
    session: { id: sessionId },
    user_message: userMsg,
    ai_message: aiMsg,
  };
}

/**
 * sendMessageStream — SSE streaming endpoint.
 *
 * Calls onChunk(text) for each streamed token.
 * Calls onMeta({ session_id, session_title, user_message_id }) once at start.
 * Calls onDone({ ai_message_id }) once at end.
 * Returns a cancel function.
 */
export function sendMessageStream(
  text,
  sessionId,
  { onChunk, onMeta, onDone, onError, tone = "neutral" }
) {
  const ctrl  = new AbortController();

  (async () => {
    try {
      const token = await ensureFreshAccessToken();
      if (!token) throw new Error("Your session expired. Please sign in again.");
      const res = await fetch(`${BASE_URL}/chat/stream/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ session: sessionId, message: text, tone }),
        signal: ctrl.signal,
      });

      if (!res.ok) {
        const err = await res.text();
        onError?.(new Error(`HTTP ${res.status}: ${err}`));
        return;
      }

      if (!res.body) throw new Error("Streaming is unavailable in this browser.");
      const reader  = res.body.getReader();
      let completed = false;
      const decoder = new TextDecoder();
      let buffer    = "";

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
            if (parsed.type === "meta")  onMeta?.(parsed);
            else if (parsed.type === "chunk") onChunk?.(parsed.text);
            else if (parsed.type === "done") { completed = true; await onDone?.(parsed); }
            else if (parsed.type === "error") throw new Error(parsed.message);
          } catch (error) {
            throw new Error(error.message || "Invalid response from server.");
          }
        }
      }
      if (!completed) throw new Error("Connection interrupted before the response finished.");
    } catch (e) {
      if (e.name !== "AbortError") onError?.(e);
    }
  })();

  return () => ctrl.abort();
}