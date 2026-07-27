import { useCallback, useRef, useState } from "react";
import { streamChat, fetchFollowUps } from "../api/chat";
import type { ChatMessage, Citation, ToolCall, ToolTrace, UsageInfo } from "../types";

export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const cancelRef = useRef<(() => void) | null>(null);

  const sendMessage = useCallback(
    (text: string) => {
      const userMsg: ChatMessage = {
        id: crypto.randomUUID(),
        role: "user",
        content: text,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, userMsg]);
      setIsStreaming(true);

      const assistantId = crypto.randomUUID();
      const toolCalls: ToolCall[] = [];
      const toolTrace: ToolTrace[] = [];
      const citations: Citation[] = [];
      let currentAgent = "";
      let accumulatedContent = "";

      setMessages((prev) => [
        ...prev,
        {
          id: assistantId,
          role: "assistant",
          content: "",
          toolCalls: [],
          toolTrace: [],
          citations: [],
          timestamp: new Date(),
        },
      ]);

      const cancel = streamChat(text, sessionId, {
        onToken: (token, agent) => {
          if (agent) currentAgent = agent;
          accumulatedContent += token;
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId
                ? { ...m, content: m.content + token, agent: currentAgent }
                : m
            )
          );
        },
        onToolCall: (tool, args, agent) => {
          toolCalls.push({ tool, args, agent });
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId ? { ...m, toolCalls: [...toolCalls] } : m
            )
          );
        },
        onToolResult: (event) => {
          // Merge result data into the matching toolTrace entry or create new
          const existing = toolTrace.find((t) => t.tool === event.tool && t.result_snippet === undefined);
          if (existing) {
            existing.result_snippet = event.result_snippet;
            existing.latency_ms = event.latency_ms;
            existing.had_error = event.had_error;
          } else {
            toolTrace.push({
              tool: event.tool,
              args: {},
              agent: event.agent,
              result_snippet: event.result_snippet,
              latency_ms: event.latency_ms,
              had_error: event.had_error,
            });
          }
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId ? { ...m, toolTrace: [...toolTrace] } : m
            )
          );
        },
        onUsage: (usage: UsageInfo) => {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId ? { ...m, usage } : m
            )
          );
        },
        onCitation: (citation) => {
          citations.push(citation);
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId ? { ...m, citations: [...citations] } : m
            )
          );
        },
        onSession: (sid) => setSessionId(sid),
        onDone: () => {
          setIsStreaming(false);
          // accumulatedContent and assistantId are local variables in sendMessage's closure —
          // no need to read from React state, so the fetch starts immediately.
          if (!accumulatedContent) return;
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId ? { ...m, isLoadingFollowUps: true } : m
            )
          );
          fetchFollowUps(accumulatedContent).then((suggestions) => {
            setMessages((curr) =>
              curr.map((m) =>
                m.id === assistantId
                  ? { ...m, followUps: suggestions, isLoadingFollowUps: false }
                  : m
              )
            );
          }).catch(() => {
            setMessages((curr) =>
              curr.map((m) =>
                m.id === assistantId ? { ...m, isLoadingFollowUps: false } : m
              )
            );
          });
        },
        onError: (err) => {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId
                ? { ...m, content: m.content || `Error: ${err}` }
                : m
            )
          );
          setIsStreaming(false);
        },
      });

      cancelRef.current = cancel;
    },
    [sessionId]
  );

  const stopStreaming = useCallback(() => {
    cancelRef.current?.();
    setIsStreaming(false);
  }, []);

  const clearChat = useCallback(() => {
    setMessages([]);
    setSessionId(null);
  }, []);

  const loadSession = useCallback(async (targetSessionId: string) => {
    const { getSession } = await import("../api/sessions");
    const detail = await getSession(targetSessionId);
    if (!detail) return;
    const restored: ChatMessage[] = detail.messages.map((m) => ({
      id: crypto.randomUUID(),
      role: m.role as "user" | "assistant",
      content: m.content,
      timestamp: new Date(m.timestamp),
      toolCalls: [],
      toolTrace: [],
      citations: [],
    }));
    setMessages(restored);
    setSessionId(targetSessionId);
  }, []);

  const updateMessage = useCallback((id: string, patch: Partial<ChatMessage>) => {
    setMessages((prev) =>
      prev.map((m) => (m.id === id ? { ...m, ...patch } : m))
    );
  }, []);

  return { messages, isStreaming, sessionId, sendMessage, stopStreaming, clearChat, loadSession, updateMessage };
}
