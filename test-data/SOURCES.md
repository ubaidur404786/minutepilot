# Test data sources

Two kinds of test data:
- `audio/`, `photos/`, `notes/`: fake meetings I record or write myself.
- `public/`: open datasets from the internet, listed below with where they come from and their license.
- `quick/`: very small files (public + synthetic) for fast tests, see *Quick test set* below.

All files below were downloaded on 2026-10-22, unchanged (the only changes are the `.transcript.txt` / `.reference.md` files, made from the QMSum JSON with `qmsum_to_txt.py`).

## Audio (for `/transcribe`)

| File | Source | License | Notes |
|---|---|---|---|
| `public/audio/ES2004a.Mix-Headset.wav` | **AMI Meeting Corpus**, University of Edinburgh. Meeting ES2004a, "headset mix". Download page: https://groups.inf.ed.ac.uk/ami/download/ · Direct file: https://groups.inf.ed.ac.uk/ami/AMICorpusMirror/amicorpus/ES2004a/audio/ES2004a.Mix-Headset.wav | CC BY 4.0 (https://groups.inf.ed.ac.uk/ami/corpus/license.shtml) | 17.5 min, English, 4 people, 16 kHz mono, 33.6 MB. Role-play design meeting (new TV remote control). **Not in git** (too big): download it again with the direct link. SHA-256 `3e2560b19bee6952c7c7ce041b0f1ea8a7ea9468044c4eea79d2a2c67e24ab0f` |
| `public/audio/ES2004a_90s.wav` | Cut from the file above: minute 1:00 to 2:30 (Python `wave`, no other change) | CC BY 4.0 | Short clip for quick tests (Whisper on CPU takes about real time). Not in git. |

Citation: Carletta, J. et al. (2005). *The AMI Meeting Corpus: A Pre-Announcement.* MLMI 2005.

## Transcripts and reference summaries (for "paste notes" and for checking the minutes)

| File | Source | License | Notes |
|---|---|---|---|
| `public/notes/ES2004a.qmsum.json` | **QMSum**, Yale-LILY, GitHub: https://github.com/Yale-LILY/QMSum (`data/ALL/test/ES2004a.json`) | MIT (repo LICENSE); transcript itself from AMI, CC BY 4.0 | **Same meeting as the audio above**, so the human transcript can be compared with the Whisper output, and the human summary with our minutes. |
| `public/notes/education_13.qmsum.json` | QMSum, `data/Committee/test/education_13.json` | MIT (repo); transcript is a public record of the Welsh Parliament (Senedd) committee | Children, Young People and Education Committee. 10,500 words: tests a long paste. Real public officials are named: public record, used only as test input, never emailed to anyone. |
| `public/notes/*.transcript.txt` | Made from the JSON above | same as source | `Speaker: text`, one line per turn. Ready to paste in the chat. |
| `public/notes/*.reference.md` | Made from the JSON above | same as source | Human-written summary + topic list from QMSum. Used to judge our minutes in step 9. |

Citation: Zhong, M. et al. (2021). *QMSum: A New Benchmark for Query-based Multi-domain Meeting Summarization.* NAACL 2021.

## Photos (for `/read-image`)

All from **Wikimedia Commons** (`Category:Whiteboards`). Downloaded as the 1920 px version.

| File | Original page | Author | License | Why this one |
|---|---|---|---|---|
| `public/photos/osm-france-board-meeting-2020.jpg` | https://commons.wikimedia.org/wiki/File:CA_physique_de_f%C3%A9vrier_2020_de_l%27association_OpenStreetMap_France_en_f%C3%A9vrier_2020_-_tableau.jpg | Benoît Prieur | CC0 | **French** board meeting agenda (OpenStreetMap France, Feb 2020). Clear handwriting. Easy case. |
| `public/photos/wmf-data-analysis-notes.jpg` | https://commons.wikimedia.org/wiki/File:Data_analysis_notes,_Wikimedia_Foundation.jpg | Steven (WMF) | CC BY-SA 3.0 | English meeting notes, 4 marker colours, numbers, glare. Medium case. |
| `public/photos/glam-wiki-board.jpg` | https://commons.wikimedia.org/wiki/File:BoardOrganizingGLAMWikipresence.jpg | Thelmadatter | CC BY-SA 3.0 | Diagram + small text, taken at an angle, dim light. Hard case (expected to fail partly). |

## Quick test set (`quick/`, added 2026-10-23)

Very small files so one test takes seconds to about two minutes. What a good answer looks like for each file: `quick/README.md`. All of them are small enough to keep in git (the 2 audio clips are 0.9 and 1.1 MB).

| File | Source | License | How it was made |
|---|---|---|---|
| `quick/audio/ami-es2004a-intro-28s.wav` | **AMI Meeting Corpus**, meeting ES2004a (same file as above) | CC BY 4.0 | Cut from `public/audio/ES2004a_90s.wav`, seconds 20.0–47.8 (= 1:20–1:48 of the original), Python `wave`, 16 kHz mono. Start and end chosen from Whisper segment times |
| `quick/audio/synthetic-team-meeting-en.wav` | **Made for this project** (synthetic): 5 sentences read by the Windows voices "Microsoft Zira" and "Microsoft David" (`System.Speech`, 16 kHz mono) | CC0 (my own script; the voices are Windows text-to-speech) | Fake meeting with known facts, so the result can be checked exactly. Same content as `quick/notes/team-meeting-en.txt` |
| `quick/notes/team-meeting-en.txt` | **Made for this project** (synthetic, fake people) | CC0 | Written by hand |
| `quick/notes/reunion-cse-fr.txt` | **Made for this project** (synthetic French CSE meeting, fake people) | CC0 | Written by hand |
| `quick/notes/ami-es2004a-price-excerpt.txt` | **QMSum** transcript of AMI ES2004a (`public/notes/ES2004a.transcript.txt`, lines 132–171) | MIT (QMSum) / CC BY 4.0 (AMI) | Copied unchanged. Contains a trap: 25 Euros is also said as "seventeen Pounds" |
| `quick/photos/flipchart-todo-list-de.jpg` | **Wikimedia Commons**, https://commons.wikimedia.org/wiki/File:Flipchart_ToDo-Liste.jpg | Public domain (author: Markus Bärlocher) | 1280 px Commons thumbnail, reduced to 580×800 (Pillow, JPEG quality 85) |
| `quick/photos/whiteboard-spring-break-en.jpg` | **Wikimedia Commons**, https://commons.wikimedia.org/wiki/File:To_do.JPG | CC BY-SA 3.0 (author: REisemann3937) | 1280 px Commons thumbnail, reduced to 1024×768 |
| `quick/photos/osm-france-board-small-fr.jpg` | Same as `public/photos/osm-france-board-meeting-2020.jpg` (Benoît Prieur, Wikimedia Commons) | CC0 | Reduced to 768×1024 |

Searched and not used for the quick set:
- *To do list.jpg* (Commons, CC BY 2.0, a notebook to-do list): one line is an inappropriate comment about a person.
- French speech on Commons: only single-word pronunciation clips (Shtooka project) or 1-hour spoken Wikipedia articles; Windows here has no French voice, so French is covered by the notes and the OSM photo.
- Mozilla Common Voice (CC0 short sentences): download needs an account, and sentences are not meetings.

## Looked at, not used

- **IAM Handwriting Database**: needs registration, non-commercial only.
- **HumynLabs handwritten notes** (Hugging Face, CC BY 4.0): school notes in PDF, not meeting notes.
- **MeetingBank** (Hugging Face): city council meetings, CC BY-NC-SA; QMSum was enough for now.
