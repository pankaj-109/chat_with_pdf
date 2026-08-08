// Chat API: SSE streaming (via fetch) plus history read/clear and session reset
// (via the axios client). axios is avoided for the stream because it does not
// expose the response body as a readable stream in the browser.

import client, { API_URL } from "./client";
import { getOrCreateSessionId } from "../session";
import type { Message } from "../types";

/** Fetch the last 50 messages for the current session, oldest first. */
export async function getHistory(): Promise<Message[]> {
  const { data } = await client.get<Message[]>("/api/chat/history");
  return data;
}

/** Clear the conversation (messages only) for the current session. */
export async function clearHistory(): Promise<void> {
  await client.delete("/api/chat/history");
}

/** Wipe the entire session server-side (documents, messages, vectors). */
export async function resetSessionOnServer(): Promise<void> {
  await client.delete("/api/session");
}

/**
 * Stream a chat answer token-by-token from the SSE endpoint.
 *
 * @returns an AbortController the caller can use to cancel the stream.
 */
export function streamChatResponse(
  question: string,
  onToken: (token: string) => void,
  onDone: () => void,
  onError: (error: unknown) => void,
): AbortController {
  const controller = new AbortController();

  (async () => {
    try {
      const response = await fetch(`${API_URL}/api/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Session-Id": getOrCreateSessionId(),
        },
        body: JSON.stringify({ question }),
        signal: controller.signal,
      });

      if (!response.ok || !response.body) {
        throw new Error(`Chat request failed with status ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        // SSE events are separated by a blank line. Keep the trailing partial
        // event in the buffer until its terminator arrives.
        const events = buffer.split("\n\n");
        buffer = events.pop() ?? "";

        for (const event of events) {
          const line = event.trim();
          if (!line.startsWith("data:")) continue;
          const payload = line.slice("data:".length).trim();
          if (payload === "[DONE]") {
            onDone();
            return;
          }
          try {
            onToken(JSON.parse(payload) as string);
          } catch {
            // Ignore malformed event fragments.
          }
        }
      }
      onDone();
    } catch (error) {
      if (error instanceof DOMException && error.name === "AbortError") return;
      onError(error);
    }
  })();

  return controller;
}
