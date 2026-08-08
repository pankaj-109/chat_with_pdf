// Document-related API calls (list, upload, delete) using the axios client.

import client from "./client";
import type { Document } from "../types";

/** List the current session's documents. */
export async function listDocuments(): Promise<Document[]> {
  const { data } = await client.get<Document[]>("/api/documents");
  return data;
}

/** Upload a PDF, optionally reporting upload progress (0-100). */
export async function uploadDocument(
  file: File,
  onProgress?: (percent: number) => void,
): Promise<Document> {
  const form = new FormData();
  form.append("file", file);
  const { data } = await client.post<Document>("/api/documents", form, {
    onUploadProgress: (event) => {
      if (onProgress && event.total) {
        onProgress(Math.round((event.loaded / event.total) * 100));
      }
    },
  });
  return data;
}

/** Delete a document (and its chunks) by id. */
export async function deleteDocument(id: number): Promise<void> {
  await client.delete(`/api/documents/${id}`);
}
