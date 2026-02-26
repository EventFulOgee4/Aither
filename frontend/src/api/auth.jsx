// src/api/auth.jsx
import { api } from "./client";

export async function login(username, password) {
  // SimpleJWT expects username/password at /token/
  const res = await api.post("/token/", { username, password });

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