import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Check, Copy, FileText, PenLine, Send } from "lucide-react";

// The minutes draft made by this answer. Only the newest draft of the chat can be approved.
export default function DraftCard({ draft, current, busy, onApprove, onChange }) {
  const [copied, setCopied] = useState(false);
  const latest = current && current.updated_at === draft.updated_at;
  const status = latest ? current.status : "replaced";
  const label = { draft: "Waiting for your approval", approved: "Approved and sent", replaced: "Replaced by a newer draft" }[status];

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(draft.markdown || "");
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch { /* clipboard blocked */ }
  };

  return (
    <div className={`draft ${status}`}>
      <div className="draft-head">
        <FileText size={16} />
        <span className="draft-kind">Minutes draft</span>
        <span className={`badge ${status}`}>{label}</span>
        <button className="icon-btn" onClick={copy} title="Copy as Markdown" aria-label="Copy as Markdown">
          {copied ? <Check size={15} /> : <Copy size={15} />}
        </button>
      </div>
      <div className="draft-body markdown">
        {/* "**Date:** …" and "**Attendees:** …" are on separate lines: keep them apart */}
        <ReactMarkdown remarkPlugins={[remarkGfm]}>{(draft.markdown || "(empty draft)").replace(/\n(?=\*\*)/g, "  \n")}</ReactMarkdown>
      </div>
      {status === "draft" && (
        <div className="draft-actions">
          <button className="btn primary" disabled={busy} onClick={onApprove}>
            <Send size={15} /> Approve and send
          </button>
          <button className="btn" disabled={busy} onClick={onChange}>
            <PenLine size={15} /> Ask for a change
          </button>
          <span className="muted small">Sends the email, creates the tasks and calendar events, saves the register.</span>
        </div>
      )}
    </div>
  );
}
