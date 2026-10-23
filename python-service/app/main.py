"""MinutePilot Python service.

- Chat page (static files in app/ui) and its API (/api/...)
- Heavy work for n8n: /transcribe, /read-image, /extract
- Live steps: n8n and this service POST /events, the page listens on /api/events/{id}
"""
import asyncio
import json
import time
from pathlib import Path
from typing import Any

import httpx
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import media, store
from .config import settings

app = FastAPI(title="MinutePilot service")
UI_DIR = Path(__file__).parent / "ui"


@app.exception_handler(ValueError)
async def bad_value(_request, err: ValueError):
    return JSONResponse({"detail": f"bad request: {err}"}, status_code=400)


class Event(BaseModel):
    sessionId: str
    step: str
    status: str = "done"  # running | done | error
    detail: str = ""
    source: str = "n8n"


class FileRef(BaseModel):
    file_id: str
    session_id: str


class ExtractRequest(BaseModel):
    session_id: str
    file_ids: list[str]


class NoteIn(BaseModel):
    source: str = "pasted notes"
    text: str


class DoneStep(BaseModel):
    step: str  # email | tasks | calendar | postponed | register
    value: Any = True


class ChatIn(BaseModel):
    sessionId: str
    message: str = ""
    files: list[dict] = []


# ---------- page ----------

# The React app (python-service/web) is built into app/ui: index.html + assets/.
# The Docker image builds it; without a build, "/" says how to make one.

@app.get("/")
def index():
    page = UI_DIR / "index.html"
    if page.exists():
        return FileResponse(page)
    return HTMLResponse("<h1>MinutePilot</h1><p>The chat page is not built yet: "
                        "<code>cd python-service/web && npm install && npm run build</code></p>")


app.mount("/assets", StaticFiles(directory=UI_DIR / "assets", check_dir=False), name="assets")


@app.get("/health")
def health():
    return {"ok": True}


# ---------- live steps ----------

@app.post("/events")
def post_event(e: Event):
    return store.add_event(e.sessionId, e.step, e.status, e.detail, e.source)


@app.get("/api/events/{session_id}")
async def stream_events(session_id: str, after: int = 0):
    """Server-Sent Events: the page gets each step as soon as it happens."""
    async def gen():
        last = after
        idle = 0
        while True:
            events = store.events_after(session_id, last)
            for ev in events:
                last = ev["index"]
                yield f"id: {ev['index']}\ndata: {json.dumps(ev, ensure_ascii=False)}\n\n"
            idle = 0 if events else idle + 1
            if idle % 50 == 49:
                yield ": keep-alive\n\n"
            await asyncio.sleep(0.3)

    return StreamingResponse(gen(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


# ---------- chat page API ----------

@app.post("/api/upload")
async def upload(session_id: str = Form(...), file: UploadFile = File(...)):
    data = await file.read()
    if len(data) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(413, f"file larger than {settings.max_upload_mb} MB")
    info = store.add_file(session_id, file.filename or "file", file.content_type, data)
    store.add_event(session_id, f"Received file {info['name']}", "done",
                    f"{info['kind']}, {info['size'] / 1e6:.1f} MB", source="page")
    return {k: info[k] for k in ("file_id", "name", "kind", "size")}


def _draft_snapshot(draft: dict | None, since: float) -> dict | None:
    """The draft, if this answer created or changed it (shown as a card under the answer)."""
    if not draft or draft.get("updated_at", 0) < since:
        return None
    return {k: draft.get(k) for k in ("title", "date", "status", "markdown", "updated_at")}


@app.post("/api/chat")
async def chat(msg: ChatIn):
    """Save the user's message, forward it to the n8n chat workflow, save and return the answer.
    The answer keeps every step reported since the previous message (uploads included),
    so an old chat still shows what the agent did."""
    session = store.load(msg.sessionId)
    turn_start = session["messages"][-1]["at"] if session["messages"] else 0.0
    files = [{k: f.get(k) for k in ("file_id", "name", "kind", "size")} for f in msg.files]
    store.add_message(msg.sessionId, "user", msg.message, files=files)
    store.add_event(msg.sessionId, "Message sent to n8n", "done", source="page")
    started = time.time()
    body = {**msg.model_dump(), "memoryKey": f"{msg.sessionId}-{session['memory_epoch']}"}

    def save_answer(text: str, steps: list, error: str = "") -> dict:
        draft = store.load(msg.sessionId)["draft"]
        return store.add_message(
            msg.sessionId, "assistant", text, steps=steps, error=error,
            events=store.events_since(msg.sessionId, turn_start),
            seconds=round(time.time() - started, 1), draft=_draft_snapshot(draft, started))

    try:
        async with httpx.AsyncClient(timeout=settings.chat_timeout_s) as client:
            resp = await client.post(settings.n8n_chat_url, json=body)
    except httpx.HTTPError as err:
        store.add_event(msg.sessionId, "Could not reach n8n", "error", str(err), source="page")
        save_answer("I could not reach n8n. Is the stack running?", [], error=str(err))
        raise HTTPException(502, f"n8n not reachable: {err}")
    if resp.status_code >= 400:
        store.add_event(msg.sessionId, "n8n returned an error", "error",
                        resp.text[:300], source="page")
        save_answer("n8n returned an error.", [], error=resp.text[:300])
        raise HTTPException(502, f"n8n error {resp.status_code}: {resp.text[:300]}")
    try:
        data = resp.json()
    except ValueError:
        data = {"reply": resp.text, "steps": []}
    answer = save_answer(data.get("reply", ""), data.get("steps", []), error=data.get("error", ""))
    return {**data, "message": answer}


@app.get("/api/sessions")
def list_sessions():
    return store.list_sessions()


@app.get("/api/sessions/{session_id}")
def session_summary(session_id: str):
    return store.summary(session_id)


@app.get("/api/sessions/{session_id}/messages")
def session_messages(session_id: str):
    session = store.load(session_id)
    draft = session["draft"]
    return {
        "session_id": session_id,
        "title": session["title"],
        "messages": session["messages"],
        # the current draft status, so an old card can show "approved" after approval
        "draft": None if not draft else {"status": draft.get("status"), "updated_at": draft.get("updated_at")},
    }


class TitleIn(BaseModel):
    title: str


@app.patch("/api/sessions/{session_id}")
def rename_session(session_id: str, body: TitleIn):
    return store.rename_session(session_id, body.title)


@app.post("/api/sessions/{session_id}/clear")
def clear_session(session_id: str):
    store.clear_session(session_id)
    return {"ok": True}


@app.delete("/api/sessions/{session_id}")
def delete_session(session_id: str):
    try:
        store.delete_session(session_id)
    except KeyError:
        raise HTTPException(404, "no such chat")
    return {"ok": True}


@app.get("/api/status")
async def status():
    """For the header: can we reach n8n and Ollama, and are the models downloaded?"""
    out = {"n8n": False, "ollama": False, "models": []}
    async with httpx.AsyncClient(timeout=3) as client:
        try:
            base = settings.n8n_chat_url.split("/webhook/")[0]
            out["n8n"] = (await client.get(f"{base}/healthz")).status_code == 200
        except httpx.HTTPError:
            pass
        try:
            tags = (await client.get(f"{settings.ollama_url}/api/tags")).json()
            out["ollama"] = True
            out["models"] = [m["name"] for m in tags.get("models", [])]
        except (httpx.HTTPError, ValueError):
            pass
    return out


@app.post("/api/sessions/{session_id}/notes")
def add_notes(session_id: str, note: NoteIn):
    saved = store.add_note(session_id, note.source, note.text)
    return {"source": saved["source"], "words": saved["words"]}


@app.get("/api/sessions/{session_id}/notes")
def get_notes(session_id: str, max_words: int = 7000):
    return store.notes_text(session_id, max_words)


@app.get("/api/sessions/{session_id}/draft")
def get_draft(session_id: str):
    draft = store.load(session_id)["draft"]
    if not draft:
        raise HTTPException(404, "no draft yet")
    return draft


@app.put("/api/sessions/{session_id}/draft")
def put_draft(session_id: str, draft: dict):
    return store.set_draft(session_id, draft)


@app.post("/api/sessions/{session_id}/draft/done")
def draft_step_done(session_id: str, step: DoneStep):
    try:
        return store.mark_done(session_id, step.step, step.value)
    except KeyError:
        raise HTTPException(404, "no draft")


@app.post("/api/sessions/{session_id}/draft/approve")
def approve(session_id: str):
    try:
        return store.approve_draft(session_id)
    except KeyError:
        raise HTTPException(404, "no draft to approve")


# ---------- heavy work (called by n8n) ----------

def _file(ref_session: str, file_id: str) -> dict:
    try:
        return store.get_file(ref_session, file_id)
    except KeyError:
        raise HTTPException(404, f"unknown file {file_id}")


@app.post("/transcribe")
def transcribe(ref: FileRef):
    info = _file(ref.session_id, ref.file_id)
    return media.transcribe(info["path"], ref.session_id, info["name"])


@app.post("/read-image")
def read_image(ref: FileRef):
    info = _file(ref.session_id, ref.file_id)
    try:
        return media.read_image(info["path"], ref.session_id, info["name"])
    except (httpx.HTTPError, RuntimeError) as err:
        store.add_event(ref.session_id, f"Could not read {info['name']}", "error", str(err), "python")
        raise HTTPException(502, f"vision model error: {err}")


@app.post("/extract")
def extract(req: ExtractRequest):
    """Turn every attached file into text, one after another (one model in the GPU
    at a time), and save the text as meeting notes for this session."""
    results = []
    for file_id in req.file_ids:
        info = _file(req.session_id, file_id)
        try:
            if info["kind"] == "audio":
                out = media.transcribe(info["path"], req.session_id, info["name"])
                source = f"audio transcript ({info['name']})"
            elif info["kind"] == "image":
                out = media.read_image(info["path"], req.session_id, info["name"])
                source = f"photo text ({info['name']})"
            else:
                raise ValueError("only audio and image files are supported")
            note = store.add_note(req.session_id, source, out["text"])
            results.append({"name": info["name"], "kind": info["kind"], "ok": True,
                            "words": note["words"], "preview": out["text"][:300]})
        except Exception as err:  # keep going with the other files, report the error
            store.add_event(req.session_id, f"Failed on {info['name']}", "error", str(err), "python")
            results.append({"name": info["name"], "kind": info["kind"], "ok": False,
                            "error": str(err)})
    return {"items": results, "total_words": sum(r.get("words", 0) for r in results)}
