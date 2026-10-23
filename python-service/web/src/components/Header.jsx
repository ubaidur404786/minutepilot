import { useState } from "react";
import { Eraser, Moon, PanelLeftOpen, SquarePen, Sun } from "lucide-react";

export default function Header({ title, sidebarOpen, onToggleSidebar, onNew, onClear, status, theme, onTheme }) {
  return (
    <header className="header">
      {!sidebarOpen && (
        <>
          <button className="icon-btn" onClick={onToggleSidebar} title="Show chats" aria-label="Show chats">
            <PanelLeftOpen size={18} />
          </button>
          <button className="icon-btn" onClick={onNew} title="New chat" aria-label="New chat">
            <SquarePen size={18} />
          </button>
        </>
      )}
      <h1 className="header-title">{title}</h1>
      <div className="header-actions">
        <ServiceStatus status={status} />
        {onClear && (
          <button className="btn subtle" onClick={onClear} title="Clear this chat">
            <Eraser size={15} /> <span className="hide-sm">Clear</span>
          </button>
        )}
        <button className="icon-btn" onClick={onTheme} title="Light / dark" aria-label="Switch light or dark theme">
          {theme === "dark" ? <Sun size={18} /> : <Moon size={18} />}
        </button>
      </div>
    </header>
  );
}

function ServiceStatus({ status }) {
  const [open, setOpen] = useState(false);
  if (!status) return null;
  const items = status.offline
    ? [["Python service", false]]
    : [["n8n workflows", status.n8n], ["Ollama", status.ollama]];
  const allOk = items.every(([, ok]) => ok);
  return (
    <div className="status-wrap">
      <button className={`status-pill ${allOk ? "ok" : "bad"}`} onClick={() => setOpen((o) => !o)}>
        <span className="pulse" /> {allOk ? "All systems ready" : "Check services"}
      </button>
      {open && (
        <div className="status-pop" onMouseLeave={() => setOpen(false)}>
          {items.map(([name, ok]) => (
            <div key={name} className="status-row">
              <span className={`dot ${ok ? "approved" : "error"}`} /> {name}
              <span className="muted">{ok ? "running" : "not reachable"}</span>
            </div>
          ))}
          {status.models?.length > 0 && (
            <div className="status-models">
              <div className="muted">Models in Ollama</div>
              {status.models.map((m) => <code key={m}>{m}</code>)}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
