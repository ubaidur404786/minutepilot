"""Small file-based store for one chat session: uploaded files, meeting notes,
the minutes draft, the chat history, and the live list of steps shown in the chat page.

One JSON file per session in DATA_DIR/sessions. Live step events stay in memory;
the steps of each answer are copied into its saved message, so old chats still show them."""
import json
import re
import threading
import time
import uuid
from pathlib import Path

from .config import settings

_lock = threading.Lock()
_events: dict[str, list[dict]] = {}
_counter = 0

AUDIO_EXT = {".wav", ".mp3", ".m4a", ".ogg", ".webm", ".flac", ".aac", ".mp4"}
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".bmp"}


def _safe_id(value: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", value or ""):
        raise ValueError("invalid id")
    return value


def _session_path(session_id: str) -> Path:
    return settings.data_dir / "sessions" / f"{_safe_id(session_id)}.json"


def load(session_id: str) -> dict:
    path = _session_path(session_id)
    session = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"session_id": session_id}
    # older session files have no chat history: fill in the missing keys
    now = time.time()
    for key, default in (("files", {}), ("notes", []), ("draft", None), ("messages", []), ("title", ""),
                         ("created_at", now), ("updated_at", now), ("memory_epoch", 0)):
        session.setdefault(key, default)
    return session


def save(session: dict) -> None:
    path = _session_path(session["session_id"])
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(session, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(path)


# ---------- files ----------

def file_kind(filename: str, content_type: str | None) -> str:
    ext = Path(filename).suffix.lower()
    ctype = (content_type or "").lower()
    if ext in AUDIO_EXT or ctype.startswith("audio/"):
        return "audio"
    if ext in IMAGE_EXT or ctype.startswith("image/"):
        return "image"
    return "other"


def add_file(session_id: str, filename: str, content_type: str | None, data: bytes) -> dict:
    file_id = uuid.uuid4().hex[:16]
    ext = Path(filename).suffix.lower()[:8]
    path = settings.data_dir / "uploads" / f"{file_id}{ext}"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    info = {
        "file_id": file_id,
        "name": Path(filename).name,
        "kind": file_kind(filename, content_type),
        "size": len(data),
        "path": str(path),
    }
    with _lock:
        session = load(session_id)
        session["files"][file_id] = info
        save(session)
    return info


def get_file(session_id: str, file_id: str) -> dict:
    info = load(session_id)["files"].get(file_id)
    if not info:
        raise KeyError(file_id)
    return info


# ---------- notes ----------

def add_note(session_id: str, source: str, text: str) -> dict:
    note = {"source": source, "text": text.strip(), "words": len(text.split()), "at": time.time()}
    new_meeting = False
    with _lock:
        session = load(session_id)
        # Minutes already approved and sent: new material belongs to a new meeting.
        # Without this, old notes were mixed into the next draft of the same chat.
        if session["draft"] and session["draft"].get("status") == "approved":
            session["notes"] = []
            session["draft"] = None
            new_meeting = True
        session["notes"].append(note)
        save(session)
    if new_meeting:
        add_event(session_id, "New meeting started", "done",
                  "the previous minutes were already sent, so their notes are not used again", source="python")
    return note


def clear_session(session_id: str) -> None:
    """Empty the chat: messages, notes and draft. The agent memory in n8n is keyed by
    session + memory_epoch, so a new epoch gives the agent a fresh memory too."""
    with _lock:
        session = load(session_id)
        session["notes"] = []
        session["draft"] = None
        session["messages"] = []
        session["title"] = ""
        session["memory_epoch"] += 1
        session["updated_at"] = time.time()
        save(session)
    with _lock:
        _events.pop(session_id, None)


def delete_session(session_id: str) -> None:
    """Remove the chat for good: its JSON file, its uploaded files and its live steps."""
    path = _session_path(session_id)
    if not path.exists():
        raise KeyError(session_id)
    with _lock:
        session = load(session_id)
        for info in session["files"].values():
            Path(info["path"]).unlink(missing_ok=True)
        path.unlink()
        _events.pop(session_id, None)


def rename_session(session_id: str, title: str) -> dict:
    with _lock:
        session = load(session_id)
        session["title"] = title.strip()[:80]
        save(session)
    return {"session_id": session_id, "title": session["title"]}


def list_sessions() -> list[dict]:
    """Chats for the sidebar, newest first. Sessions without messages (API tests) are left out."""
    out = []
    for path in (settings.data_dir / "sessions").glob("*.json"):
        try:
            session = load(path.stem)
        except (ValueError, json.JSONDecodeError):
            continue
        if not session["messages"]:
            continue
        draft = session["draft"]
        out.append({
            "session_id": session["session_id"],
            "title": session["title"] or "New chat",
            "updated_at": session["updated_at"],
            "messages": len(session["messages"]),
            "draft_status": draft.get("status") if draft else None,
        })
    return sorted(out, key=lambda s: s["updated_at"], reverse=True)


# ---------- chat history ----------

def add_message(session_id: str, role: str, text: str, **extra) -> dict:
    """Save one chat message (user or assistant). The first user message names the chat."""
    message = {"id": uuid.uuid4().hex[:12], "role": role, "text": text, "at": time.time(), **extra}
    with _lock:
        session = load(session_id)
        session["messages"].append(message)
        if role == "user" and not session["title"]:
            first_line = (text.strip().splitlines() or [""])[0]
            names = ", ".join(f.get("name", "") for f in extra.get("files", []))
            title = first_line or names or "New chat"
            session["title"] = title[:60] + ("…" if len(title) > 60 else "")
        session["updated_at"] = message["at"]
        save(session)
    return message


def notes_text(session_id: str, max_words: int) -> dict:
    full = "\n\n".join(f"### {n['source']}\n{n['text']}" for n in load(session_id)["notes"])
    words = full.split()
    total = len(words)
    truncated = total > max_words
    text = " ".join(words[:max_words]) if truncated else full
    return {"text": text, "words": total, "used_words": min(total, max_words), "truncated": truncated}


# ---------- draft ----------

def set_draft(session_id: str, draft: dict) -> dict:
    with _lock:
        session = load(session_id)
        draft = {**draft, "status": "draft", "updated_at": time.time()}
        draft.pop("done", None)  # a new or changed draft has not been sent yet
        session["draft"] = draft
        save(session)
    return draft


def mark_done(session_id: str, step: str, value) -> dict:
    """Remember a finished approval step (email, tasks, ...) so a retry after a failure skips it."""
    with _lock:
        session = load(session_id)
        if not session["draft"]:
            raise KeyError("no draft")
        done = session["draft"].setdefault("done", {})
        if isinstance(value, dict) and isinstance(done.get(step), dict):
            done[step].update(value)
        else:
            done[step] = value
        save(session)
        return done


def approve_draft(session_id: str) -> dict:
    with _lock:
        session = load(session_id)
        if not session["draft"]:
            raise KeyError("no draft")
        session["draft"]["status"] = "approved"
        session["draft"]["approved_at"] = time.time()
        save(session)
        return session["draft"]


def summary(session_id: str) -> dict:
    session = load(session_id)
    draft = session["draft"]
    return {
        "session_id": session_id,
        "notes": [{"source": n["source"], "words": n["words"]} for n in session["notes"]],
        "total_words": sum(n["words"] for n in session["notes"]),
        "draft": None if not draft else {
            "title": draft.get("title"),
            "status": draft.get("status"),
            "actions": len(draft.get("actions", [])),
        },
    }


# ---------- live steps ----------

def add_event(session_id: str, step: str, status: str = "done", detail: str = "", source: str = "") -> dict:
    _safe_id(session_id)
    event = {"step": step, "status": status, "detail": detail, "source": source, "at": time.time()}
    global _counter
    with _lock:
        _counter += 1
        event["index"] = _counter
        events = _events.setdefault(session_id, [])
        events.append(event)
        del events[:-500]
    return event


def events_after(session_id: str, after: int) -> list[dict]:
    with _lock:
        return [e for e in _events.get(session_id, []) if e["index"] > after]


def events_since(session_id: str, since: float) -> list[dict]:
    """Steps reported after a moment in time: saved with the answer they belong to."""
    with _lock:
        return [e for e in _events.get(session_id, []) if e["at"] >= since]
