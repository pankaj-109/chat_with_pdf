import { useRef, useState, type ChangeEvent } from "react";
import { Loader2, Upload } from "lucide-react";

import { uploadDocument } from "../api/documents";
import type { Document } from "../types";

interface UploadButtonProps {
  onUploaded: (doc: Document) => void;
}

/** Hidden file input + styled trigger button. Uploads a single PDF. */
export default function UploadButton({ onUploaded }: UploadButtonProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleChange = async (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setError(null);
    setUploading(true);
    try {
      const doc = await uploadDocument(file);
      onUploaded(doc);
    } catch (err) {
      const detail = (err as { response?: { data?: { detail?: string } } })
        ?.response?.data?.detail;
      setError(detail ?? "Upload failed. Please try again.");
    } finally {
      setUploading(false);
      // Reset so selecting the same file again still fires `change`.
      if (inputRef.current) inputRef.current.value = "";
    }
  };

  return (
    <div>
      <input
        ref={inputRef}
        type="file"
        accept="application/pdf"
        className="hidden"
        onChange={handleChange}
      />
      <button
        onClick={() => inputRef.current?.click()}
        disabled={uploading}
        className="flex w-full items-center justify-center gap-2 rounded-lg bg-coral px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-coral-dark disabled:opacity-60"
      >
        {uploading ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          <Upload className="h-4 w-4" />
        )}
        {uploading ? "Uploading..." : "Upload PDF"}
      </button>
      {error && <p className="mt-2 text-xs text-red-600">{error}</p>}
    </div>
  );
}
