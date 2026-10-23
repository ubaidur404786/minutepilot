// Calls to the Python service (it forwards chat messages to n8n).

async function json(res) {
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || `error ${res.status}`);
  return data;
}

const send = (method, url, body) =>
  fetch(url, {
    method,
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  }).then(json);

export const api = {
  sessions: () => fetch("/api/sessions").then(json),
  messages: (id) => fetch(`/api/sessions/${id}/messages`).then(json),
  rename: (id, title) => send("PATCH", `/api/sessions/${id}`, { title }),
  clear: (id) => send("POST", `/api/sessions/${id}/clear`),
  remove: (id) => send("DELETE", `/api/sessions/${id}`),
  status: () => fetch("/api/status").then(json),
  chat: (sessionId, message, files) => send("POST", "/api/chat", { sessionId, message, files }),
  upload: (sessionId, file) => {
    const form = new FormData();
    form.append("session_id", sessionId);
    form.append("file", file);
    return fetch("/api/upload", { method: "POST", body: form }).then(json);
  },
};

// Live steps of one chat (Server-Sent Events). Returns a function that closes the stream.
export function listenToSteps(sessionId, onStep) {
  const source = new EventSource(`/api/events/${sessionId}`);
  source.onmessage = (e) => onStep(JSON.parse(e.data));
  return () => source.close();
}

export function newSessionId() {
  const raw = crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}${Math.random()}`;
  return raw.replace(/[^A-Za-z0-9]/g, "").slice(0, 32);
}
