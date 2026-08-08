import { useEffect, useRef } from "react";

import type { Message as MessageType } from "../types";
import Message from "./Message";

interface MessageListProps {
  messages: MessageType[];
  isStreaming: boolean;
}

/** Scrollable message list that auto-scrolls to the newest message. */
export default function MessageList({ messages, isStreaming }: MessageListProps) {
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="flex-1 space-y-4 overflow-y-auto p-6">
      {messages.map((message, index) => (
        <Message
          key={message.id ?? `pending-${index}`}
          message={message}
          streaming={
            isStreaming &&
            index === messages.length - 1 &&
            message.role === "assistant"
          }
        />
      ))}
      <div ref={endRef} />
    </div>
  );
}
