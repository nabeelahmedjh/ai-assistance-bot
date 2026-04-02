"use client";

import { FormEvent, useEffect, useMemo, useRef, useState } from "react";

type ChatRole = "user" | "assistant" | "system";

type ChatMessage = {
  id: string;
  role: ChatRole;
  text: string;
};

type HistoryTurn = {
  id: number;
  role: "user" | "assistant";
  message: string;
};

type SocketMessageEvent = {
  type: "message";
  request_id?: string;
  response?: {
    answer?: string;
  };
};

type SocketStreamStartEvent = {
  type: "stream_start";
  request_id: string;
};

type SocketStreamTokenEvent = {
  type: "stream_token";
  request_id: string;
  token: string;
};

type SocketStreamEndEvent = {
  type: "stream_end";
  request_id: string;
};

type SocketTypingEvent = {
  type: "typing";
  is_typing?: boolean;
};

type SocketErrorEvent = {
  type: "error";
  error?: string;
};

type SocketPayload =
  | SocketMessageEvent
  | SocketTypingEvent
  | SocketErrorEvent
  | SocketStreamStartEvent
  | SocketStreamTokenEvent
  | SocketStreamEndEvent;

type ChatWidgetProps = {
  leadId: string;
  apiUrl: string;
  wsUrl: string;
};

const statusTheme: Record<string, string> = {
  connected: "bg-emerald-500",
  connecting: "bg-amber-500",
  disconnected: "bg-slate-400",
};

export default function ChatWidget({ leadId, apiUrl, wsUrl }: ChatWidgetProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [status, setStatus] = useState("disconnected");
  const [assistantTyping, setAssistantTyping] = useState(false);
  const [connectionIssue, setConnectionIssue] = useState<string | null>(null);
  const [retryTick, setRetryTick] = useState(0);

  const socketRef = useRef<WebSocket | null>(null);
  const typingTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const historyContainerRef = useRef<HTMLDivElement | null>(null);
  const activeStreamIdRef = useRef<string | null>(null);

  const normalizedApi = useMemo(() => apiUrl.replace(/\/$/, ""), [apiUrl]);
  const normalizedWs = useMemo(() => wsUrl.replace(/\/$/, ""), [wsUrl]);

  useEffect(() => {
    const historyUrl = `${normalizedApi}/ai/chat/history/${encodeURIComponent(leadId)}/`;

    const loadHistory = async () => {
      try {
        const response = await fetch(historyUrl);
        if (!response.ok) {
          return;
        }

        const turns = (await response.json()) as HistoryTurn[];
        setMessages(
          turns.map((turn) => ({
            id: `history-${turn.id}`,
            role: turn.role,
            text: turn.message,
          })),
        );
      } catch {
        setMessages((prev) => [
          ...prev,
          {
            id: `system-history-${Date.now()}`,
            role: "system",
            text: "Could not load chat history yet.",
          },
        ]);
      }
    };

    loadHistory();
  }, [leadId, normalizedApi]);

  useEffect(() => {
    const socketUrl = `${normalizedWs}/ws/chat/${encodeURIComponent(leadId)}/`;
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
    let isActive = true;

    const socket = new WebSocket(socketUrl);
    socketRef.current = socket;

    socket.onopen = () => {
      setStatus("connected");
      setConnectionIssue(null);
    };

    socket.onclose = () => {
      setStatus("disconnected");
      setAssistantTyping(false);

      if (!isActive) {
        return;
      }

      reconnectTimer = setTimeout(() => {
        setRetryTick((prev) => prev + 1);
      }, 1200);
    };

    socket.onerror = () => {
      setConnectionIssue("WebSocket connection error. Retrying...");
    };

    socket.onmessage = (event) => {
      let payload: SocketPayload | null = null;
      try {
        payload = JSON.parse(event.data) as SocketPayload;
      } catch {
        return;
      }

      if (payload.type === "typing") {
        setAssistantTyping(Boolean(payload.is_typing));
        return;
      }

      if (payload.type === "stream_start") {
        const streamMessageId = `stream-${payload.request_id}`;
        activeStreamIdRef.current = streamMessageId;
        setAssistantTyping(true);
        setMessages((prev) => [
          ...prev,
          {
            id: streamMessageId,
            role: "assistant",
            text: "",
          },
        ]);
        return;
      }

      if (payload.type === "stream_token") {
        const streamMessageId = `stream-${payload.request_id}`;
        setMessages((prev) =>
          prev.map((message) =>
            message.id === streamMessageId
              ? { ...message, text: `${message.text}${payload.token}` }
              : message,
          ),
        );
        return;
      }

      if (payload.type === "stream_end") {
        setAssistantTyping(false);
        return;
      }

      if (payload.type === "error") {
        setMessages((prev) => [
          ...prev,
          {
            id: `system-error-${Date.now()}`,
            role: "system",
            text: payload.error || "Unexpected WebSocket error.",
          },
        ]);
        return;
      }

      if (payload.type === "message") {
        const assistantText = payload.response?.answer?.trim();
        if (!assistantText) {
          return;
        }

        const streamMessageId = payload.request_id ? `stream-${payload.request_id}` : activeStreamIdRef.current;

        setAssistantTyping(false);
        setMessages((prev) => {
          if (streamMessageId && prev.some((item) => item.id === streamMessageId)) {
            return prev.map((item) =>
              item.id === streamMessageId ? { ...item, text: assistantText } : item,
            );
          }

          return [
            ...prev,
            {
              id: `assistant-${Date.now()}`,
              role: "assistant",
              text: assistantText,
            },
          ];
        });

        activeStreamIdRef.current = null;
      }
    };

    return () => {
      isActive = false;
      if (reconnectTimer) {
        clearTimeout(reconnectTimer);
      }
      if (typingTimerRef.current) {
        clearTimeout(typingTimerRef.current);
      }
      socket.close();
      socketRef.current = null;
    };
  }, [leadId, normalizedWs, retryTick]);

  useEffect(() => {
    const container = historyContainerRef.current;
    if (!container) {
      return;
    }

    container.scrollTop = container.scrollHeight;
  }, [assistantTyping, messages]);

  const emitTyping = (isTyping: boolean) => {
    if (!socketRef.current || socketRef.current.readyState !== WebSocket.OPEN) {
      return;
    }

    socketRef.current.send(
      JSON.stringify({
        type: "typing",
        is_typing: isTyping,
      }),
    );
  };

  const onInputChange = (value: string) => {
    setInputValue(value);
    emitTyping(true);

    if (typingTimerRef.current) {
      clearTimeout(typingTimerRef.current);
    }

    typingTimerRef.current = setTimeout(() => {
      emitTyping(false);
    }, 700);
  };

  const onSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const text = inputValue.trim();
    if (!text) {
      return;
    }

    if (!socketRef.current || socketRef.current.readyState !== WebSocket.OPEN) {
      setMessages((prev) => [
        ...prev,
        {
          id: `system-offline-${Date.now()}`,
          role: "system",
          text: "Socket is not connected yet.",
        },
      ]);
      return;
    }

    setMessages((prev) => [
      ...prev,
      {
        id: `user-${Date.now()}`,
        role: "user",
        text,
      },
    ]);

    socketRef.current.send(
      JSON.stringify({
        type: "message",
        message: text,
      }),
    );

    setInputValue("");
    emitTyping(false);
  };

  const onRetryConnection = () => {
    setConnectionIssue(null);
    setRetryTick((prev) => prev + 1);
  };

  return (
    <section className="w-full max-w-3xl rounded-3xl border border-slate-200 bg-white/90 shadow-[0_24px_80px_-40px_rgba(2,6,23,0.45)] backdrop-blur">
      <header className="flex items-center justify-between border-b border-slate-200 px-5 py-4">
        <div>
          <h1 className="text-lg font-semibold tracking-tight text-slate-900">Sales Assistant</h1>
          <p className="text-sm text-slate-500">Lead: {leadId}</p>
        </div>

        <div className="flex items-center gap-2 rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-slate-700">
          <span className={`h-2.5 w-2.5 rounded-full ${statusTheme[status] || statusTheme.disconnected}`} />
          {status}
        </div>
      </header>

      {status !== "connected" ? (
        <div className="flex items-center justify-between gap-3 border-b border-amber-200 bg-amber-50 px-4 py-2 text-xs text-amber-900">
          <p>{connectionIssue || "Socket disconnected. Trying to reconnect..."}</p>
          <button
            type="button"
            onClick={onRetryConnection}
            className="rounded-md border border-amber-300 px-2 py-1 font-semibold transition hover:bg-amber-100"
          >
            Retry now
          </button>
        </div>
      ) : null}

      <div
        ref={historyContainerRef}
        className="h-[48vh] min-h-[260px] max-h-[460px] overflow-y-auto px-4 py-4"
      >
        <div className="flex flex-col gap-3">
          {messages.length === 0 ? (
            <p className="rounded-xl border border-dashed border-slate-300 bg-slate-50 p-4 text-sm text-slate-500">
              Ask about pricing, delivery, or container options to start the conversation.
            </p>
          ) : null}

          {messages.map((message) => {
            const isUser = message.role === "user";
            const isSystem = message.role === "system";

            return (
              <article
                key={message.id}
                className={[
                  "max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-6",
                  isUser
                    ? "ml-auto bg-teal-700 text-white"
                    : isSystem
                      ? "mx-auto bg-rose-50 text-rose-700"
                      : "bg-amber-50 text-slate-800",
                ].join(" ")}
              >
                {message.text}
              </article>
            );
          })}

          {assistantTyping ? (
            <div className="max-w-[85%] rounded-2xl bg-amber-100 px-4 py-3 text-sm text-slate-700">
              Assistant is typing...
            </div>
          ) : null}
        </div>
      </div>

      <form onSubmit={onSubmit} className="border-t border-slate-200 p-4">
        <div className="flex gap-2">
          <input
            value={inputValue}
            onChange={(event) => onInputChange(event.target.value)}
            placeholder="Type your question..."
            className="h-12 flex-1 rounded-xl border border-slate-300 bg-white px-4 text-sm text-slate-900 outline-none ring-teal-500 transition focus:ring-2"
          />
          <button
            type="submit"
            disabled={status !== "connected"}
            className="h-12 rounded-xl bg-slate-900 px-5 text-sm font-semibold text-white transition hover:bg-slate-700"
          >
            Send
          </button>
        </div>
      </form>
    </section>
  );
}
