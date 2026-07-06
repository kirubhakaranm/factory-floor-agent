// SSE chat client for streaming agent responses

export interface ChatStreamCallbacks {
  onToken: (text: string, agent?: string) => void;
  onToolCall: (tool: string, args: Record<string, unknown>, agent?: string) => void;
  onToolResult: (tool: string, agent?: string) => void;
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

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (line.startsWith("event: ")) {
            continue;
          }
          if (line.startsWith("data: ")) {
            const raw = line.slice(6);
            try {
              const data = JSON.parse(raw);

              if (data.text !== undefined) {
                callbacks.onToken(data.text, data.agent);
              } else if (data.tool !== undefined && data.args !== undefined) {
                callbacks.onToolCall(data.tool, data.args, data.agent);
              } else if (data.tool !== undefined && data.args === undefined) {
                callbacks.onToolResult(data.tool, data.agent);
              } else if (data.session_id !== undefined && data.response_length !== undefined) {
                callbacks.onDone(data.session_id);
              } else if (data.session_id !== undefined) {
                callbacks.onSession(data.session_id);
              }
            } catch {
              // Skip non-JSON lines
            }
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
