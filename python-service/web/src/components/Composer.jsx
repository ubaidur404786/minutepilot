import { forwardRef, useImperativeHandle, useRef, useState } from "react";
import { ArrowUp, Loader2, Paperclip } from "lucide-react";
import { FileChip } from "./Message.jsx";
import { fileKind } from "../util.js";

const Composer = forwardRef(function Composer({ onSend, busy, disabled }, ref) {
  const [text, setText] = useState("");
  const [files, setFiles] = useState([]);
  const box = useRef(null);
  const picker = useRef(null);

  const grow = () => {
    const el = box.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 240)}px`;
  };

  const addFiles = (list) => setFiles((f) => [...f, ...Array.from(list || [])]);

  useImperativeHandle(ref, () => ({
    prefill: (t) => { setText(t); setTimeout(() => { box.current?.focus(); grow(); }, 0); },
    openPicker: () => picker.current?.click(),
    addFiles,
  }));

  const submit = () => {
    if (busy || disabled || (!text.trim() && !files.length)) return;
    onSend(text, files);
    setText("");
    setFiles([]);
    setTimeout(grow, 0);
  };

  return (
    <div className="composer-wrap">
      <div className={`composer ${busy ? "busy" : ""}`}>
        {files.length > 0 && (
          <div className="file-row">
            {files.map((f, i) => (
              <FileChip key={`${f.name}-${i}`} file={{ name: f.name, kind: fileKind(f) }}
                onRemove={() => setFiles((all) => all.filter((_, j) => j !== i))} />
            ))}
          </div>
        )}
        <textarea
          ref={box}
          rows={1}
          value={text}
          placeholder={busy ? "The agent is working… you can type your next message" : "Message MinutePilot, or paste your meeting notes"}
          onChange={(e) => { setText(e.target.value); grow(); }}
          onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); submit(); } }}
          onPaste={(e) => { if (e.clipboardData.files.length) { e.preventDefault(); addFiles(e.clipboardData.files); } }}
        />
        <div className="composer-bar">
          <button className="icon-btn" onClick={() => picker.current?.click()} title="Attach a recording or photos" aria-label="Attach files">
            <Paperclip size={18} />
          </button>
          <input ref={picker} type="file" multiple hidden accept="audio/*,image/*,.wav,.mp3,.m4a,.ogg,.webm,.flac"
            onChange={(e) => { addFiles(e.target.files); e.target.value = ""; }} />
          <span className="hint">Audio, photos or pasted notes · Enter to send · Shift + Enter for a new line</span>
          <button className="send" onClick={submit} disabled={busy || disabled || (!text.trim() && !files.length)} aria-label="Send">
            {busy ? <Loader2 size={18} className="spin" /> : <ArrowUp size={18} />}
          </button>
        </div>
      </div>
      <p className="disclaimer">AI drafts can contain mistakes. Nothing is sent before you approve.</p>
    </div>
  );
});

export default Composer;
