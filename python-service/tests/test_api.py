"""API tests without the heavy models: Whisper and Ollama are replaced by fakes."""
import json
import os
import tempfile

os.environ["DATA_DIR"] = tempfile.mkdtemp()

from fastapi.testclient import TestClient  # noqa: E402

from app import main, media, store  # noqa: E402

client = TestClient(main.app)
SID = "test123"


def test_health_and_page():
    assert client.get("/health").json() == {"ok": True}
    assert "MinutePilot" in client.get("/").text


def test_bad_session_id_is_rejected():
    r = client.post("/events", json={"sessionId": "../etc", "step": "x"})
    assert r.status_code == 400


def test_events_are_kept_in_order():
    client.post("/events", json={"sessionId": SID, "step": "first"})
    client.post("/events", json={"sessionId": SID, "step": "second", "status": "running"})
    events = store.events_after(SID, 0)
    assert [e["step"] for e in events][-2:] == ["first", "second"]
    assert events[-1]["index"] > events[-2]["index"]


def test_upload_and_extract(monkeypatch):
    monkeypatch.setattr(media, "transcribe", lambda path, sid, name: {"text": "we decide to buy chairs"})
    monkeypatch.setattr(media, "read_image", lambda path, sid, name: {"text": "budget 2000"})
    a = client.post("/api/upload", data={"session_id": SID}, files={"file": ("rec.m4a", b"123", "audio/mp4")}).json()
    p = client.post("/api/upload", data={"session_id": SID}, files={"file": ("board.jpg", b"456", "image/jpeg")}).json()
    t = client.post("/api/upload", data={"session_id": SID}, files={"file": ("x.txt", b"hi", "text/plain")}).json()
    assert (a["kind"], p["kind"], t["kind"]) == ("audio", "image", "other")

    out = client.post("/extract", json={"session_id": SID, "file_ids": [a["file_id"], p["file_id"], t["file_id"]]}).json()
    assert [i["ok"] for i in out["items"]] == [True, True, False]
    assert out["total_words"] == 7

    notes = client.get(f"/api/sessions/{SID}/notes").json()
    assert "buy chairs" in notes["text"] and "budget 2000" in notes["text"]
    assert client.get(f"/api/sessions/{SID}").json()["total_words"] == 7


def test_notes_are_cut_when_too_long():
    sid = "long1"
    client.post(f"/api/sessions/{sid}/notes", json={"text": "word " * 50})
    out = client.get(f"/api/sessions/{sid}/notes", params={"max_words": 10}).json()
    assert out["truncated"] and len(out["text"].split()) == 10


def test_draft_then_approve():
    sid = "draft1"
    assert client.get(f"/api/sessions/{sid}/draft").status_code == 404
    assert client.post(f"/api/sessions/{sid}/draft/approve").status_code == 404
    client.put(f"/api/sessions/{sid}/draft", json={"title": "CSE", "actions": [{"what": "x"}], "markdown": "# CSE"})
    assert client.get(f"/api/sessions/{sid}").json()["draft"] == {"title": "CSE", "status": "draft", "actions": 1}
    assert client.post(f"/api/sessions/{sid}/draft/approve").json()["status"] == "approved"


def test_notes_after_approval_start_a_new_meeting():
    sid = "newmeeting1"
    client.post(f"/api/sessions/{sid}/notes", json={"text": "old meeting notes"})
    client.put(f"/api/sessions/{sid}/draft", json={"title": "Old", "actions": [], "markdown": "# Old"})
    client.post(f"/api/sessions/{sid}/notes", json={"text": "second photo, same meeting"})
    assert client.get(f"/api/sessions/{sid}").json()["draft"]["title"] == "Old"  # not approved: notes add up
    client.post(f"/api/sessions/{sid}/draft/approve")
    client.post(f"/api/sessions/{sid}/notes", json={"text": "new meeting notes"})
    notes = client.get(f"/api/sessions/{sid}/notes").json()["text"]
    assert "new meeting notes" in notes and "old meeting" not in notes
    assert client.get(f"/api/sessions/{sid}").json()["draft"] is None


def test_done_steps_are_kept_until_the_draft_changes():
    sid = "done1"
    assert client.post(f"/api/sessions/{sid}/draft/done", json={"step": "email"}).status_code == 404
    client.put(f"/api/sessions/{sid}/draft", json={"title": "CSE", "actions": [], "markdown": "# CSE"})
    client.post(f"/api/sessions/{sid}/draft/done", json={"step": "email"})
    client.post(f"/api/sessions/{sid}/draft/done", json={"step": "tasks", "value": {"0": "t0"}})
    done = client.post(f"/api/sessions/{sid}/draft/done", json={"step": "tasks", "value": {"1": "t1"}}).json()
    assert done == {"email": True, "tasks": {"0": "t0", "1": "t1"}}
    client.put(f"/api/sessions/{sid}/draft", json={"title": "CSE v2", "actions": [], "markdown": "# CSE", "done": done})
    assert "done" not in client.get(f"/api/sessions/{sid}/draft").json()


def test_chat_reports_n8n_down():
    main.settings.n8n_chat_url = "http://127.0.0.1:9/nothing"
    r = client.post("/api/chat", json={"sessionId": "chat1", "message": "hi"})
    assert r.status_code == 502
    assert store.events_after("chat1", 0)[-1]["status"] == "error"


def test_chat_history_rename_clear_delete(monkeypatch):
    import httpx

    sent = {}

    def fake_n8n(request):
        sent.update(json.loads(request.content))
        store.add_event("hist1", "AI is writing the minutes", "running")
        store.set_draft("hist1", {"title": "CSE", "actions": [], "markdown": "# CSE"})
        return httpx.Response(200, json={"reply": "Draft ready", "steps": [{"tool": "make_minutes"}]})

    real_client = httpx.AsyncClient
    monkeypatch.setattr(main.httpx, "AsyncClient",
                        lambda **kw: real_client(transport=httpx.MockTransport(fake_n8n), **kw))
    main.settings.n8n_chat_url = "http://n8n.test/webhook/minutepilot-chat"

    r = client.post("/api/chat", json={"sessionId": "hist1", "message": "Minutes of the CSE meeting\nnotes..."})
    assert r.status_code == 200 and r.json()["reply"] == "Draft ready"
    assert sent["memoryKey"] == "hist1-0"

    chat = client.get("/api/sessions/hist1/messages").json()
    user, answer = chat["messages"]
    assert chat["title"] == "Minutes of the CSE meeting"
    assert user["role"] == "user" and answer["role"] == "assistant"
    assert [e["step"] for e in answer["events"]][-1] == "AI is writing the minutes"
    assert answer["draft"]["title"] == "CSE" and answer["steps"][0]["tool"] == "make_minutes"
    assert any(s["session_id"] == "hist1" for s in client.get("/api/sessions").json())

    assert client.patch("/api/sessions/hist1", json={"title": "Renamed"}).json()["title"] == "Renamed"

    client.post("/api/sessions/hist1/clear")
    assert client.get("/api/sessions/hist1/messages").json()["messages"] == []
    client.post("/api/chat", json={"sessionId": "hist1", "message": "again"})
    assert sent["memoryKey"] == "hist1-1"  # fresh agent memory after clearing

    assert client.delete("/api/sessions/hist1").status_code == 200
    assert not any(s["session_id"] == "hist1" for s in client.get("/api/sessions").json())
    assert client.delete("/api/sessions/hist1").status_code == 404


def test_failed_chat_is_saved_with_its_error():
    main.settings.n8n_chat_url = "http://127.0.0.1:9/nothing"
    client.post("/api/chat", json={"sessionId": "chat2", "message": "hi"})
    answer = client.get("/api/sessions/chat2/messages").json()["messages"][-1]
    assert answer["role"] == "assistant" and answer["error"]
