export interface SessionSummary {
  session_id: string;
  created_at: string;
  message_count: number;
}

export interface SessionMessage {
  role: "user" | "assistant";
  content: string;
  timestamp: string;
}

export interface SessionDetail {
  session_id: string;
  created_at: string;
  messages: SessionMessage[];
}

export async function listSessions(): Promise<SessionSummary[]> {
  const res = await fetch("/api/sessions");
  if (!res.ok) return [];
  return res.json();
}

export async function getSession(sessionId: string): Promise<SessionDetail | null> {
  const res = await fetch(`/api/sessions/${sessionId}`);
  if (!res.ok) return null;
  const data = await res.json();
  if (data.error) return null;
  return data as SessionDetail;
}
