import { FormEvent, useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { useChat } from "../hooks/useChat";
import type { ChatMessage, ToolCall } from "../types";

const SUGGESTED_QUERIES = [
  "Why is Press 1 running hot?",
  "What's the Cpk trend for panel thickness at Stamping?",
  "Compare Day shift vs Night shift OEE this month",
  "Show MTBF/MTTR for Station STP-01-PRS",
  "Should we reject Lot 4502 based on AQL sampling?",
  "Did the weld parameter change improve quality?",
  "What components are needed for PE-SV200?",
  "Create a work order for Press 1 hydraulic pump inspection",
];

function ToolCallBadge({ tc }: { tc: ToolCall }) {
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-blue-50 text-blue-700 text-xs rounded-full border border-blue-200">
      <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
        <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
      </svg>
      {tc.tool}
    </span>
  );
}

function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";

  return (
    <div className={`flex gap-3 ${isUser ? "justify-end" : ""}`}>
      {!isUser && (
        <div className="w-8 h-8 rounded-full bg-primeev-600 flex items-center justify-center flex-shrink-0">
          <span className="text-white text-xs font-bold">PE</span>
        </div>
      )}
      <div className={`max-w-[75%] ${isUser ? "order-first" : ""}`}>
        {!isUser && message.agent && (
          <div className="text-xs text-gray-400 mb-1">{message.agent}</div>
        )}
        <div
          className={`rounded-lg px-4 py-3 text-sm ${
            isUser
              ? "bg-primeev-600 text-white"
              : "bg-white border border-gray-200 text-gray-800"
          }`}
        >
          {isUser ? (
            <div className="whitespace-pre-wrap">{message.content || "..."}</div>
          ) : (
            <div className="prose prose-sm max-w-none prose-table:text-xs prose-td:py-1 prose-th:py-1">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  table: ({ children }) => (
                    <div className="overflow-x-auto my-2">
                      <table className="min-w-full border-collapse border border-gray-300 text-xs">{children}</table>
                    </div>
                  ),
                  th: ({ children }) => (
                    <th className="border border-gray-300 bg-gray-100 px-3 py-1.5 text-left font-semibold">{children}</th>
                  ),
                  td: ({ children }) => (
                    <td className="border border-gray-300 px-3 py-1.5">{children}</td>
                  ),
                  h1: ({ children }) => <h1 className="text-base font-bold mt-3 mb-1">{children}</h1>,
                  h2: ({ children }) => <h2 className="text-sm font-bold mt-3 mb-1">{children}</h2>,
                  h3: ({ children }) => <h3 className="text-sm font-semibold mt-2 mb-1">{children}</h3>,
                  ul: ({ children }) => <ul className="list-disc list-outside ml-4 my-1 space-y-0.5">{children}</ul>,
                  ol: ({ children }) => <ol className="list-decimal list-outside ml-4 my-1 space-y-0.5">{children}</ol>,
                  li: ({ children }) => <li className="leading-relaxed">{children}</li>,
                  code: ({ children, className }) =>
                    className ? (
                      <pre className="bg-gray-900 text-green-400 rounded p-3 my-2 overflow-x-auto text-xs">
                        <code>{children}</code>
                      </pre>
                    ) : (
                      <code className="bg-gray-100 text-red-600 px-1 py-0.5 rounded text-xs font-mono">{children}</code>
                    ),
                  blockquote: ({ children }) => (
                    <blockquote className="border-l-4 border-primeev-400 pl-3 my-2 text-gray-600 italic">{children}</blockquote>
                  ),
                  strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
                  hr: () => <hr className="my-3 border-gray-200" />,
                  p: ({ children }) => <p className="mb-2 last:mb-0 leading-relaxed">{children}</p>,
                }}
              >
                {message.content || "..."}
              </ReactMarkdown>
            </div>
          )}
        </div>
        {/* Tool calls */}
        {!isUser && message.toolCalls && message.toolCalls.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-1">
            {message.toolCalls.map((tc, i) => (
              <ToolCallBadge key={i} tc={tc} />
            ))}
          </div>
        )}
      </div>
      {isUser && (
        <div className="w-8 h-8 rounded-full bg-gray-300 flex items-center justify-center flex-shrink-0">
          <span className="text-gray-600 text-xs font-bold">ME</span>
        </div>
      )}
    </div>
  );
}

export default function ChatPage() {
  const { messages, isStreaming, sendMessage, stopStreaming, clearChat } = useChat();
  const [input, setInput] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isStreaming) return;
    sendMessage(input.trim());
    setInput("");
  };

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)]">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold text-gray-800">Agent Chat</h2>
        <button
          onClick={clearChat}
          className="text-sm text-gray-500 hover:text-gray-700 px-3 py-1 border border-gray-300 rounded"
        >
          New Chat
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto space-y-4 pb-4">
        {messages.length === 0 && (
          <div className="text-center py-12">
            <div className="text-4xl mb-4">PE</div>
            <h3 className="text-lg font-medium text-gray-700 mb-2">
              PrimeEV Factory Floor Agent
            </h3>
            <p className="text-sm text-gray-500 mb-6">
              Ask me about equipment, quality, production, or continuous improvement.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2 max-w-2xl mx-auto">
              {SUGGESTED_QUERIES.map((q) => (
                <button
                  key={q}
                  onClick={() => { setInput(q); }}
                  className="text-left text-sm px-3 py-2 bg-white border border-gray-200 rounded-lg hover:border-primeev-400 hover:bg-primeev-50 transition-colors"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}

        {isStreaming && (
          <div className="flex items-center gap-2 text-sm text-gray-400">
            <div className="flex gap-1">
              <span className="w-1.5 h-1.5 bg-primeev-500 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
              <span className="w-1.5 h-1.5 bg-primeev-500 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
              <span className="w-1.5 h-1.5 bg-primeev-500 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
            </div>
            Agent is thinking...
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="flex gap-2 pt-4 border-t border-gray-200">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about equipment, quality, production..."
          className="flex-1 px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primeev-500 focus:border-transparent text-sm"
          disabled={isStreaming}
        />
        {isStreaming ? (
          <button
            type="button"
            onClick={stopStreaming}
            className="px-4 py-2.5 bg-red-500 text-white rounded-lg hover:bg-red-600 text-sm font-medium"
          >
            Stop
          </button>
        ) : (
          <button
            type="submit"
            disabled={!input.trim()}
            className="px-4 py-2.5 bg-primeev-600 text-white rounded-lg hover:bg-primeev-700 disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium"
          >
            Send
          </button>
        )}
      </form>
    </div>
  );
}
