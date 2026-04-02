"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";

type DocumentRow = {
  id: number;
  title: string;
  source_type: string;
  uploaded_at: string;
  processed: boolean;
};

export default function AdminPage() {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api";
  const normalizedApi = useMemo(() => apiUrl.replace(/\/$/, ""), [apiUrl]);

  const [documents, setDocuments] = useState<DocumentRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busyIds, setBusyIds] = useState<number[]>([]);

  const loadDocuments = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${normalizedApi}/documents/`);
      if (!response.ok) {
        throw new Error(`Failed to load documents (${response.status}).`);
      }

      const rows = (await response.json()) as DocumentRow[];
      setDocuments(rows);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load documents.");
    } finally {
      setLoading(false);
    }
  }, [normalizedApi]);

  useEffect(() => {
    loadDocuments();
  }, [loadDocuments]);

  const triggerIngestion = async (id: number) => {
    setBusyIds((prev) => [...prev, id]);
    setError(null);

    try {
      const response = await fetch(`${normalizedApi}/documents/${id}/ingest/`, {
        method: "POST",
      });

      if (!response.ok) {
        throw new Error(`Ingestion failed for document ${id}.`);
      }

      await loadDocuments();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to ingest document.");
    } finally {
      setBusyIds((prev) => prev.filter((item) => item !== id));
    }
  };

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-5xl flex-col gap-4 px-4 py-8">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Document Admin</h1>
          <p className="text-sm text-slate-600">Review processing status and trigger ingestion.</p>
        </div>
        <Link href="/" className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white">
          Back to Chat
        </Link>
      </header>

      {error ? <p className="rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</p> : null}

      <section className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-50 text-slate-700">
            <tr>
              <th className="px-3 py-2">Title</th>
              <th className="px-3 py-2">Source</th>
              <th className="px-3 py-2">Uploaded</th>
              <th className="px-3 py-2">Status</th>
              <th className="px-3 py-2">Action</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={5} className="px-3 py-4 text-slate-500">
                  Loading documents...
                </td>
              </tr>
            ) : documents.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-3 py-4 text-slate-500">
                  No documents found.
                </td>
              </tr>
            ) : (
              documents.map((doc) => {
                const isBusy = busyIds.includes(doc.id);
                return (
                  <tr key={doc.id} className="border-t border-slate-100">
                    <td className="px-3 py-2 text-slate-900">{doc.title}</td>
                    <td className="px-3 py-2 text-slate-700">{doc.source_type}</td>
                    <td className="px-3 py-2 text-slate-700">
                      {new Date(doc.uploaded_at).toLocaleString()}
                    </td>
                    <td className="px-3 py-2">
                      <span
                        className={[
                          "rounded-full px-2 py-1 text-xs font-semibold",
                          doc.processed ? "bg-emerald-100 text-emerald-700" : "bg-amber-100 text-amber-700",
                        ].join(" ")}
                      >
                        {doc.processed ? "processed" : "pending"}
                      </span>
                    </td>
                    <td className="px-3 py-2">
                      <button
                        type="button"
                        onClick={() => triggerIngestion(doc.id)}
                        disabled={isBusy}
                        className="rounded-md border border-slate-300 px-3 py-1 text-xs font-semibold text-slate-800 transition hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-60"
                      >
                        {isBusy ? "Ingesting..." : "Ingest"}
                      </button>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </section>
    </main>
  );
}
