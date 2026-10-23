"""Turn a QMSum meeting JSON into (1) a plain transcript to paste in chat and
(2) a reference summary file used later to judge our minutes."""
import json
import sys
from pathlib import Path

src = Path(sys.argv[1])
out_dir = Path(sys.argv[2])
name = src.name.replace(".qmsum.json", "")
d = json.loads(src.read_text(encoding="utf-8"))

lines = [f"{t['speaker']}: {t['content']}" for t in d["meeting_transcripts"]]
(out_dir / f"{name}.transcript.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

ref = ["# Reference answers from QMSum (human-written)", ""]
for q in d.get("general_query_list", []):
    ref += [f"## {q['query']}", q["answer"], ""]
ref += ["# Topics", ""]
ref += [f"- {t['topic']}" for t in d.get("topic_list", [])]
(out_dir / f"{name}.reference.md").write_text("\n".join(ref) + "\n", encoding="utf-8")

print(name, len(lines), "turns", sum(len(l.split()) for l in lines), "words")
