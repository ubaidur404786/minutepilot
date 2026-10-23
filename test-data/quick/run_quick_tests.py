"""Send each quick test file through the chat page API and print the time and the answer.

Usage (stack running, models downloaded):
    python test-data/quick/run_quick_tests.py            all tests
    python test-data/quick/run_quick_tests.py notes      only the tests whose name contains "notes"

Each test uses a new chat session (quick-<name>-<time>), so you can open the chat page
and look at its steps. Nothing is approved: no email, task or event is created.
Only the Python standard library is used.
"""
import json
import mimetypes
import sys
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

API = "http://localhost:8000"
HERE = Path(__file__).parent
ASK = "Please write the minutes of this meeting."

TESTS = [
    # name, kind, file
    ("notes-en", "notes", "notes/team-meeting-en.txt"),
    ("notes-fr", "notes", "notes/reunion-cse-fr.txt"),
    ("notes-ami-price", "notes", "notes/ami-es2004a-price-excerpt.txt"),
    ("audio-synthetic", "file", "audio/synthetic-team-meeting-en.wav"),
    ("audio-ami", "file", "audio/ami-es2004a-intro-28s.wav"),
    ("photo-flipchart", "file", "photos/flipchart-todo-list-de.jpg"),
    ("photo-whiteboard", "file", "photos/whiteboard-spring-break-en.jpg"),
    ("photo-osm-fr", "file", "photos/osm-france-board-small-fr.jpg"),
]


def post_json(path, body, timeout=1800):
    req = urllib.request.Request(API + path, json.dumps(body).encode("utf-8"),
                                 {"Content-Type": "application/json; charset=utf-8"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def upload(session_id, path):
    boundary = uuid.uuid4().hex
    ctype = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    body = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"session_id\"\r\n\r\n{session_id}\r\n"
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{path.name}\"\r\n"
            f"Content-Type: {ctype}\r\n\r\n").encode() + path.read_bytes() + f"\r\n--{boundary}--\r\n".encode()
    req = urllib.request.Request(API + "/api/upload", body,
                                 {"Content-Type": f"multipart/form-data; boundary={boundary}"})
    with urllib.request.urlopen(req, timeout=300) as resp:
        return json.loads(resp.read().decode("utf-8"))


def get(path):
    with urllib.request.urlopen(API + path, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def run(name, kind, rel):
    path = HERE / rel
    session = f"quick-{name}-{int(time.time())}"
    start = time.time()
    if kind == "notes":
        # same as pasting the notes in the chat box
        msg = {"sessionId": session, "message": path.read_text(encoding="utf-8") + "\n\n" + ASK}
    else:
        info = upload(session, path)
        msg = {"sessionId": session, "message": ASK, "files": [info]}
    try:
        answer = post_json("/api/chat", msg)
    except urllib.error.HTTPError as err:
        print(f"\n=== {name} ({rel}) · FAILED: HTTP {err.code} {err.read().decode('utf-8', 'replace')[:300]}")
        return
    seconds = time.time() - start
    tools = ", ".join(s.get("tool") or "?" for s in answer.get("steps", [])) or "none"
    print(f"\n=== {name} ({rel}) · {seconds:.0f} s · tools: {tools}")
    print("Answer:", answer.get("reply", answer))
    try:
        draft = get(f"/api/sessions/{session}/draft")
    except Exception:
        print("Draft: none")
        return
    print("Draft:", json.dumps({k: draft.get(k) for k in
                                ("title", "date", "attendees", "decisions", "actions", "postponed", "next_meeting")},
                               ensure_ascii=False, indent=1))


if __name__ == "__main__":
    only = sys.argv[1] if len(sys.argv) > 1 else ""
    for test in TESTS:
        if only in test[0]:
            run(*test)
