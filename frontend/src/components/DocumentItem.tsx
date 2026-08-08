import { FileText, Trash2 } from "lucide-react";

import type { Document } from "../types";

interface DocumentItemProps {
  doc: Document;
  onDelete: (id: number) => void;
}

/** A single document row with a confirm-on-click delete button. */
export default function DocumentItem({ doc, onDelete }: DocumentItemProps) {
  const handleDelete = () => {
    if (window.confirm(`Delete "${doc.filename}"?`)) {
      onDelete(doc.id);
    }
  };

  return (
    <li className="group flex items-center justify-between gap-2 rounded-md px-2 py-2 hover:bg-surface">
      <div className="flex min-w-0 items-center gap-2">
        <FileText className="h-4 w-4 shrink-0 text-teal" />
        <div className="min-w-0">
          <p className="truncate text-sm text-gray-800">{doc.filename}</p>
          <p className="text-xs text-gray-400">{doc.chunk_count} chunks</p>
        </div>
      </div>
      <button
        onClick={handleDelete}
        title="Delete document"
        aria-label={`Delete ${doc.filename}`}
        className="text-gray-400 opacity-0 transition hover:text-red-600 group-hover:opacity-100"
      >
        <Trash2 className="h-4 w-4" />
      </button>
    </li>
  );
}
