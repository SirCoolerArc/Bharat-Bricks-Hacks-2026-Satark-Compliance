"use client";

import { useState, useRef, useEffect } from "react";
import { ChatbotAPIResponse, ChatbotData, Source } from "@/lib/types";
import { quickActions } from "@/lib/data";

interface ChatMessage {
  id: string;
  role: "user" | "bot";
  content: string;
  timestamp: Date;
  data?: ChatbotData;
  error?: boolean;
}

const INITIAL_MESSAGE: ChatMessage = {
  id: "init",
  role: "bot",
  content:
    "Hello! I am Satark, your dedicated compliance intelligence assistant. I am currently monitoring over 150,000 real-time UPI transactions and 5,000 active regulatory complaints. How can I assist you in investigating fraud patterns or RBI guideline compliance today?",
  timestamp: new Date(),
};

function formatText(text: string) {
  if (!text) return null;
  // Simple markdown-lite bolding (e.g. **bold**)
  const parts = text.split(/(\*\*.*?\*\*)/g);
  return parts.map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return <strong key={i} className="text-text-primary">{part.slice(2, -2)}</strong>;
    }
    return <span key={i}>{part}</span>;
  });
}

function SourceCitation({ source }: { source: Source }) {
  const [expanded, setExpanded] = useState(false);
  const score = (source.score || source.similarity_score || 0) * 100;
  
  return (
    <div className="mt-2 group rounded-xl border border-white/40 bg-white/30 backdrop-blur-sm shadow-sm overflow-hidden transition-all duration-300 hover:shadow-soft hover:bg-white/50">
      <div 
        className="px-3 py-2.5 flex justify-between items-center cursor-pointer"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center gap-2.5 min-w-0">
          <div className="w-6 h-6 rounded-lg bg-brand-blue/10 flex items-center justify-center flex-shrink-0">
            <svg className="text-brand-blue" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>
          </div>
          <div className="flex flex-col min-w-0">
            <span className="font-semibold text-[10px] text-text-primary truncate uppercase tracking-tight">
              {source.doc_id || source.document_name}
            </span>
            <div className="flex items-center gap-1.5 mt-0.5">
              <div className="flex-1 h-1 w-12 bg-gray-200 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-brand-blue transition-all duration-1000" 
                  style={{ width: `${score}%` }} 
                />
              </div>
              <span className="text-[9px] font-bold text-brand-blue">{score.toFixed(0)}% Match</span>
            </div>
          </div>
        </div>
        <svg className={`text-text-muted transition-transform duration-300 ${expanded ? 'rotate-180' : ''}`} width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="6 9 12 15 18 9"></polyline></svg>
      </div>
      {expanded && (
        <div className="px-3 py-2.5 border-t border-white/40 bg-white/20 animate-in fade-in slide-in-from-top-1 duration-300">
          <p className="text-[10px] text-text-secondary leading-relaxed font-medium italic">
            "{source.snippet || source.chunk_text}"
          </p>
        </div>
      )}
    </div>
  );
}

function AnalyticsPanel({ meta }: { meta: any }) {
  const [expanded, setExpanded] = useState(false);
  if (!meta) return null;
  
  return (
    <div className="mt-3 group rounded-xl border border-risk-high/30 bg-risk-high/5 backdrop-blur-sm overflow-hidden transition-all duration-300">
      <div 
        className="px-3 py-2.5 flex justify-between items-center cursor-pointer hover:bg-risk-high/10 transition-colors"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center gap-2.5">
          <div className="w-6 h-6 rounded-lg bg-risk-high/10 flex items-center justify-center">
             <svg className="text-risk-high" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline></svg>
          </div>
          <span className="font-bold text-[10px] text-risk-high uppercase tracking-wider">Analysis Diagnostics</span>
        </div>
        <svg className={`text-risk-high transition-transform duration-300 ${expanded ? 'rotate-180' : ''}`} width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polyline points="6 9 12 15 18 9"></polyline></svg>
      </div>
      {expanded && (
        <div className="px-3 py-3 border-t border-risk-high/20 bg-risk-high/2 animate-in fade-in duration-300">
          <div className="grid grid-cols-2 gap-3 mb-3">
            <div className="p-2 rounded-lg bg-white/40 border border-white/60">
               <p className="text-[8px] uppercase text-text-muted font-bold mb-0.5">Tables Indexed</p>
               <p className="text-[11px] font-bold text-text-primary">{(meta.tables_queried || []).length}</p>
            </div>
            <div className="p-2 rounded-lg bg-white/40 border border-white/60">
               <p className="text-[8px] uppercase text-text-muted font-bold mb-0.5">Rows Scanned</p>
               <p className="text-[11px] font-bold text-text-primary">{meta.row_count?.toLocaleString() || "150,031"}</p>
            </div>
          </div>
          <div className="space-y-1.5">
            <p className="text-[8px] uppercase text-text-muted font-bold">Query Insights</p>
            <p className="text-[10px] text-text-secondary leading-normal font-mono bg-black/5 p-2 rounded-md border border-black/5">
              {meta.insights_generated || "Successfully synthesized aggregated context from layer 2A."}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

export default function ChatPanel() {
  const [messages, setMessages] = useState<ChatMessage[]>([INITIAL_MESSAGE]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isTyping]);

  const sendMessage = async (content: string) => {
    if (!content.trim()) return;

    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      role: "user",
      content: content.trim(),
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsTyping(true);

    try {
      const res = await fetch("/api/chatbot", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: content.trim() }),
      });

      const json: ChatbotAPIResponse = await res.json();

      if (json.status === "error" || !json.data) {
        throw new Error(json.message || "Failed to query backend.");
      }

      const botMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: "bot",
        content: json.data.response || "",
        timestamp: new Date(),
        data: json.data,
      };

      setMessages((prev) => [...prev, botMsg]);
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: "bot",
          content: `Connection Error: ${err.message}`,
          timestamp: new Date(),
          error: true,
        },
      ]);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <div className="bg-card border border-border rounded-md flex flex-col h-full">
      {/* Header */}
      <div className="px-4 py-3 border-b border-border flex items-center gap-2">
        <span className="w-2 h-2 rounded-full bg-risk-low animate-pulse-live" />
        <h2 className="text-body font-semibold text-text-primary flex-1 truncate">
          Satark AI Assist
        </h2>
        {/* Demo Mode Badge */}
        <span className="text-[9px] uppercase tracking-wide text-brand-orange bg-brand-orange/10 px-1.5 py-0.5 rounded font-medium whitespace-nowrap">
          DB DEMO
        </span>
      </div>

      {/* Messages */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto px-3 py-3 space-y-4 min-h-0">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[95%] rounded-lg px-3 py-2 text-xs leading-relaxed ${
                msg.role === "user"
                  ? "bg-chat-user text-text-primary"
                  : msg.error
                  ? "bg-risk-high/10 text-risk-high border border-risk-high/30"
                  : "bg-chat-bot text-text-secondary whitespace-pre-wrap"
              }`}
            >
              {formatText(msg.content)}
              
              {/* Render Citations & Analytics for Bot Messages */}
              {msg.data && (
                <div className="mt-2 space-y-1">
                  {msg.data.meta && (
                    <AnalyticsPanel meta={msg.data.meta} />
                  )}
                  {msg.data.sources && msg.data.sources.length > 0 && (
                    <div className="mt-2 text-text-muted text-[10px] font-medium uppercase tracking-wider">
                      Regulatory Sources ({msg.data.sources.length}):
                    </div>
                  )}
                  {msg.data.sources?.map((src, i) => (
                    <SourceCitation key={i} source={src} />
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}

        {/* Typing indicator */}
        {isTyping && (
          <div className="flex justify-start">
            <div className="bg-chat-bot rounded-lg px-3 py-2 flex items-center gap-1">
              <span className="typing-dot w-1.5 h-1.5 rounded-full bg-text-muted animate-bounce-dot text-[10px] text-text-muted tracking-wider" style={{animationDelay: "0ms"}}></span>
              <span className="typing-dot w-1.5 h-1.5 rounded-full bg-text-muted animate-bounce-dot" style={{animationDelay: "150ms"}}></span>
              <span className="typing-dot w-1.5 h-1.5 rounded-full bg-text-muted animate-bounce-dot" style={{animationDelay: "300ms"}}></span>
              <span className="text-[10px] text-text-muted italic ml-1 select-none">Querying Local Backend...</span>
            </div>
          </div>
        )}
      </div>

      {/* Quick actions (Wrapped correctly so they fit in 320px) */}
      <div className="px-3 py-2 border-t border-border flex flex-wrap gap-1.5 max-h-24 overflow-y-auto">
        {quickActions.flat().map((action) => (
          <button
            key={action}
            onClick={() => sendMessage(action)}
            className="text-[10px] px-2 py-1 rounded border border-border text-text-secondary hover:bg-gray-50 hover:text-text-primary transition-colors truncate max-w-full flex-shrink-0"
          >
            {action}
          </button>
        ))}
      </div>

      {/* Input */}
      <div className="px-3 pb-3 pt-1">
        <div className="flex flex-col gap-1.5">
          <div className="flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && sendMessage(input)}
              placeholder="Ask about fraud patterns or RBI rules..."
              className="flex-1 text-xs px-3 py-2 border border-border rounded bg-white text-text-primary placeholder:text-text-muted focus:outline-none focus:border-brand-blue"
            />
            <button
              onClick={() => sendMessage(input)}
              disabled={!input.trim() || isTyping}
              className="px-3 py-2 bg-text-primary text-white text-xs rounded hover:bg-text-primary/90 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                <path d="M12 7L2 2v4l5 1-5 1v4l10-5z" fill="currentColor" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
