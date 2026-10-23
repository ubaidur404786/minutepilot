import { useEffect, useState } from "react";

export default function ConfirmDialog({ title, text, action, danger, run, onClose }) {
  const [working, setWorking] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const esc = (e) => { if (e.key === "Escape") onClose(); };
    document.addEventListener("keydown", esc);
    return () => document.removeEventListener("keydown", esc);
  }, [onClose]);

  const go = async () => {
    setWorking(true);
    try {
      await run();
      onClose();
    } catch (err) {
      setError(err.message);
      setWorking(false);
    }
  };

  return (
    <div className="modal-scrim" onMouseDown={onClose}>
      <div className="modal" role="dialog" aria-modal="true" aria-labelledby="confirm-title" onMouseDown={(e) => e.stopPropagation()}>
        <h2 id="confirm-title">{title}</h2>
        <p className="muted">{text}</p>
        {error && <p className="error-text">{error}</p>}
        <div className="modal-actions">
          <button className="btn" onClick={onClose}>Cancel</button>
          <button className={`btn ${danger ? "danger" : "primary"}`} onClick={go} disabled={working} autoFocus>
            {working ? "Working…" : action}
          </button>
        </div>
      </div>
    </div>
  );
}
