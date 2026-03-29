"use client";

import { useState, useRef, useEffect } from "react";
import Card from "@/components/Card";
import Button from "@/components/Button";
import { ChatMessage } from "@/types";

interface ChatPanelProps {
  title?: string;
  placeholder?: string;
  welcomeMessage?: string;
  apiEndpoint?: string;
  quickChips?: string[];
}

export default function ChatPanel({
  title = "Ask SATARK",
  placeholder = "Ask about UPI fraud, RBI guidelines, or how to stay safe…",
  welcomeMessage = "Hello! I'm SATARK, your UPI fraud protection assistant. I can help with reporting fraud, understanding refund policies, and staying safe. What would you like to know?",
  apiEndpoint = "/api/chat",
  quickChips = [],
}: ChatPanelProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "welcome",
      role: "assistant",
      content: welcomeMessage,
      timestamp: new Date().toISOString(),
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  async function handleSend(text?: string) {
    const toSend = (text || input).trim();
    if (!toSend || loading) return;

    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      content: toSend,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch(apiEndpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: toSend, history: messages }),
      });

      if (res.ok) {
        const assistantMsg: ChatMessage = await res.json();
        setMessages((prev) => [...prev, assistantMsg]);
      } else {
        setMessages((prev) => [
          ...prev,
          {
            id: `err-${Date.now()}`,
            role: "assistant",
            content: "Sorry, I couldn't process that. Please try again.",
            timestamp: new Date().toISOString(),
          },
        ]);
      }
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: `err-${Date.now()}`,
          role: "assistant",
          content: "Connection issue. Please check your network and try again.",
          timestamp: new Date().toISOString(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  // Show quick chips only when user hasn't sent any message yet
  const showChips = quickChips.length > 0 && messages.length <= 1;

  return (
    <Card padding="sm" className="flex flex-col" >
      <div className="flex items-center justify-between mb-3 px-1">
        <h3 className="text-sm font-semibold text-ink">{title}</h3>
        <span className="text-xs text-ink-faint">Powered by SATARK AI</span>
      </div>

      {/* Messages */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto space-y-3 mb-3 px-1"
        style={{ maxHeight: 360, minHeight: 200 }}
      >
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[85%] rounded-lg px-3 py-2 text-sm leading-relaxed ${
                msg.role === "user"
                  ? "bg-accent text-white"
                  : "bg-surface-100 text-ink"
              }`}
            >
              {/* Render markdown-like bold */}
              {msg.content.split("\n").map((line, i) => (
                <p key={i} className={i > 0 ? "mt-1.5" : ""}>
                  {line.replace(/\*\*(.*?)\*\*/g, "").length < line.length
                    ? line.split(/\*\*(.*?)\*\*/).map((part, j) =>
                        j % 2 === 1 ? (
                          <strong key={j}>{part}</strong>
                        ) : (
                          <span key={j}>{part}</span>
                        )
                      )
                    : line}
                </p>
              ))}
              {/* Source citations */}
              {msg.sources && msg.sources.length > 0 && (
                <div className="mt-2 pt-1.5" style={{ borderTop: "0.5px solid var(--border-color)" }}>
                  <p className="text-[11px] opacity-60 flex items-center gap-1">
                    <span>📎</span> Sources: {msg.sources.join(" · ")}
                  </p>
                </div>
              )}
            </div>
          </div>
        ))}

        {/* Quick chips */}
        {showChips && (
          <div className="flex flex-wrap gap-1.5 pt-1">
            {quickChips.map((chip) => (
              <button
                key={chip}
                onClick={() => handleSend(chip)}
                className="px-2.5 py-1 rounded-full text-xs bg-surface-100 text-ink-muted hover:bg-accent-light hover:text-accent transition-colors"
                style={{ border: "0.5px solid var(--border-color)" }}
              >
                {chip}
              </button>
            ))}
          </div>
        )}

        {loading && (
          <div className="flex justify-start">
            <div className="bg-surface-100 rounded-lg px-3 py-2 text-sm text-ink-faint">
              <span className="inline-flex gap-1">
                <span className="animate-bounce" style={{ animationDelay: "0ms" }}>●</span>
                <span className="animate-bounce" style={{ animationDelay: "150ms" }}>●</span>
                <span className="animate-bounce" style={{ animationDelay: "300ms" }}>●</span>
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Input */}
      <div className="flex gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={loading}
          className="flex-1 px-3 py-2 rounded-md text-sm bg-white text-ink placeholder:text-ink-faint focus:outline-none focus:ring-2 focus:ring-accent/30 disabled:opacity-50"
          style={{ border: "0.5px solid var(--border-color)" }}
        />
        <Button onClick={() => handleSend()} disabled={loading || !input.trim()} size="sm">
          Send
        </Button>
      </div>
    </Card>
  );
}
