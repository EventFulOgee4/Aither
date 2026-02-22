import { api } from "./client";

export async function login(username, password) {
  const res = await api.post("/auth/login/", { username, password });
  localStorage.setItem("access", res.data.access);
  localStorage.setItem("refresh", res.data.refresh);
  return res.data;
}

export function isAuthed() {
  return Boolean(localStorage.getItem("access"));
}

export function logout() {
  localStorage.removeItem("access");
  localStorage.removeItem("refresh");
}