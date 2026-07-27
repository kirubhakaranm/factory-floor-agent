import { createContext, useContext, FormEvent, useEffect, useRef, useState, useCallback } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { useChat } from "../hooks/useChat";
import { reformatMessage } from "../api/chat";
import { listSessions } from "../api/sessions";
import type { SessionSummary } from "../api/sessions";
import type { ChatMessage, Citation, ResponseMode, ToolTrace } from "../types";

// ─── Theme ────────────────────────────────────────────────────────────────────

const DarkCtx = createContext(true);
const useDark = () => useContext(DarkCtx);

const T = {
  dark: {
    root:        "bg-[#111111] border-[#1e1e1e]",
    header:      "border-[#1e1e1e] bg-[#111111]",
    body:        "bg-[#111111]",
    card:        "bg-[#1e1e1e] border-[#2a2a2a] hover:border-[#3a3a3a]",
    input:       "bg-[#1a1a1a] border-[#2a2a2a] focus-within:border-[#3a3a3a]",
    sidebar:     "border-[#1e1e1e] bg-[#111111]",
    divider:     "border-[#1a1a1a]",
    divider2:    "border-[#1e1e1e]",
    btn:         "border-[#2a2a2a] text-gray-600 hover:text-gray-400",
    btnActive:   "bg-blue-900/20 text-blue-400 border-blue-900/40",
    text1:       "text-gray-100",
    text2:       "text-gray-200",
    text3:       "text-gray-400",
    text4:       "text-gray-600",
    text5:       "text-gray-700",
    label:       "text-gray-700",
    badge:       "bg-[#1a1a1a] text-gray-600 border-[#2a2a2a]",
    badgeErr:    "bg-red-900/20 text-red-400 border-red-800/30",
    iconBg:      "bg-[#2a2a2a]",
    sendBtn:     "bg-[#2a2a2a] text-gray-400 hover:bg-[#3a3a3a]",
    stopBtn:     "bg-red-900/30 text-red-400 hover:bg-red-900/50",
    suggestBtn:  "bg-[#1a1a1a] border-[#2a2a2a] hover:border-[#3a3a3a] text-gray-500 hover:text-gray-300",
    dot:         "bg-gray-700",
    prose:       "[&_p]:text-gray-200 [&_p]:leading-relaxed [&_p]:my-2 " +
                 "[&_h1]:text-gray-100 [&_h1]:font-semibold [&_h1]:text-base [&_h1]:mt-4 [&_h1]:mb-1 " +
                 "[&_h2]:text-gray-100 [&_h2]:font-semibold [&_h2]:text-sm [&_h2]:mt-4 [&_h2]:mb-1 " +
                 "[&_h3]:text-gray-200 [&_h3]:font-semibold [&_h3]:text-sm [&_h3]:mt-3 [&_h3]:mb-1 " +
                 "[&_li]:text-gray-200 [&_li]:leading-relaxed " +
                 "[&_strong]:text-gray-100 [&_strong]:font-semibold " +
                 "[&_ul]:list-disc [&_ul]:list-outside [&_ul]:ml-5 [&_ul]:my-2 [&_ul]:space-y-1 " +
                 "[&_ol]:list-decimal [&_ol]:list-outside [&_ol]:ml-5 [&_ol]:my-2 [&_ol]:space-y-1 " +
                 "[&_hr]:border-[#2a2a2a] [&_hr]:my-3 " +
                 "[&_blockquote]:border-l-4 [&_blockquote]:border-[#2a2a2a] [&_blockquote]:pl-4 [&_blockquote]:text-gray-500",
    tableHeader: "bg-[#1e1e1e] border-[#2a2a2a] text-gray-300",
    tableCell:   "border-[#2a2a2a] text-gray-400",
    codePre:     "bg-[#0d0d0d] text-green-400 border-[#2a2a2a]",
    codeInline:  "bg-[#1a1a1a] text-green-400 border-[#2a2a2a]",
    placeholder: "placeholder-gray-700",
    inputText:   "text-gray-200",
  },
  light: {
    root:        "bg-gray-50 border-gray-200",
    header:      "border-gray-200 bg-gray-50",
    body:        "bg-gray-50",
    card:        "bg-white border-gray-200 hover:border-gray-300",
    input:       "bg-white border-gray-300 focus-within:border-gray-400",
    sidebar:     "border-gray-200 bg-white",
    divider:     "border-gray-100",
    divider2:    "border-gray-200",
    btn:         "border-gray-300 text-gray-500 hover:text-gray-700",
    btnActive:   "bg-blue-50 text-blue-600 border-blue-300",
    text1:       "text-gray-900",
    text2:       "text-gray-800",
    text3:       "text-gray-600",
    text4:       "text-gray-400",
    text5:       "text-gray-300",
    label:       "text-gray-400",
    badge:       "bg-gray-100 text-gray-500 border-gray-200",
    badgeErr:    "bg-red-50 text-red-600 border-red-200",
    iconBg:      "bg-gray-200",
    sendBtn:     "bg-gray-200 text-gray-600 hover:bg-gray-300",
    stopBtn:     "bg-red-100 text-red-500 hover:bg-red-200",
    suggestBtn:  "bg-white border-gray-200 hover:border-gray-300 text-gray-600 hover:text-gray-800",
    dot:         "bg-gray-400",
    prose:       "[&_p]:text-gray-700 [&_p]:leading-relaxed [&_p]:my-2 " +
                 "[&_h1]:text-gray-900 [&_h1]:font-semibold [&_h1]:text-base [&_h1]:mt-4 [&_h1]:mb-1 " +
                 "[&_h2]:text-gray-900 [&_h2]:font-semibold [&_h2]:text-sm [&_h2]:mt-4 [&_h2]:mb-1 " +
                 "[&_h3]:text-gray-800 [&_h3]:font-semibold [&_h3]:text-sm [&_h3]:mt-3 [&_h3]:mb-1 " +
                 "[&_li]:text-gray-700 [&_li]:leading-relaxed " +
                 "[&_strong]:text-gray-900 [&_strong]:font-semibold " +
                 "[&_ul]:list-disc [&_ul]:list-outside [&_ul]:ml-5 [&_ul]:my-2 [&_ul]:space-y-1 " +
                 "[&_ol]:list-decimal [&_ol]:list-outside [&_ol]:ml-5 [&_ol]:my-2 [&_ol]:space-y-1 " +
                 "[&_hr]:border-gray-200 [&_hr]:my-3 " +
                 "[&_blockquote]:border-l-4 [&_blockquote]:border-gray-300 [&_blockquote]:pl-4 [&_blockquote]:text-gray-500",
    tableHeader: "bg-gray-100 border-gray-200 text-gray-700",
    tableCell:   "border-gray-200 text-gray-600",
    codePre:     "bg-gray-900 text-green-400 border-gray-700",
    codeInline:  "bg-gray-100 text-red-600 border-gray-200",
    placeholder: "placeholder-gray-400",
    inputText:   "text-gray-800",
  },
};

// ─── Source Card ───────────────────────────────────────────────────────────────

function SourceCard({ citation, index }: { citation: Citation; index: number }) {
  const dark = useDark();
  const t = dark ? T.dark : T.light;
  const fileName = citation.path ? citation.path.split("/").pop() : null;
  return (
    <div className={`relative mb-3 p-3 rounded-lg border transition-colors group ${t.card}`}>
      {/* Hover tooltip — filename */}
      {fileName && (
        <div className={`absolute bottom-full left-2 mb-1.5 px-2 py-1 text-[10px] font-mono rounded whitespace-nowrap
          opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity duration-150 z-20
          ${dark ? "bg-gray-900 text-gray-300 border border-[#2a2a2a]" : "bg-gray-800 text-gray-100"}`}>
          {fileName}
          <div className={`absolute top-full left-3 border-4 border-transparent
            ${dark ? "border-t-gray-900" : "border-t-gray-800"}`} />
        </div>
      )}
      <div className="flex items-start gap-2">
        <div className={`w-5 h-5 rounded-full flex items-center justify-center shrink-0 text-[10px] font-mono mt-0.5 ${t.iconBg} ${t.text4}`}>
          {index + 1}
        </div>
        <div className="min-w-0">
          <div className={`text-xs font-medium leading-snug mb-0.5 line-clamp-2 ${t.text2}`}>
            {citation.title}
          </div>
          <div className={`text-[10px] uppercase tracking-wide mb-1 ${t.label}`}>
            {citation.doc_type_label}
          </div>
          {citation.excerpt && (
            <div className={`text-xs leading-relaxed line-clamp-3 ${t.text4}`}>
              {citation.excerpt}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ─── Sources Sidebar ───────────────────────────────────────────────────────────

function SourcesSidebar({ citations }: { citations: Citation[] }) {
  const dark = useDark();
  const t = dark ? T.dark : T.light;
  return (
    <div className={`w-64 shrink-0 border-l overflow-y-auto ${t.sidebar}`}>
      <div className={`px-4 py-3 border-b sticky top-0 ${t.sidebar} ${t.divider2}`}>
        <h3 className={`text-xs font-semibold uppercase tracking-wider ${t.text4}`}>
          Sources · {citations.length}
        </h3>
      </div>
      <div className="px-3 py-3">
        {citations.map((c, i) => (
          <SourceCard key={c.id} citation={c} index={i} />
        ))}
      </div>
    </div>
  );
}

// ─── Tool Pills ────────────────────────────────────────────────────────────────

function ToolPills({ traces }: { traces: ToolTrace[] }) {
  const dark = useDark();
  const t = dark ? T.dark : T.light;
  if (traces.length === 0) return null;
  return (
    <div className="flex flex-wrap gap-1.5 mb-3">
      {traces.map((ti, i) => (
        <span key={i} className={`text-xs px-2 py-0.5 rounded-full font-mono border ${ti.had_error ? t.badgeErr : t.badge}`}>
          {ti.tool}
          {ti.latency_ms !== undefined && (
            <span className={`ml-1 ${t.text5}`}>{ti.latency_ms}ms</span>
          )}
        </span>
      ))}
    </div>
  );
}

// ─── Action Bar ────────────────────────────────────────────────────────────────

function ActionBar({
  message,
  onReformat,
  onToggleView,
}: {
  message: ChatMessage;
  onReformat: (id: string, targetMode: ResponseMode) => void;
  onToggleView: (id: string) => void;
}) {
  const dark = useDark();
  const t = dark ? T.dark : T.light;
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    const text =
      message.activeView === "reformatted" && message.reformattedContent
        ? message.reformattedContent
        : message.content;
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  const currentMode =
    message.activeView === "reformatted" && message.reformattedMode
      ? message.reformattedMode
      : (message.responseMode ?? "detailed");
  const hasReformatted = !!message.reformattedContent;
  const targetMode: ResponseMode = currentMode === "detailed" ? "summarized" : "detailed";

  return (
    <div className={`flex items-center gap-4 mt-4 pt-3 border-t ${t.divider2}`}>
      <button onClick={handleCopy} className={`flex items-center gap-1.5 text-xs transition-colors ${t.text4} hover:${t.text3}`}>
        <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
        </svg>
        {copied ? "Copied" : "Copy"}
      </button>

      {hasReformatted ? (
        <button onClick={() => onToggleView(message.id)} className={`text-xs transition-colors ${t.text4}`}>
          {message.activeView === "reformatted" ? "Show original" : `Show ${message.reformattedMode}`}
        </button>
      ) : (
        <button
          onClick={() => onReformat(message.id, targetMode)}
          disabled={message.isReformatting}
          className={`flex items-center gap-1.5 text-xs transition-colors disabled:opacity-40 ${t.text4}`}
        >
          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h10M4 18h7" />
          </svg>
          {message.isReformatting ? "Reformatting…" : currentMode === "detailed" ? "Summarize" : "Expand"}
        </button>
      )}

      <div className={`ml-auto flex items-center gap-3 text-xs ${t.text5}`}>
        {(message.citations?.length ?? 0) > 0 && <span>{message.citations!.length} sources</span>}
        {message.usage?.cost_usd && message.usage.cost_usd > 0 && (
          <span className="font-mono">${message.usage.cost_usd.toFixed(4)}</span>
        )}
        {message.usage?.total_latency_ms && message.usage.total_latency_ms > 0 && (
          <span>{message.usage.total_latency_ms}ms</span>
        )}
      </div>
    </div>
  );
}

// ─── Follow-ups ────────────────────────────────────────────────────────────────

function FollowUps({
  suggestions,
  loading,
  onSelect,
}: {
  suggestions?: string[];
  loading?: boolean;
  onSelect: (q: string) => void;
}) {
  const dark = useDark();
  const t = dark ? T.dark : T.light;

  if (loading) {
    return (
      <div className={`mt-6 pt-4 border-t ${t.divider2}`}>
        <div className={`text-xs mb-3 font-medium ${t.text4}`}>Follow-ups</div>
        <div className="space-y-2">
          {[1, 2, 3].map((i) => (
            <div key={i} className={`h-5 rounded animate-pulse ${t.iconBg}`} style={{ width: `${60 + i * 10}%` }} />
          ))}
        </div>
      </div>
    );
  }

  const items = suggestions && suggestions.length > 0 ? suggestions : [];
  if (items.length === 0) return null;

  return (
    <div className={`mt-6 pt-4 border-t ${t.divider2}`}>
      <div className={`text-xs mb-3 font-medium ${t.text4}`}>Follow-ups</div>
      <div className="space-y-2">
        {items.map((s) => (
          <button
            key={s}
            onClick={() => onSelect(s)}
            className={`flex items-center gap-2 w-full text-left text-sm transition-colors group ${t.text3}`}
          >
            <span className={`shrink-0 ${t.text5}`}>↳</span>
            <span>{s}</span>
          </button>
        ))}
      </div>
    </div>
  );
}

// ─── Message Block ─────────────────────────────────────────────────────────────

function MessageBlock({
  message,
  isLast,
  showDebug,
  onReformat,
  onToggleView,
  onFollowUp,
}: {
  message: ChatMessage;
  isLast: boolean;
  showDebug: boolean;
  onReformat: (id: string, targetMode: ResponseMode) => void;
  onToggleView: (id: string) => void;
  onFollowUp: (q: string) => void;
}) {
  const dark = useDark();
  const t = dark ? T.dark : T.light;
  const isUser = message.role === "user";

  if (isUser) {
    return (
      <div className="py-5">
        <div className={`text-[10px] mb-1.5 uppercase tracking-widest font-semibold ${t.label}`}>You</div>
        <div className={`text-base font-medium ${t.text1}`}>{message.content}</div>
      </div>
    );
  }

  const displayContent =
    message.activeView === "reformatted" && message.reformattedContent
      ? message.reformattedContent
      : message.content || "...";

  return (
    <div className={`py-5 border-t ${t.divider}`}>
      <div className="flex items-center gap-2 mb-3">
        <div className={`w-5 h-5 rounded-full flex items-center justify-center shrink-0 ${t.iconBg}`}>
          <span className={`text-[9px] font-bold ${t.text4}`}>PE</span>
        </div>
        <span className={`text-[10px] uppercase tracking-widest font-semibold ${t.label}`}>
          PrimeEV Agent
        </span>
        {message.agent && message.agent !== "root_agent" && (
          <span className={`text-[10px] ${t.text5}`}>· {message.agent}</span>
        )}
      </div>

      {showDebug && message.toolTrace && message.toolTrace.length > 0 && (
        <ToolPills traces={message.toolTrace} />
      )}

      <div className={`prose prose-sm max-w-none ${t.prose}`}>
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={{
            table: ({ children }) => (
              <div className="overflow-x-auto my-3">
                <table className="min-w-full border-collapse text-xs">{children}</table>
              </div>
            ),
            th: ({ children }) => (
              <th className={`border px-3 py-1.5 text-left font-semibold ${t.tableHeader}`}>{children}</th>
            ),
            td: ({ children }) => (
              <td className={`border px-3 py-1.5 ${t.tableCell}`}>{children}</td>
            ),
            pre: ({ children }) => <>{children}</>,
            code: ({ children, className }) =>
              className ? (
                <pre className={`rounded-lg p-4 my-3 overflow-x-auto text-xs border ${t.codePre}`}>
                  <code>{children}</code>
                </pre>
              ) : (
                <code className={`px-1.5 py-0.5 rounded text-xs font-mono border ${t.codeInline}`}>{children}</code>
              ),
          }}
        >
          {displayContent}
        </ReactMarkdown>
      </div>

      {message.content && message.content !== "..." && (
        <ActionBar message={message} onReformat={onReformat} onToggleView={onToggleView} />
      )}

      {isLast && message.content && message.content !== "..." && (
        <FollowUps
          suggestions={message.followUps}
          loading={message.isLoadingFollowUps}
          onSelect={onFollowUp}
        />
      )}
    </div>
  );
}

// ─── Sessions Panel ───────────────────────────────────────────────────────────

function SessionsPanel({
  currentSessionId,
  onSelect,
  onNew,
}: {
  currentSessionId: string | null;
  onSelect: (id: string) => void;
  onNew: () => void;
}) {
  const dark = useDark();
  const t = dark ? T.dark : T.light;
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    listSessions()
      .then(setSessions)
      .finally(() => setLoading(false));
  }, [currentSessionId]);

  function fmt(iso: string) {
    const d = new Date(iso);
    const now = new Date();
    const diffMs = now.getTime() - d.getTime();
    const diffMin = Math.floor(diffMs / 60000);
    if (diffMin < 1) return "just now";
    if (diffMin < 60) return `${diffMin}m ago`;
    const diffH = Math.floor(diffMin / 60);
    if (diffH < 24) return `${diffH}h ago`;
    return d.toLocaleDateString(undefined, { month: "short", day: "numeric" });
  }

  return (
    <div className={`w-52 shrink-0 flex flex-col border-r overflow-hidden ${t.sidebar} ${t.divider2}`}>
      <div className={`px-3 py-2.5 border-b sticky top-0 shrink-0 ${t.sidebar} ${t.divider2}`}>
        <button
          onClick={onNew}
          className={`w-full text-left text-xs font-semibold px-2.5 py-1.5 rounded border transition-colors ${t.btn}`}
        >
          + New Chat
        </button>
      </div>
      <div className="flex-1 overflow-y-auto py-1">
        {loading ? (
          <div className="space-y-1.5 px-2 py-2">
            {[1, 2, 3].map((i) => (
              <div key={i} className={`h-10 rounded animate-pulse ${t.iconBg}`} />
            ))}
          </div>
        ) : sessions.length === 0 ? (
          <p className={`text-xs text-center py-6 ${t.text4}`}>No sessions yet</p>
        ) : (
          sessions.map((s) => {
            const isActive = s.session_id === currentSessionId;
            return (
              <button
                key={s.session_id}
                onClick={() => onSelect(s.session_id)}
                className={`w-full text-left px-3 py-2 transition-colors ${isActive ? t.btnActive : `hover:${t.card}`}`}
              >
                <div className={`text-xs font-mono truncate mb-0.5 ${isActive ? "" : t.text3}`}>
                  {s.session_id.slice(0, 8)}…
                </div>
                <div className={`flex items-center justify-between text-[10px] ${t.text4}`}>
                  <span>{s.message_count} msg{s.message_count !== 1 ? "s" : ""}</span>
                  <span>{fmt(s.created_at)}</span>
                </div>
              </button>
            );
          })
        )}
      </div>
    </div>
  );
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function ChatPage() {
  const { messages, isStreaming, sessionId, sendMessage, stopStreaming, clearChat, loadSession, updateMessage } = useChat();
  const [input, setInput] = useState("");
  const [showDebug, setShowDebug] = useState(false);
  const [showSessions, setShowSessions] = useState(false);
  const [isDark, setIsDark] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const t = isDark ? T.dark : T.light;

  const handleLoadSession = useCallback(async (id: string) => {
    if (id === sessionId) return;
    await loadSession(id);
  }, [loadSession, sessionId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleReformat = async (id: string, targetMode: ResponseMode) => {
    const msg = messages.find((m) => m.id === id);
    if (!msg) return;
    updateMessage(id, { isReformatting: true });
    try {
      const text = await reformatMessage(msg.content, targetMode);
      updateMessage(id, { isReformatting: false, reformattedContent: text, reformattedMode: targetMode, activeView: "reformatted" });
    } catch {
      updateMessage(id, { isReformatting: false });
    }
  };

  const handleToggleView = (id: string) => {
    const msg = messages.find((m) => m.id === id);
    if (!msg) return;
    updateMessage(id, { activeView: msg.activeView === "reformatted" ? "original" : "reformatted" });
  };

  const handleSend = (text: string) => {
    if (!text.trim() || isStreaming) return;
    sendMessage(text.trim());
    setInput("");
  };

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    handleSend(input);
  };

  const latestCitations =
    [...messages].reverse().find((m) => m.role === "assistant" && (m.citations?.length ?? 0) > 0)?.citations ?? [];

  const sessionCost = messages
    .filter((m) => m.role === "assistant" && m.usage)
    .reduce((sum, m) => sum + (m.usage?.cost_usd ?? 0), 0);

  const lastAssistantIdx = messages.reduce((last, m, i) => (m.role === "assistant" ? i : last), -1);

  return (
    <DarkCtx.Provider value={isDark}>
      <div className={`flex flex-col h-[calc(100vh-8rem)] rounded-xl overflow-hidden border ${t.root}`}>

        {/* Header */}
        <div className={`flex items-center justify-between px-5 py-2.5 border-b shrink-0 ${t.header}`}>
          <div className="flex items-center gap-3">
            <span className={`text-sm font-semibold ${t.text2}`}>Factory Floor Agent</span>
            {sessionCost > 0 && (
              <span className={`text-xs font-mono ${t.text5}`}>${sessionCost.toFixed(4)}</span>
            )}
          </div>
          <div className="flex items-center gap-2">
            {/* Sessions toggle */}
            <button
              onClick={() => setShowSessions((v) => !v)}
              className={`text-xs px-2.5 py-1 rounded border transition-colors ${showSessions ? t.btnActive : t.btn}`}
              title="Previous sessions"
            >
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </button>

            {/* Dark/Light toggle */}
            <button
              onClick={() => setIsDark((v) => !v)}
              className={`text-xs px-2.5 py-1 rounded border transition-colors ${t.btn}`}
              title={isDark ? "Switch to light mode" : "Switch to dark mode"}
            >
              {isDark ? (
                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364-6.364l-.707.707M6.343 17.657l-.707.707M17.657 17.657l-.707-.707M6.343 6.343l-.707-.707M12 8a4 4 0 100 8 4 4 0 000-8z" />
                </svg>
              ) : (
                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
                </svg>
              )}
            </button>

            <button
              onClick={() => setShowDebug((v) => !v)}
              className={`text-xs px-2.5 py-1 rounded border transition-colors ${showDebug ? t.btnActive : t.btn}`}
            >
              Debug
            </button>
            <button
              onClick={clearChat}
              className={`text-xs px-2.5 py-1 rounded border transition-colors ${t.btn}`}
            >
              New Chat
            </button>
          </div>
        </div>

        {/* Body */}
        <div className={`flex flex-1 overflow-hidden ${t.body}`}>
          {/* Sessions sidebar */}
          {showSessions && (
            <SessionsPanel
              currentSessionId={sessionId}
              onSelect={handleLoadSession}
              onNew={clearChat}
            />
          )}

          {/* Messages */}
          <div className="flex-1 overflow-y-auto px-8 py-2">
            {messages.length === 0 && (
              <div className="flex flex-col items-center justify-center h-full pb-10">
                <div className={`text-4xl font-bold mb-3 ${t.text5}`}>PE</div>
                <h3 className={`text-lg font-semibold mb-1 ${t.text3}`}>PrimeEV Factory Floor Agent</h3>
                <p className={`text-sm mb-8 text-center max-w-sm ${t.text4}`}>
                  Ask about equipment failures, quality trends, production OEE, or continuous improvement.
                </p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2 w-full max-w-lg">
                  {[
                    "STP-01-PRS-HYP01 had a critical overstrain failure on Jun 25 — what caused it and what should we do next?",
                    "Weld current Cpk at WLD-01-UBD is trending toward 1.3 and close to the warning threshold — is this a process control concern?",
                    "Press 1 hydraulic oil temperature is reading 72°C right now. Is this a problem? What does the sensor show in the last 2 hours and what does the SOP say?",
                    "Which machines across all Stamping stations are at highest risk of failure in the next 48 hours based on current degradation state?",
                  ].map((q) => (
                    <button
                      key={q}
                      onClick={() => handleSend(q)}
                      className={`text-left text-sm px-4 py-2.5 border rounded-lg transition-colors ${t.suggestBtn}`}
                    >
                      {q}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {messages.map((msg, idx) => (
              <MessageBlock
                key={msg.id}
                message={msg}
                isLast={idx === lastAssistantIdx && !isStreaming}
                showDebug={showDebug}
                onReformat={handleReformat}
                onToggleView={handleToggleView}
                onFollowUp={handleSend}
              />
            ))}

            {isStreaming && (
              <div className="flex items-center gap-1.5 py-4">
                {[0, 150, 300].map((d) => (
                  <span
                    key={d}
                    className={`w-1.5 h-1.5 rounded-full animate-bounce ${t.dot}`}
                    style={{ animationDelay: `${d}ms` }}
                  />
                ))}
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Sources sidebar */}
          {latestCitations.length > 0 && <SourcesSidebar citations={latestCitations} />}
        </div>

        {/* Input */}
        <form onSubmit={handleSubmit} className={`shrink-0 px-5 py-3 border-t ${t.divider2} ${t.header}`}>
          <div className={`flex items-center gap-2 border rounded-xl px-4 py-2.5 transition-colors ${t.input}`}>
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask a follow-up..."
              className={`flex-1 bg-transparent text-sm focus:outline-none ${t.inputText} ${t.placeholder}`}
              disabled={isStreaming}
            />
            {isStreaming ? (
              <button
                type="button"
                onClick={stopStreaming}
                className={`w-7 h-7 flex items-center justify-center rounded-lg transition-colors ${t.stopBtn}`}
              >
                <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 24 24">
                  <rect x="6" y="6" width="12" height="12" rx="1" />
                </svg>
              </button>
            ) : (
              <button
                type="submit"
                disabled={!input.trim()}
                className={`w-7 h-7 flex items-center justify-center rounded-lg transition-colors disabled:opacity-30 disabled:cursor-not-allowed ${t.sendBtn}`}
              >
                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M5 12h14M12 5l7 7-7 7" />
                </svg>
              </button>
            )}
          </div>
        </form>

      </div>
    </DarkCtx.Provider>
  );
}
