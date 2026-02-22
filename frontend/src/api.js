export async function createSession() {
  const token = localStorage.getItem("access");

  const response = await fetch(API_BASE + "chat/sessions/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ title: "New Session" }),
  });

  return response.json();
}

export async function sendMessage(sessionId, message) {
  const token = localStorage.getItem("access");

  const response = await fetch(API_BASE + "chat/messages/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({
      session: sessionId,
      message: message,
    }),
  });

  return response.json();
}