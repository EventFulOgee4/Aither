export const BASE_URL = (import.meta.env?.VITE_API_BASE_URL || "http://127.0.0.1:8000/api").replace(/\/$/, "");
let refreshPromise = null;

function isExpired(token) {
  try {
    const payload = JSON.parse(atob(token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/")));
    return !payload.exp || payload.exp <= Date.now() / 1000 + 30;
  } catch { return true; }
}

async function fetchJSON(path, { method = "GET", data, token, params = {} } = {}) {
  const url = new URL(`${BASE_URL}${path}`, globalThis.location?.origin || "http://localhost");
  for (const [key, value] of Object.entries(params)) url.searchParams.set(key, value);
  const response = await fetch(url, {
    method,
    headers: { ...(data !== undefined ? { "Content-Type": "application/json" } : {}), ...(token ? { Authorization: `Bearer ${token}` } : {}) },
    body: data === undefined ? undefined : JSON.stringify(data),
    signal: AbortSignal.timeout(60000),
  });
  const body = response.status === 204 ? null : await response.json();
  if (!response.ok) {
    const error = new Error(body?.detail || "Request failed. Please try again.");
    error.response = { status: response.status, data: body };
    throw error;
  }
  return { data: body };
}

export async function ensureFreshAccessToken(force = false) {
  const access = localStorage.getItem("access");
  if (!force && access && !isExpired(access)) return access;
  const refresh = localStorage.getItem("refresh");
  if (!refresh) return null;
  if (!refreshPromise) {
    refreshPromise = fetchJSON("/token/refresh/", { method: "POST", data: { refresh } })
      .then(({ data }) => {
        localStorage.setItem("access", data.access);
        if (data.refresh) localStorage.setItem("refresh", data.refresh);
        return data.access;
      })
      .catch((error) => {
        if ([400, 401].includes(error.response?.status)) {
          localStorage.removeItem("access");
          localStorage.removeItem("refresh");
        }
        throw error;
      })
      .finally(() => { refreshPromise = null; });
  }
  return refreshPromise;
}

async function request(path, options) {
  try {
    return await fetchJSON(path, { ...options, token: localStorage.getItem("access") });
  } catch (error) {
    if (error.response?.status !== 401 || path === "/token/") throw error;
    const token = await ensureFreshAccessToken(true);
    if (!token) throw error;
    return fetchJSON(path, { ...options, token });
  }
}

export const api = {
  get: (path, options = {}) => request(path, options),
  post: (path, data) => request(path, { method: "POST", data }),
  delete: (path) => request(path, { method: "DELETE" }),
};
