import { FileText } from "lucide-react";

interface TopBarProps {
  sessionId: string;
}

/** Top bar: app title and a small (non-secret) session indicator. */
export default function TopBar({ sessionId }: TopBarProps) {
  return (
    <header className="flex items-center justify-between bg-navy px-6 py-3">
      <div className="flex items-center gap-2.5">
        {/* coral accent bar echoing the deck's title underline */}
        <span className="h-5 w-1 rounded-full bg-coral" />
        <FileText className="h-5 w-5 text-coral" />
        <h1 className="text-lg font-semibold tracking-tight text-white">
          Chat with PDF
        </h1>
      </div>
      <span className="rounded bg-white/10 px-2 py-1 font-mono text-xs text-teal-light">
        Session: {sessionId.slice(0, 5)}...
      </span>
    </header>
  );
}
