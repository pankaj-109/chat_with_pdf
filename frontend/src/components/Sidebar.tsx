import { useState } from "react";
import { RotateCcw } from "lucide-react";

import type { Document } from "../types";
import ConfirmModal from "./ConfirmModal";
import DocumentList from "./DocumentList";
import UploadButton from "./UploadButton";

interface SidebarProps {
  documents: Document[];
  onUploaded: (doc: Document) => void;
  onDelete: (id: number) => void;
  onReset: () => void;
}

/** Left column: upload, document list, and the destructive reset action. */
export default function Sidebar({
  documents,
  onUploaded,
  onDelete,
  onReset,
}: SidebarProps) {
  const [confirmOpen, setConfirmOpen] = useState(false);

  return (
    <aside className="flex w-[280px] shrink-0 flex-col border-r border-gray-200 bg-white">
      <div className="flex-1 space-y-4 overflow-y-auto p-4">
        <UploadButton onUploaded={onUploaded} />
        <div>
          <h2 className="mb-1 px-2 text-xs font-semibold uppercase tracking-wide text-teal">
            Documents
          </h2>
          <DocumentList documents={documents} onDelete={onDelete} />
        </div>
      </div>

      <div className="border-t border-gray-200 p-4">
        <button
          onClick={() => setConfirmOpen(true)}
          className="flex w-full items-center justify-center gap-2 rounded-lg border border-red-200 px-4 py-2 text-sm text-red-600 hover:bg-red-50"
        >
          <RotateCcw className="h-4 w-4" /> Reset session
        </button>
      </div>

      <ConfirmModal
        open={confirmOpen}
        title="Reset session?"
        message="This permanently deletes all your documents and chat history and starts a fresh session."
        confirmLabel="Reset everything"
        onConfirm={() => {
          setConfirmOpen(false);
          onReset();
        }}
        onCancel={() => setConfirmOpen(false)}
      />
    </aside>
  );
}
