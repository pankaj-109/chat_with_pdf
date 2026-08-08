// Anonymous per-browser session identity. The session UUID is the only "user"
// concept in this app and is stored in localStorage.

import { v4 as uuidv4 } from "uuid";

const STORAGE_KEY = "pdfchat_session_id";

/** Return the existing session UUID, creating and persisting one if absent. */
export function getOrCreateSessionId(): string {
  let id = localStorage.getItem(STORAGE_KEY);
  if (!id) {
    id = uuidv4();
    localStorage.setItem(STORAGE_KEY, id);
  }
  return id;
}

/** Discard the current session UUID and generate a fresh one. Returns the new id. */
export function resetSession(): string {
  localStorage.removeItem(STORAGE_KEY);
  const id = uuidv4();
  localStorage.setItem(STORAGE_KEY, id);
  return id;
}
