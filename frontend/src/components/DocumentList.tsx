import type { Document } from "../types";
import DocumentItem from "./DocumentItem";

interface DocumentListProps {
  documents: Document[];
  onDelete: (id: number) => void;
}

/** The list of uploaded documents, or an empty hint. */
export default function DocumentList({ documents, onDelete }: DocumentListProps) {
  if (documents.length === 0) {
    return <p className="px-2 py-4 text-xs text-gray-400">No documents yet.</p>;
  }

  return (
    <ul className="space-y-1">
      {documents.map((doc) => (
        <DocumentItem key={doc.id} doc={doc} onDelete={onDelete} />
      ))}
    </ul>
  );
}
