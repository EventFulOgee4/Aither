import { api } from "./client";

export async function logMood(mood, intensity, note = "") {
  const res = await api.post("/mood/", { mood, intensity, note });
  return res.data;
}

export async function moodStats() {
  const res = await api.get("/mood/stats/");
  return res.data;
}