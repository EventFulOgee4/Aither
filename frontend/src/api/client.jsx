import axios from "axios";

const BASE_URL = "http://127.0.0.1:8000/api";

export const api = axios.create({
  baseURL: BASE_URL,
});

// ==============================
// Attach access token to requests
// ==============================
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("access");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// ==============================
// Token refresh handling
// ==============================
let isRefreshing = false;
let failedQueue = [];

const processQueue = (error, token = null) => {
  failedQueue.forEach((prom) => {
    if (error) prom.reject(error);
    else prom.resolve(token);
  });
  failedQueue = [];
};

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (
      error.response?.status === 401 &&
      !originalRequest._retry
    ) {
      originalRequest._retry = true;

      const refresh = localStorage.getItem("refresh");

      if (!refresh) {
        localStorage.removeItem("access");
        localStorage.removeItem("refresh");
        return Promise.reject(error);
      }

      // If refresh already in progress, queue request
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        }).then((token) => {
          originalRequest.headers.Authorization = `Bearer ${token}`;
          return api(originalRequest);
        });
      }

      isRefreshing = true;

      try {
        const res = await axios.post(
          `${BASE_URL}/token/refresh/`,
          { refresh }
        );

        const newAccess = res.data.access;
        localStorage.setItem("access", newAccess);

        processQueue(null, newAccess);

        originalRequest.headers.Authorization = `Bearer ${newAccess}`;
        return api(originalRequest);
      } catch (err) {
        processQueue(err, null);
        localStorage.removeItem("access");
        localStorage.removeItem("refresh");
        return Promise.reject(err);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);
// ==============================
// Proactive refresh (avoid initial 401)
// ==============================
function getJwtPayload(token) {
  try {
    const base64 = token.split(".")[1];
    const json = atob(base64.replace(/-/g, "+").replace(/_/g, "/"));
    return JSON.parse(json);
  } catch {
    return null;
  }
}

function isExpired(token, skewSeconds = 30) {
  const payload = getJwtPayload(token);
  if (!payload?.exp) return true;
  const now = Math.floor(Date.now() / 1000);
  return payload.exp <= now + skewSeconds;
}

export async function ensureFreshAccessToken() {
  const access = localStorage.getItem("access");
  const refresh = localStorage.getItem("refresh");

  if (!refresh) return null;

  // If access token is valid, return it (ADDED PROACTIVE CHECK)
  if (access && !isExpired(access)) {
    return access; // still valid
  }

  try {
    const res = await axios.post(`${BASE_URL}/token/refresh/`, { refresh });
    const newAccess = res.data.access;
    localStorage.setItem("access", newAccess);
    return newAccess;
  } catch {
    localStorage.removeItem("access");
    localStorage.removeItem("refresh");
    return null;
  }
}
