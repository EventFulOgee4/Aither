import { api } from "./client";

export async function login(username, password) {
  const res = await api.post("/token/", { username, password });
  localStorage.setItem("access", res.data.access);
  localStorage.setItem("refresh", res.data.refresh);
  return res.data;
}

export async function register(username, email, password) {
  // Create the account
  await api.post("/users/register/", { username, email, password });
  // Then log in automatically
  return login(username, password);
}

export function isAuthed() {
  return Boolean(localStorage.getItem("access"));
}

export function logout() {
  localStorage.removeItem("access");
  localStorage.removeItem("refresh");
}