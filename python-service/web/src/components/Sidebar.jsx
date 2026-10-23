import { useEffect, useRef, useState } from "react";
import { Check, Eraser, MessageSquare, MoreHorizontal, PanelLeftClose, Pencil, Plus, Search, Trash2, X } from "lucide-react";
import { dayGroup } from "../util.js";

const GROUPS = ["Today", "Yesterday", "Previous 7 days", "Older"];

export default function Sidebar({ open, sessions, activeId, busyId, onNew, onOpen, onClear, onDelete, onRename, onClose }) {
  const [query, setQuery] = useState("");
  const shown = sessions.filter((s) => s.title.toLowerCase().includes(query.toLowerCase()));

  return (
    <>
      <div className={`scrim ${open ? "show" : ""}`} onClick={onClose} />
      <aside className={`sidebar ${open ? "open" : ""}`} aria-label="Chats">
        <div className="sidebar-top">
          <div className="brand">
            <span className="brand-mark">MP</span>
            <div>
              <div className="brand-name">MinutePilot</div>
              <div className="brand-sub">From meeting to action</div>
            </div>
            <button className="icon-btn ghost" onClick={onClose} title="Hide chats" aria-label="Hide chats">
              <PanelLeftClose size={18} />
            </button>
          </div>
          <button className="new-chat" onClick={onNew}>
            <Plus size={16} /> New chat
          </button>
          <label className="search">
            <Search size={15} />
            <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search chats" />
          </label>
        </div>

        <nav className="session-list">
          {shown.length === 0 && (
            <p className="empty-list">{sessions.length ? "No chat matches your search." : "Your chats will appear here."}</p>
          )}
          {GROUPS.map((group) => {
            const items = shown.filter((s) => dayGroup(s.updated_at) === group);
            if (!items.length) return null;
            return (
              <section key={group}>
                <h3>{group}</h3>
                {items.map((s) => (
                  <SessionItem
                    key={s.session_id}
                    session={s}
                    active={s.session_id === activeId}
                    busy={s.session_id === busyId}
                    onOpen={() => onOpen(s.session_id)}
                    onClear={() => onClear(s.session_id)}
                    onDelete={() => onDelete(s.session_id)}
                    onRename={(t) => onRename(s.session_id, t)}
                  />
                ))}
              </section>
            );
          })}
        </nav>

        <div className="sidebar-foot">
          Self-hosted · n8n · Ollama · Google
        </div>
      </aside>
    </>
  );
}

function SessionItem({ session, active, busy, onOpen, onClear, onDelete, onRename }) {
  const [menu, setMenu] = useState(false);
  const [editing, setEditing] = useState(false);
  const [title, setTitle] = useState(session.title);
  const ref = useRef(null);

  useEffect(() => {
    if (!menu) return;
    const close = (e) => { if (!ref.current?.contains(e.target)) setMenu(false); };
    document.addEventListener("mousedown", close);
    return () => document.removeEventListener("mousedown", close);
  }, [menu]);

  const save = () => {
    setEditing(false);
    if (title.trim() && title !== session.title) onRename(title.trim());
    else setTitle(session.title);
  };

  const status = busy ? "working" : session.draft_status;
  return (
    <div ref={ref} className={`session ${active ? "active" : ""}`}>
      {editing ? (
        <div className="session-edit">
          <input
            autoFocus
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter") save(); if (e.key === "Escape") { setTitle(session.title); setEditing(false); } }}
          />
          <button className="icon-btn" onClick={save} aria-label="Save name"><Check size={15} /></button>
          <button className="icon-btn" onClick={() => { setTitle(session.title); setEditing(false); }} aria-label="Cancel"><X size={15} /></button>
        </div>
      ) : (
        <button className="session-main" onClick={onOpen} title={session.title}>
          <MessageSquare size={15} className="session-icon" />
          <span className="session-title">{session.title}</span>
          {status && <span className={`dot ${status}`} title={statusLabel(status)} />}
        </button>
      )}
      {!editing && (
        <button className="icon-btn session-more" onClick={() => setMenu((m) => !m)} aria-label="Chat options">
          <MoreHorizontal size={16} />
        </button>
      )}
      {menu && (
        <div className="menu" role="menu">
          <button onClick={() => { setMenu(false); setEditing(true); }}><Pencil size={14} /> Rename</button>
          <button onClick={() => { setMenu(false); onClear(); }}><Eraser size={14} /> Clear messages</button>
          <button className="danger" onClick={() => { setMenu(false); onDelete(); }}><Trash2 size={14} /> Delete</button>
        </div>
      )}
    </div>
  );
}

function statusLabel(status) {
  return { working: "The agent is working", draft: "Draft waiting for approval", approved: "Minutes sent" }[status] || "";
}
