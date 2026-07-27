// SSE chat client for streaming agent responses

import type { Citation, ResponseMode, UsageInfo } from "../types";

export interface ToolResultEvent {
  tool: string;
  agent?: string;
  result_snippet?: string;
  latency_ms?: number;
  had_error?: boolean;
}

export interface ChatStreamCallbacks {
  onToken: (text: string, agent?: string) => void;
  onToolCall: (tool: string, args: Record<string, unknown>, agent?: string) => void;
  onToolResult: (event: ToolResultEvent) => void;
  onUsage: (usage: UsageInfo) => void;
  onCitation: (citation: Citation) => void;
  onDone: (sessionId: string) => void;
  onError: (error: string) => void;
  onSession: (sessionId: string) => void;
}

export function streamChat(
  message: string,
  sessionId: string | null,
  callbacks: ChatStreamCallbacks
): () => void {
  const controller = new AbortController();

  (async () => {
    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message, session_id: sessionId }),
        signal: controller.signal,
      });

      if (!res.ok) {
        callbacks.onError(`API error: ${res.status}`);
        return;
      }

      const reader = res.body?.getReader();
      if (!reader) {
        callbacks.onError("No response body");
        return;
      }

      const decoder = new TextDecoder();
      let buffer = "";
      let currentEvent = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (line === "") {
            currentEvent = "";
            continue;
          }
          if (line.startsWith("event: ")) {
            currentEvent = line.slice(7).trim();
            continue;
          }
          if (line.startsWith("data: ")) {
            const raw = line.slice(6);
            try {
              const data = JSON.parse(raw);
              switch (currentEvent) {
                case "token":
                  callbacks.onToken(data.text, data.agent);
                  break;
                case "tool_call":
                  callbacks.onToolCall(data.tool, data.args, data.agent);
                  break;
                case "tool_result":
                  callbacks.onToolResult(data as ToolResultEvent);
                  break;
                case "usage":
                  callbacks.onUsage(data as UsageInfo);
                  break;
                case "citation":
                  callbacks.onCitation(data as Citation);
                  break;
                case "done":
                  callbacks.onDone(data.session_id);
                  break;
                case "session":
                  callbacks.onSession(data.session_id);
                  break;
              }
            } catch {
              // Skip non-JSON lines
            }
            currentEvent = "";
          }
        }
      }
    } catch (err) {
      if (!controller.signal.aborted) {
        callbacks.onError(String(err));
      }
    }
  })();

  return () => controller.abort();
}

export async function fetchFollowUps(responseText: string): Promise<string[]> {
  const res = await fetch("/api/chat/follow-ups", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ response_text: responseText }),
  });
  if (!res.ok) return [];
  const data = await res.json();
  return data.suggestions as string[];
}

export async function reformatMessage(
  originalText: string,
  targetMode: ResponseMode
): Promise<string> {
  const res = await fetch("/api/chat/reformat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ original_text: originalText, target_mode: targetMode }),
  });
  if (!res.ok) throw new Error(`Reformat failed: ${res.status}`);
  const data = await res.json();
  return data.text as string;
}
