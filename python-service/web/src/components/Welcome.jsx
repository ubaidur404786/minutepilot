import { CalendarDays, Camera, ClipboardList, ListTodo, Mic, NotebookPen } from "lucide-react";

export default function Welcome({ onSend, onPrefill, onAttach }) {
  const start = [
    { icon: NotebookPen, title: "Paste meeting notes", text: "Typed notes or a transcript", run: () => onPrefill("Minutes please:\n\n") },
    { icon: Mic, title: "Upload a recording", text: "Audio is transcribed on this computer", run: onAttach },
    { icon: Camera, title: "Photo of the board", text: "Whiteboard, flipchart or notebook", run: onAttach },
  ];
  const ask = [
    { icon: ListTodo, text: "Which tasks are still open?" },
    { icon: CalendarDays, text: "What meetings are coming up?" },
    { icon: ClipboardList, text: "Prepare the agenda for the next meeting." },
  ];
  return (
    <div className="welcome">
      <div className="welcome-mark">MP</div>
      <h2>What happened in your meeting?</h2>
      <p className="muted">
        Send notes, a recording or photos. I write the minutes, you approve them, and I send the email,
        create the tasks and calendar events, and save everything in the register.
      </p>
      <div className="start-grid">
        {start.map(({ icon: Icon, title, text, run }) => (
          <button key={title} className="start-card" onClick={run}>
            <Icon size={20} />
            <span className="start-title">{title}</span>
            <span className="muted small">{text}</span>
          </button>
        ))}
      </div>
      <div className="ask-row">
        {ask.map(({ icon: Icon, text }) => (
          <button key={text} className="chip" onClick={() => onSend(text)}>
            <Icon size={14} /> {text}
          </button>
        ))}
      </div>
    </div>
  );
}
