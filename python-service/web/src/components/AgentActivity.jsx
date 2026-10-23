import { useEffect, useState } from "react";
import { ChevronDown, CircleCheck, CircleX, Loader2, Workflow, Wrench } from "lucide-react";
import { SOURCE_LABEL, clock, duration } from "../util.js";

// Every step n8n and the Python service report for one answer, in one block that can be
// opened or closed. It is open while the agent works and closes to a one-line summary after.

function collapseSteps(events, finished) {
  const out = [];
  for (const ev of events) {
    const last = out[out.length - 1];
    // progress of the same step (e.g. "Transcribing 25 %… 50 %") replaces the line
    if (last && last.step === ev.step && last.status === "running") {
      out[out.length - 1] = { ...ev };
      continue;
    }
    for (const s of out) if (s.status === "running") s.status = "done";
    out.push({ ...ev });
  }
  if (finished) for (const s of out) if (s.status === "running") s.status = "done";
  return out;
}

export default function AgentActivity({ events, steps, running, seconds, startedAt }) {
  const [open, setOpen] = useState(running);
  const [now, setNow] = useState(Date.now() / 1000);

  useEffect(() => { setOpen(running); }, [running]);
  useEffect(() => {
    if (!running) return;
    const t = setInterval(() => setNow(Date.now() / 1000), 1000);
    return () => clearInterval(t);
  }, [running]);

  const list = collapseSteps(events, !running);
  const failed = list.some((s) => s.status === "error");
  const current = running ? list[list.length - 1] : null;
  const elapsed = running ? now - (list[0]?.at || startedAt) : seconds;

  return (
    <div className={`activity ${open ? "open" : ""} ${running ? "running" : ""} ${failed ? "failed" : ""}`}>
      <button className="activity-head" onClick={() => setOpen((o) => !o)} aria-expanded={open}>
        <span className="activity-icon">
          {running ? <Loader2 size={16} className="spin" /> : failed ? <CircleX size={16} /> : <Workflow size={16} />}
        </span>
        <span className="activity-title">
          {running
            ? (current ? current.step : "Starting…")
            : failed ? "The agent stopped on an error" : "Agent activity"}
        </span>
        <span className="activity-meta">
          {list.length} step{list.length === 1 ? "" : "s"}{elapsed ? ` · ${duration(elapsed)}` : ""}
        </span>
        <ChevronDown size={16} className="chev" />
      </button>

      {open && (
        <div className="activity-body">
          <ol className="timeline">
            {list.map((s, i) => (
              <li key={`${s.index}-${i}`} className={s.status}>
                <span className="t-icon">
                  {s.status === "running" ? <Loader2 size={14} className="spin" />
                    : s.status === "error" ? <CircleX size={14} /> : <CircleCheck size={14} />}
                </span>
                <div className="t-text">
                  <div className="t-step">
                    {s.step}
                    {s.source && <span className={`src ${s.source}`}>{SOURCE_LABEL[s.source] || s.source}</span>}
                  </div>
                  {s.detail && <div className="t-detail">{s.detail}</div>}
                </div>
                <time className="t-time">{clock(s.at)}</time>
              </li>
            ))}
            {running && list.length === 0 && <li className="running"><span className="t-icon"><Loader2 size={14} className="spin" /></span><div className="t-text">Sending your message…</div></li>}
          </ol>

          {steps.length > 0 && (
            <div className="tools">
              <div className="tools-title"><Wrench size={13} /> Tools the agent used</div>
              {steps.map((t, i) => (
                <details key={i} className="tool">
                  <summary><code>{t.tool}</code></summary>
                  <div className="tool-io">
                    <div><span className="muted">input</span><pre>{JSON.stringify(t.input, null, 1)}</pre></div>
                    <div><span className="muted">result</span><pre>{pretty(t.result)}</pre></div>
                  </div>
                </details>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function pretty(result) {
  try {
    const parsed = JSON.parse(result);
    const inner = Array.isArray(parsed) && parsed[0]?.result ? parsed[0].result : parsed;
    return typeof inner === "string" ? inner : JSON.stringify(inner, null, 1);
  } catch {
    return String(result ?? "");
  }
}
