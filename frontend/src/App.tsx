import { useCallback, useEffect, useRef, useState } from "react";

import {
  clearHistory,
  getHistory,
  resetSessionOnServer,
  streamChatResponse,
} from "./api/chat";
import { deleteDocument, listDocuments } from "./api/documents";
import { getOrCreateSessionId, resetSession } from "./session";
import type { Document, Message } from "./types";
import ChatArea from "./components/ChatArea";
import Sidebar from "./components/Sidebar";
import TopBar from "./components/TopBar";

export default function App() {
  // Ensure a session UUID exists from the very first render.
  const [sessionId, setSessionId] = useState<string>(() => getOrCreateSessionId());
  const [documents, setDocuments] = useState<Document[]>([]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  // Tracks the in-flight stream so we can cancel it on clear/reset/unmount.
  const abortRef = useRef<AbortController | null>(null);

  const stopStreaming = useCallback(() => {
    abortRef.current?.abort();
    abortRef.current = null;
    setIsStreaming(false);
  }, []);

  // Cancel any in-flight stream when the component unmounts.
  useEffect(() => () => abortRef.current?.abort(), []);

  const loadState = useCallback(async () => {
    try {
      const [docs, history] = await Promise.all([listDocuments(), getHistory()]);
      setDocuments(docs);
      setMessages(history);
    } catch (err) {
      // Network/initial-load failure is non-fatal; the UI just starts empty.
      console.error("Failed to load session state:", err);
    }
  }, []);

  useEffect(() => {
    void loadState();
  }, [loadState]);

  const handleUploaded = (doc: Document) => {
    setDocuments((prev) => [doc, ...prev]);
  };

  const handleDeleteDocument = async (id: number) => {
    try {
      await deleteDocument(id);
      setDocuments((prev) => prev.filter((doc) => doc.id !== id));
    } catch (err) {
      console.error("Failed to delete document:", err);
    }
  };

  // Replace the trailing assistant message via a transform. No-op if the last
  // message isn't an assistant bubble (e.g. the conversation was cleared/reset
  // mid-stream and the array was emptied) — so late tokens can't crash the update.
  const replaceLastAssistant = (transform: (last: Message) => Message) =>
    setMessages((prev) => {
      const last = prev[prev.length - 1];
      if (!last || last.role !== "assistant") return prev;
      const next = [...prev];
      next[next.length - 1] = transform(last);
      return next;
    });

  const appendToLast = (token: string) =>
    replaceLastAssistant((last) => ({ ...last, content: last.content + token }));

  const handleSend = (question: string) => {
    // Optimistically append the user message and an empty assistant placeholder.
    setMessages((prev) => [
      ...prev,
      { role: "user", content: question },
      { role: "assistant", content: "" },
    ]);
    setIsStreaming(true);

    abortRef.current = streamChatResponse(
      question,
      appendToLast,
      () => {
        abortRef.current = null;
        setIsStreaming(false);
      },
      (err) => {
        console.error("Chat stream error:", err);
        abortRef.current = null;
        setIsStreaming(false);
        replaceLastAssistant(() => ({
          role: "assistant",
          content: "Sorry, something went wrong. Please try again.",
        }));
      },
    );
  };

  const handleClearConversation = async () => {
    stopStreaming();
    try {
      await clearHistory();
      setMessages([]);
    } catch (err) {
      console.error("Failed to clear conversation:", err);
    }
  };

  const handleResetSession = async () => {
    stopStreaming();
    try {
      await resetSessionOnServer();
    } catch (err) {
      console.error("Failed to reset session on server:", err);
    }
    // Always rotate the local session id so the user gets a clean slate.
    const newId = resetSession();
    setSessionId(newId);
    setDocuments([]);
    setMessages([]);
  };

  return (
    <div className="flex h-screen flex-col">
      <TopBar sessionId={sessionId} />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar
          documents={documents}
          onUploaded={handleUploaded}
          onDelete={handleDeleteDocument}
          onReset={handleResetSession}
        />
        <ChatArea
          documents={documents}
          messages={messages}
          isStreaming={isStreaming}
          onSend={handleSend}
          onClear={handleClearConversation}
        />
      </div>
    </div>
  );
}
