import { FileUp, MessageSquare } from "lucide-react";

import type { Document, Message } from "../types";
import ChatInput from "./ChatInput";
import MessageList from "./MessageList";

interface ChatAreaProps {
  documents: Document[];
  messages: Message[];
  isStreaming: boolean;
  onSend: (question: string) => void;
  onClear: () => void;
}

/** Center column: message list (or empty state) plus the composer. */
export default function ChatArea({
  documents,
  messages,
  isStreaming,
  onSend,
  onClear,
}: ChatAreaProps) {
  const hasDocuments = documents.length > 0;

  return (
    <main className="flex min-w-0 flex-1 flex-col bg-surface">
      {messages.length === 0 ? (
        <div className="flex flex-1 flex-col items-center justify-center p-6 text-center text-gray-500">
          {hasDocuments ? (
            <>
              <MessageSquare className="mb-3 h-10 w-10 text-teal-light" />
              <p>Ask me anything about your documents</p>
            </>
          ) : (
            <>
              <FileUp className="mb-3 h-10 w-10 text-teal-light" />
              <p>Upload a PDF to get started</p>
            </>
          )}
        </div>
      ) : (
        <MessageList messages={messages} isStreaming={isStreaming} />
      )}
      <ChatInput disabled={isStreaming} onSend={onSend} onClear={onClear} />
    </main>
  );
}
