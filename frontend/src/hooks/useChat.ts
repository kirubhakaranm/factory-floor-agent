import { useCallback, useRef, useState } from "react";
import { streamChat } from "../api/chat";
import type { ChatMessage, ToolCall } from "../types";

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
      let currentAgent = "";

      setMessages((prev) => [
        ...prev,
        { id: assistantId, role: "assistant", content: "", toolCalls: [], timestamp: new Date() },
      ]);

      const cancel = streamChat(text, sessionId, {
        onToken: (token, agent) => {
          if (agent) currentAgent = agent;
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
        onToolResult: () => {},
        onSession: (sid) => setSessionId(sid),
        onDone: () => setIsStreaming(false),
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

  return { messages, isStreaming, sessionId, sendMessage, stopStreaming, clearChat };
}
