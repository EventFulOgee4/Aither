import { api } from "./client";

export async function logMood(mood, intensity, session = null) {
  const res = await api.post("/chat/moods/", { mood, intensity, session });
  return res.data;
}

export async function moodStats() {
  const res = await api.get("/chat/moods/");
  return res.data;
}