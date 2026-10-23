"""Heavy work: voice -> text (faster-whisper) and photo -> text (Ollama vision)."""
import base64
import io
import threading
import time

import httpx
from PIL import Image

from . import store
from .config import settings

_whisper = None
_whisper_lock = threading.Lock()

VISION_PROMPT = (
    "This is a photo of a whiteboard or a notebook page from a meeting. "
    "Write down all the text you can read, line by line, in its original language. "
    "Keep lists and arrows as simple text (use '-' and '->'). "
    "Write [?] for a word you cannot read. Do not add explanations."
)


def _get_whisper():
    global _whisper
    with _whisper_lock:
        if _whisper is None:
            from faster_whisper import WhisperModel  # heavy import, only when needed

            _whisper = WhisperModel(
                settings.whisper_model,
                device=settings.whisper_device,
                compute_type=settings.whisper_compute,
                download_root=str(settings.data_dir / "whisper-models"),
            )
        return _whisper


def transcribe(path: str, session_id: str | None = None, name: str = "audio") -> dict:
    start = time.time()

    def log(step, status="running", detail=""):
        if session_id:
            store.add_event(session_id, step, status, detail, source="python")

    log(f"Loading speech model (whisper {settings.whisper_model})")
    model = _get_whisper()
    segments, info = model.transcribe(path, vad_filter=True, beam_size=1)
    log(f"Transcribing {name}", detail=f"{info.duration / 60:.1f} min of audio, language: {info.language}")

    texts, next_report = [], 0.25
    for seg in segments:  # lazy generator: the real work happens here
        texts.append(seg.text.strip())
        progress = seg.end / max(info.duration, 1)
        if progress >= next_report:
            log(f"Transcribing {name}", detail=f"{int(progress * 100)}% done")
            next_report += 0.25
    text = " ".join(t for t in texts if t)
    took = time.time() - start
    log(f"Transcribed {name}", "done", f"{len(text.split())} words in {took:.0f} s")
    return {
        "text": text,
        "language": info.language,
        "duration_s": round(info.duration, 1),
        "seconds_taken": round(took, 1),
    }


def _image_b64(path: str, max_side: int = 1600) -> str:
    img = Image.open(path)
    img = img.convert("RGB")
    img.thumbnail((max_side, max_side))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return base64.b64encode(buf.getvalue()).decode()


def read_image(path: str, session_id: str | None = None, name: str = "photo") -> dict:
    start = time.time()
    if session_id:
        store.add_event(session_id, f"Reading {name}", "running",
                        f"vision model {settings.vision_model}", source="python")
    body = {
        "model": settings.vision_model,
        "messages": [{"role": "user", "content": VISION_PROMPT, "images": [_image_b64(path)]}],
        "stream": False,
        "keep_alive": 0,  # free the GPU right away: only one model fits at a time
        "options": {"temperature": 0},
    }
    resp = httpx.post(f"{settings.ollama_url}/api/chat", json=body, timeout=600)
    if resp.status_code == 404:
        raise RuntimeError(f"vision model {settings.vision_model} not found in Ollama "
                           f"(run: ollama pull {settings.vision_model})")
    resp.raise_for_status()
    text = resp.json()["message"]["content"].strip()
    took = time.time() - start
    if session_id:
        store.add_event(session_id, f"Read {name}", "done",
                        f"{len(text.split())} words in {took:.0f} s", source="python")
    return {"text": text, "seconds_taken": round(took, 1)}
