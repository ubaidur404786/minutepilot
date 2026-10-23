import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { AlertTriangle, FileAudio, FileImage, File as FileIcon } from "lucide-react";
import AgentActivity from "./AgentActivity.jsx";
import DraftCard from "./DraftCard.jsx";

export default function Message({ message, liveEvents, draftState, busy, onApprove, onChange }) {
  if (message.role === "user") {
    return (
      <div className="msg user">
        <div className="bubble">
          {message.files?.length > 0 && (
            <div className="file-row">
              {message.files.map((f) => <FileChip key={f.name} file={f} />)}
            </div>
          )}
          {message.text && <div className="user-text">{message.text}</div>}
        </div>
      </div>
    );
  }

  const running = !!message.pending;
  const events = running ? liveEvents : message.events || [];
  return (
    <div className="msg assistant">
      <div className="avatar" aria-hidden>MP</div>
      <div className="assistant-body">
        {(running || events.length > 0) && (
          <AgentActivity
            events={events}
            steps={message.steps || []}
            running={running}
            seconds={message.seconds}
            startedAt={message.at}
          />
        )}
        {!running && message.text && (
          <div className="markdown">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.text}</ReactMarkdown>
          </div>
        )}
        {!running && message.error && (
          <div className="notice error">
            <AlertTriangle size={16} />
            <div>
              <strong>Something went wrong.</strong> {message.error}
              <div className="muted">Open the agent activity above to see where it stopped.</div>
            </div>
          </div>
        )}
        {!running && message.draft && (
          <DraftCard draft={message.draft} current={draftState} busy={busy} onApprove={onApprove} onChange={onChange} />
        )}
      </div>
    </div>
  );
}

export function FileChip({ file, onRemove }) {
  const Icon = file.kind === "audio" ? FileAudio : file.kind === "image" ? FileImage : FileIcon;
  return (
    <span className={`file-chip ${file.kind}`}>
      <Icon size={14} />
      <span className="file-name">{file.name}</span>
      {onRemove && <button onClick={onRemove} aria-label={`Remove ${file.name}`}>×</button>}
    </span>
  );
}
