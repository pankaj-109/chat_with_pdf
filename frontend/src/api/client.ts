// Axios instance that automatically attaches the session header to every request.

import axios from "axios";

import { getOrCreateSessionId } from "../session";

export const API_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const client = axios.create({ baseURL: API_URL });

client.interceptors.request.use((config) => {
  config.headers["X-Session-Id"] = getOrCreateSessionId();
  return config;
});

export default client;