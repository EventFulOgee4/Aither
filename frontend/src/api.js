const API_BASE = "http://127.0.0.1:8000/api/";

export async function getSessions() {
  const response = await fetch(API_BASE + "sessions/");
  return response.json();
}
