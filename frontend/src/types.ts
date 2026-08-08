// Shared TypeScript types mirroring the backend's API shapes.

export interface Document {
  id: number;
  filename: string;
  chunk_count: number;
  uploaded_at: string;
}

export type Role = "user" | "assistant";

export interface Message {
  // `id` / `created_at` are absent for messages created optimistically on the
  // client before the server round-trip; present for messages loaded from history.
  id?: number;
  role: Role;
  content: string;
  created_at?: string;
}
