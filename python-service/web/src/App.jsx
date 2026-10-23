import { useCallback, useEffect, useRef, useState } from "react";
import { api, listenToSteps, newSessionId } from "./api.js";
import Sidebar from "./components/Sidebar.jsx";
import Header from "./components/Header.jsx";
import Message from "./components/Message.jsx";
import Composer from "./components/Composer.jsx";
import Welcome from "./components/Welcome.jsx";
import ConfirmDialog from "./components/ConfirmDialog.jsx";
import { fileKind } from "./util.js";

const SESSION_KEY = "mp-session";
const THEME_KEY = "mp-theme";

function remember(key, value) {
  try { localStorage.setItem(key, value); } catch { /* private window: not remembered */ }
}
function recall(key) {
  try { return localStorage.getItem(key); } catch { return null; }
}

export default function App() {
  const [sessions, setSessions] = useState([]);
  const [activeId, setActiveId] = useState(() => recall(SESSION_KEY) || newSessionId());
  const [messages, setMessages] = useState([]);
  const [draftState, setDraftState] = useState(null); // status of the chat's current draft
  const [busyId, setBusyId] = useState(null); // chat waiting for an answer
  const [live, setLive] = useState(null); // { sessionId, turnStart, events } of the running turn
  const [sidebarOpen, setSidebarOpen] = useState(() => window.innerWidth > 900);
  const [status, setStatus] = useState(null);
  const [theme, setTheme] = useState(() => recall(THEME_KEY) ||
    (window.matchMedia?.("(prefers-color-scheme: dark)").matches ? "dark" : "light"));
  const [confirm, setConfirm] = useState(null);
  const [error, setError] = useState("");
  const composer = useRef(null);
  const scroller = useRef(null);
  const liveRef = useRef(null);
  liveRef.current = live;
  const activeIdRef = useRef(activeId);
  activeIdRef.current = activeId;

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    remember(THEME_KEY, theme);
  }, [theme]);

  const loadSessions = useCallback(() => api.sessions().then(setSessions).catch(() => {}), []);

  const loadChat = useCallback(async (id) => {
    try {
      const chat = await api.messages(id);
      setMessages(chat.messages);
      setDraftState(chat.draft);
    } catch (err) {
      setError(`Could not open the chat: ${err.message}`);
    }
  }, []);

  // first load, and service status every 30 s
  useEffect(() => {
    loadSessions();
    const check = () => api.status().then(setStatus).catch(() => setStatus({ offline: true }));
    check();
    const timer = setInterval(check, 30000);
    return () => clearInterval(timer);
  }, [loadSessions]);

  // open the active chat and listen to its live steps
  useEffect(() => {
    remember(SESSION_KEY, activeId);
    if (busyId !== activeId) loadChat(activeId);
    return listenToSteps(activeId, (step) => {
      const turn = liveRef.current;
      if (!turn || turn.sessionId !== activeId || step.at < turn.turnStart) return;
      setLive((t) => (t && t.sessionId === activeId ? { ...t, events: [...t.events, step] } : t));
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeId, loadChat]);

  // keep the newest message in view
  useEffect(() => {
    const el = scroller.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages, live?.events.length]);

  async function send(text, files = []) {
    text = (text || "").trim();
    if ((!text && !files.length) || busyId) return;
    const sid = activeId;
    setError("");
    setBusyId(sid);
    setLive({ sessionId: sid, turnStart: Date.now() / 1000 - 2, events: [] });
    setMessages((m) => [
      ...m,
      { id: "pending-user", role: "user", text, files: files.map((f) => ({ name: f.name, kind: fileKind(f) })), at: Date.now() / 1000 },
      { id: "pending-answer", role: "assistant", pending: true, at: Date.now() / 1000 },
    ]);
    try {
      const uploaded = [];
      for (const f of files) uploaded.push(await api.upload(sid, f));
      await api.chat(sid, text, uploaded);
    } catch (err) {
      // the server saves failed answers too; this covers a failed upload
      setError(err.message);
    } finally {
      setBusyId(null);
      setLive(null);
      if (sid === activeIdRef.current) await loadChat(sid);
      loadSessions();
    }
  }

  function newChat() {
    setActiveId(newSessionId());
    setMessages([]);
    setDraftState(null);
    setError("");
    if (window.innerWidth <= 900) setSidebarOpen(false);
  }

  function openChat(id) {
    if (id === activeId) return;
    setMessages([]);
    setActiveId(id);
    setError("");
    if (window.innerWidth <= 900) setSidebarOpen(false);
  }

  function askClear(id) {
    setConfirm({
      title: "Clear this chat?",
      text: "Messages, meeting notes and the draft are removed. The agent also forgets this chat. Emails, tasks and events already sent stay in Google.",
      action: "Clear chat",
      run: async () => {
        await api.clear(id);
        if (id === activeId) await loadChat(id);
        loadSessions();
      },
    });
  }

  function askDelete(id) {
    setConfirm({
      title: "Delete this chat?",
      text: "The chat, its notes and its uploaded files are deleted for good. Emails, tasks and events already sent stay in Google.",
      action: "Delete",
      danger: true,
      run: async () => {
        await api.remove(id).catch(() => {}); // a chat that was never sent has nothing to delete
        if (id === activeId) newChat();
        loadSessions();
      },
    });
  }

  async function rename(id, title) {
    await api.rename(id, title);
    loadSessions();
  }

  const active = sessions.find((s) => s.session_id === activeId);
  const busy = busyId === activeId;

  return (
    <div className={`app ${sidebarOpen ? "with-sidebar" : ""}`}>
      <Sidebar
        open={sidebarOpen}
        sessions={sessions}
        activeId={activeId}
        busyId={busyId}
        onNew={newChat}
        onOpen={openChat}
        onClear={askClear}
        onDelete={askDelete}
        onRename={rename}
        onClose={() => setSidebarOpen(false)}
      />
      <main className="main">
        <Header
          title={active?.title || (messages.length ? "New chat" : "MinutePilot")}
          sidebarOpen={sidebarOpen}
          onToggleSidebar={() => setSidebarOpen((o) => !o)}
          onNew={newChat}
          onClear={messages.length ? () => askClear(activeId) : null}
          status={status}
          theme={theme}
          onTheme={() => setTheme((t) => (t === "dark" ? "light" : "dark"))}
        />
        <div
          className="chat-scroll"
          ref={scroller}
          onDragOver={(e) => e.preventDefault()}
          onDrop={(e) => {
            e.preventDefault();
            composer.current?.addFiles(e.dataTransfer.files);
          }}
        >
          <div className="chat-column">
            {messages.length === 0 ? (
              <Welcome
                onSend={(t) => send(t)}
                onPrefill={(t) => composer.current?.prefill(t)}
                onAttach={() => composer.current?.openPicker()}
              />
            ) : (
              messages.map((m) => (
                <Message
                  key={m.id}
                  message={m}
                  liveEvents={m.pending ? live?.events || [] : null}
                  draftState={draftState}
                  busy={!!busyId}
                  onApprove={() => send("Approve")}
                  onChange={() => composer.current?.prefill("Change: ")}
                />
              ))
            )}
            {error && <div className="banner error">{error}</div>}
          </div>
        </div>
        <Composer ref={composer} onSend={send} busy={busy} disabled={!!busyId && !busy} />
      </main>
      {confirm && <ConfirmDialog {...confirm} onClose={() => setConfirm(null)} />}
    </div>
  );
}
