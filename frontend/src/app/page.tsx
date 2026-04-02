"use client";

import { FormEvent, useMemo, useState } from "react";

import ChatWidget from "@/components/chat-widget";

export default function Home() {
  const defaultLeadId = process.env.NEXT_PUBLIC_DEFAULT_LEAD_ID || "lead-demo-1";
  const [draftLeadId, setDraftLeadId] = useState(defaultLeadId);
  const [activeLeadId, setActiveLeadId] = useState(defaultLeadId);

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api";
  const wsUrl = process.env.NEXT_PUBLIC_WS_URL || "ws://127.0.0.1:8001";

  const safeLeadId = useMemo(
    () => activeLeadId.trim().replace(/[^a-zA-Z0-9_-]/g, ""),
    [activeLeadId],
  );

  const onLeadSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const normalized = draftLeadId.trim().replace(/[^a-zA-Z0-9_-]/g, "");
    if (!normalized) {
      return;
    }

    setDraftLeadId(normalized);
    setActiveLeadId(normalized);
  };

  return (
    <main className="relative flex min-h-screen items-start justify-center overflow-x-hidden px-4 py-4 sm:items-center sm:py-8">
      <div className="pointer-events-none absolute -top-40 left-1/2 h-[420px] w-[640px] -translate-x-1/2 rounded-full bg-[radial-gradient(circle,rgba(13,148,136,0.22),rgba(13,148,136,0))]" />
      <div className="pointer-events-none absolute -bottom-44 right-0 h-[340px] w-[380px] rounded-full bg-[radial-gradient(circle,rgba(245,158,11,0.2),rgba(245,158,11,0))]" />

      <div className="z-10 flex w-full max-w-3xl flex-col gap-3">
        <form
          onSubmit={onLeadSubmit}
          className="flex flex-wrap items-center gap-2 rounded-2xl border border-slate-200 bg-white/85 p-3 shadow-[0_18px_40px_-30px_rgba(2,6,23,0.6)] backdrop-blur"
        >
          <label htmlFor="leadId" className="text-sm font-semibold text-slate-700">
            Lead ID
          </label>
          <input
            id="leadId"
            value={draftLeadId}
            onChange={(event) => setDraftLeadId(event.target.value)}
            placeholder="lead-demo-1"
            className="h-10 min-w-[220px] flex-1 rounded-lg border border-slate-300 bg-white px-3 text-sm text-slate-900 outline-none ring-teal-500 transition focus:ring-2"
          />
          <button
            type="submit"
            className="h-10 rounded-lg bg-slate-900 px-4 text-sm font-semibold text-white transition hover:bg-slate-700"
          >
            Start Chat
          </button>
        </form>

        <ChatWidget key={safeLeadId} leadId={safeLeadId} apiUrl={apiUrl} wsUrl={wsUrl} />
      </div>
    </main>
  );
}
