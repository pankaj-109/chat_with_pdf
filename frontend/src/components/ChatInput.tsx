import { useState, type KeyboardEvent } from "react";
import { Send, Trash2 } from "lucide-react";

interface ChatInputProps {
  disabled: boolean;
  onSend: (question: string) => void;
  onClear: () => void;
}

/** Message composer: Enter to send, Shift+Enter for a newline. */
export default function ChatInput({ disabled, onSend, onClear }: ChatInputProps) {
  const [text, setText] = useState("");

  const submit = () => {
    const question = text.trim();
    if (!question || disabled) return;
    onSend(question);
    setText("");
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  };

  return (
    <div className="border-t border-gray-200 bg-white p-4">
      <div className="flex items-end gap-2">
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          rows={1}
          placeholder="Ask a question about your documents..."
          className="max-h-40 flex-1 resize-none rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-coral focus:outline-none focus:ring-2 focus:ring-coral/40"
        />
        <button
          onClick={submit}
          disabled={disabled || !text.trim()}
          className="flex h-10 w-10 items-center justify-center rounded-lg bg-coral text-white hover:bg-coral-dark disabled:opacity-50"
          title="Send"
          aria-label="Send"
        >
          <Send className="h-4 w-4" />
        </button>
      </div>
      <button
        onClick={onClear}
        className="mt-2 flex items-center gap-1 text-xs text-gray-500 hover:text-red-600"
      >
        <Trash2 className="h-3 w-3" /> Clear conversation
      </button>
    </div>
  );
}
