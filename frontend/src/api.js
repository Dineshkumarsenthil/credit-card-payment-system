import axios from "axios";

export const DJANGO_URL = import.meta.env.VITE_DJANGO_URL || "http://127.0.0.1:8000";
export const PAYMENT_URL = import.meta.env.VITE_PAYMENT_URL || "http://127.0.0.1:8001";

export const api = axios.create({ baseURL: DJANGO_URL });
export const payApi = axios.create({ baseURL: PAYMENT_URL });

const isPublic = (url = "") => url.includes("/api/auth/login") || url.includes("/api/auth/register") || url.includes("/api/auth/refresh");

// Attach the JWT access token to every protected request
const attachToken = (config) => {
  const token = localStorage.getItem("access");
  if (token && !isPublic(config.url)) config.headers.Authorization = `Bearer ${token}`;
  return config;
};
api.interceptors.request.use(attachToken);
payApi.interceptors.request.use(attachToken);

// On 401, try the refresh token once, then retry the original request
let refreshing = null;
const onError = async (error) => {
  const original = error.config;
  const refresh = localStorage.getItem("refresh");
  if (error.response?.status === 401 && original && !original._retry && refresh && !isPublic(original.url)) {
    original._retry = true;
    try {
      refreshing = refreshing || axios.post(`${DJANGO_URL}/api/auth/refresh/`, { refresh });
      const { data } = await refreshing;
      refreshing = null;
      localStorage.setItem("access", data.access);
      if (data.refresh) localStorage.setItem("refresh", data.refresh);
      original.headers.Authorization = `Bearer ${data.access}`;
      return axios(original);
    } catch {
      refreshing = null;
      localStorage.clear();
      window.location.href = "/login";
    }
  }
  return Promise.reject(error);
};
api.interceptors.response.use((r) => r, onError);
payApi.interceptors.response.use((r) => r, onError);

// Turn Django / FastAPI error bodies into one readable line
export function errMsg(err) {
  const d = err.response?.data;
  if (!d) return err.message || "Something went wrong. Check that the servers are running.";
  if (typeof d === "string") return d;
  if (Array.isArray(d)) return d.join(" ");
  if (Array.isArray(d.detail)) return d.detail.map((x) => x.msg || JSON.stringify(x)).join(" ");
  if (d.detail) return String(d.detail);
  return Object.entries(d)
    .map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(" ") : typeof v === "object" ? JSON.stringify(v) : v}`)
    .join(" | ");
}
