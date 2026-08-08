import ReactMarkdown, { type Components } from "react-markdown";
import remarkGfm from "remark-gfm";

import type { Message as MessageType } from "../types";

// Map markdown elements to Tailwind utility classes. This keeps styling to
// "plain Tailwind" (no @tailwindcss/typography plugin) while still rendering
// lists, code, tables, etc. legibly against Tailwind's preflight reset.
const markdownComponents: Components = {
  p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
  ul: ({ children }) => <ul className="mb-2 list-disc pl-5">{children}</ul>,
  ol: ({ children }) => <ol className="mb-2 list-decimal pl-5">{children}</ol>,
  li: ({ children }) => <li className="mb-1">{children}</li>,
  h1: ({ children }) => <h1 className="mb-2 text-base font-bold">{children}</h1>,
  h2: ({ children }) => <h2 className="mb-2 text-base font-semibold">{children}</h2>,
  h3: ({ children }) => <h3 className="mb-1 text-sm font-semibold">{children}</h3>,
  code: ({ children }) => (
    <code className="rounded bg-gray-100 px-1 py-0.5 font-mono text-xs">
      {children}
    </code>
  ),
  pre: ({ children }) => (
    <pre className="mb-2 overflow-x-auto rounded bg-gray-100 p-2 text-xs">
      {children}
    </pre>
  ),
  a: ({ children, href }) => (
    <a
      href={href}
      target="_blank"
      rel="noreferrer"
      className="text-teal underline"
    >
      {children}
    </a>
  ),
  strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
  blockquote: ({ children }) => (
    <blockquote className="mb-2 border-l-2 border-gray-300 pl-3 italic text-gray-600">
      {children}
    </blockquote>
  ),
  table: ({ children }) => (
    <table className="my-2 border-collapse text-xs">{children}</table>
  ),
  th: ({ children }) => (
    <th className="border border-gray-300 bg-gray-50 px-2 py-1">{children}</th>
  ),
  td: ({ children }) => (
    <td className="border border-gray-300 px-2 py-1">{children}</td>
  ),
};

interface MessageProps {
  message: MessageType;
  streaming?: boolean;
}

/** A single chat bubble. User messages are plain text; assistant messages render markdown. */
export default function Message({ message, streaming }: MessageProps) {
  const isUser = message.role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-2 text-sm ${
          isUser
            ? "bg-navy text-white"
            : "border border-gray-200 bg-white text-gray-800 shadow-sm"
        }`}
      >
        {isUser ? (
          <span className="whitespace-pre-wrap">{message.content}</span>
        ) : (
          <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
            {message.content}
          </ReactMarkdown>
        )}
        {streaming && (
          <span className="ml-0.5 inline-block h-4 w-2 animate-pulse bg-coral align-middle" />
        )}
      </div>
    </div>
  );
}
