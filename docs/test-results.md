# Test results

Real results only, including failures. Laptop: i5-13420H, 7.6 GB RAM, RTX 3050 6 GB.

## 2026-10-22 · smoke tests (no AI models yet, Google not connected)

| Test | Input | Result |
|---|---|---|
| Python unit tests | `python -m pytest python-service/tests` | 7 passed (Whisper and Ollama replaced by fakes) |
| Chat page → n8n → agent → chat page | "What are my open tasks?" in the chat page | Works up to the AI agent. The agent fails with `model 'qwen2.5:7b' not found` (model not downloaded yet); the error path answers the chat cleanly. Right panel showed live: *Message sent to n8n → n8n received the message → AI agent is deciding → AI agent failed* |
| Files through workflow 1 | 90 s audio + 1 photo | n8n called `/extract`; each file's success/failure was reported live. First run failed: missing `requests` package (fixed), then PyAV 19 incompatible with faster-whisper (`metadata_errors`) → pinned `av==16.1.0`. Photo: vision model not downloaded yet |
| Whisper `small`, CPU int8 | `test-data/public/audio/ES2004a_90s.wav` (AMI ES2004a, minute 1:00–2:30) | 90 s of audio transcribed in **87.5 s** (includes loading the model; the first run also downloaded the model, ~11 min on this connection). Text is close to the human transcript; one visible error: "pooches" → "poochers". Rough speed on this CPU: about real time, so the full 17.5-min recording will take around 15 min |

## 2026-10-23 · models downloaded, Google credentials imported (not signed in yet)

| Test | Input | Result |
|---|---|---|
| Models present | `ollama list` | `qwen2.5:7b` (4.7 GB) and `qwen2.5vl:3b` (3.2 GB) |
| Text model alone | "Reply with exactly: OK" | Correct. 39.3 s, of which 38.2 s loading the model (cold start). In GPU: 4.3 of 5.4 GB, the rest runs on the CPU (6 GB card) |
| Vision model alone (`/read-image`) | `wmf-data-analysis-notes.jpg` (medium) | 197.5 s (includes swapping the text model out of the GPU). Text is readable and in the right order; some words misread ("coated", "Huggle Sheet 1: 2") |
| Minutes from pasted transcript (chat → agent → `make_minutes`) | ES2004a transcript, 3,784 words | Works end to end in **87.6 s**; the right panel showed every step live. Agent picked `make_minutes` correctly. **Quality vs QMSum reference:** production cost 12.50 € correct; **selling price wrong: draft said 17 €, transcript says "twenty five Euros"**; next meeting date 2026-11-24 **invented** (not in the transcript); actions vague ("work on individual designs", owner unassigned). Attendees = roles (correct for AMI) |
| Change the draft (`change_minutes`) | "The selling price was 25 euros, not 17." | 1st try: **failed** — agent answered in Chinese, called no tool, and said the change was recorded. After a prompt fix: tool called, decision now "25 Euros" (43 s) |
| Photo through the chat | `osm-france-board-meeting-2020.jpg` (easy, French) | Works end to end (5 min 38 s: 235 s reading the photo, the rest the two text-model calls). OCR text faithful. 1st draft poor: every heading became an action **and** a postponed topic (10 + 10), date guessed from the file name (2020-10-23). After a prompt fix: 2 actions, 4 postponed topics, date = today; but owners "Membre2"/"Membre3" were **invented** |
| Approve (before Google sign-in) | "Approved, send it." | **Failed badly at first:** the agent called no tool but replied "Approving and sending… Calendar event added… saved in the register". Fixed by routing approval around the AI (see below). Now: answers in ~1 s, stops at Gmail with "Google is not connected yet" and nothing else runs; draft stays "draft" |
| Approve variants | "Approve", "Valider", "Approuvé" | All three go straight to workflow 3 |
| Lookup (before Google sign-in) | "Which tasks are still open?" | 1st try: tool failed on its input schema (`query` required) and the agent still answered "I found 2 open actions" (invented). Fixed: `query` optional; the agent now says it could not get the tasks, and the answer carries a "lookup failed" warning |
| Python unit tests | `python -m pytest -q tests` | 7 passed |

### Bugs found and fixed on 2026-10-23
- `setup-n8n.ps1` never imported the Google credentials: Windows PowerShell adds a BOM when it pipes text to `docker`, n8n rejected the JSON (`Unexpected token` = the invisible BOM character). The container now strips the BOM. Output now says "Successfully imported 5 credentials".
- Google Calendar nodes (workflows 3, 4, 6) used calendar ID `primary`; n8n 2.44 only accepts an email-shaped ID ("Not a valid Google Calendar ID") and refused to start workflow 3. Now the owner's Gmail address (= the primary calendar).
- Workflow 3 gave tasks owned by "Unassigned" the address `…+unassigned@gmail.com` (case-sensitive check). Fixed.
- Approval no longer depends on the model: a clear approval of a draft goes from workflow 1 directly to workflow 3.
- The answer gets a visible warning when a tool failed, or when it claims an action but no tool ran.
- Prompts: agent must call `change_minutes` to change the draft, must not take title/date from file names, answers in French or English only; minutes: headings are not actions, no item in two lists.

### Not fixed (model limits, kept visible)
- Wrong numbers and invented dates/owners in drafts (see above). This is why the human approval step exists: read the draft before approving.
- Speed: a photo takes ~4 min to read on this laptop; one model swap costs ~40 s.

## 2026-10-23 · Google connected: full test

Each result was also checked directly in Gmail, Google Calendar and the Google Sheet, not only from n8n's report.

| Test | Input | Result |
|---|---|---|
| Google sign-in | 4 credentials in n8n | All 4 have an access and a refresh token |
| Lookup: calendar | "What meetings are coming up in my calendar?" (chat page) | Works. Lists the 4 upcoming events. Steps shown live, including "Looking up information · calendar" |
| Lookup: register | "What did we decide in past meetings about the price?" | Works (searched the Sheet; empty at that time) |
| Lookup: tasks | "Which tasks are still open?" | Works in a chat with a draft. In a **new** chat the agent first answered "no draft yet" without calling the tool; fixed with a prompt rule ("lookup works at any time"), then worked |
| Approve, 1st try | Kick-off draft (ES2004a) | **Failed** at Google Tasks: `Bad request` because the due date had no time zone (`2026-11-24T09:00:00`). The email had already gone out and task 1 was already created |
| Approve, 2nd try (after the date fix) | same draft | Worked in 24 s: email to 5 addresses (owner + 4 aliases), 2 tasks, 2 calendar events, rows in Meetings / Actions / Postponed. **But the retry sent the email a second time and created task 1 again**, and one Actions row had no task id |
| Approval made safe to retry | test draft with a broken due date on action 2 | 1st try: email + task A done, task B failed → "Approval stopped", draft stays unapproved, what was done is recorded. After fixing the date, 2nd try: **no second email**, only task B, the calendar event and the register rows. Checked in Gmail (1 email), Calendar (1 event), Sheet (1 meeting row) |
| Approve an already approved draft | "Approve" | "These minutes were already approved and sent." (before the fix the AI answered "Do you approve?") |
| Agenda in the chat | "Prepare the agenda for the next meeting." | Works: postponed topics + open tasks from Google. It mixes topics from all meetings (by design: every open postponed topic) |
| Morning reminders (workflow 5, run by hand) | 1 task due today | Email "MinutePilot: 1 task(s) late or due today" received |
| Agenda email (workflow 4, run by hand) | meeting in 2 days | 1st run: **no email** — the "meeting in exactly 2 days" check never matched (`$now.plus(2, 'days')` adds 2 ms inside a Code node). After the fix: email "Draft agenda: Next meeting: Schedule test" received |
| Live steps in the chat page | the questions above | Every step appears on the right as it happens. A failed tool shows a warning under the answer and its error in "Tools the agent used" (seen once while workflows were being re-imported: "workflow is not active") |

### Bugs found and fixed (Google part)
- Google Tasks due date needs a time zone: now `YYYY-MM-DDT00:00:00.000Z`.
- Approval was not safe to retry: a failure halfway left the email sent and some tasks created, and a retry did them again. Now every finished step is recorded on the draft (`/api/sessions/{id}/draft/done`) and skipped on the next try; tasks and events are recorded one by one.
- Actions rows lost task ids (matched by position); now built from the recorded ids in their own branch.
- "Approve" on an approved draft went to the AI; now it gets the "already approved" answer.
- Agenda workflow: date maths fixed (`$now.plus({ days: 2 })`); the daily run logged with an empty session id (400 from the Python service), now `daily-jobs`.
- Workflows 4 and 5 had only a schedule trigger, so they could not be tested on demand: added a **Test now** (manual) trigger.

### Test data left in your Google account
Test emails in Gmail ("Minutes: Kick-off meeting" ×2, "Minutes: Retry test", "Minutes: Schedule test", one reminder, one agenda); 5 Google Tasks (one duplicate "Work on individual designs…" from the bug above); calendar events on 23 Oct, 25 Oct, 6 Nov and 24 Nov; 3 meetings in the register Sheet. Delete them by hand when you no longer need them.

## 2026-10-23 · Quick test set (`test-data/quick/`, run with `run_quick_tests.py`)

Time = from sending the message to the answer, on this laptop (includes swapping models in the GPU). Expected answers: `test-data/quick/README.md`.

| Test | Time | Result |
|---|---|---|
| `notes/team-meeting-en.txt` (10 lines) | 53 s | All facts right: 3 actions with owner and date, launch date, postponed budget, next meeting 2026-11-06 10:00. Small fault: the 3 actions are also repeated as "decisions" |
| `notes/reunion-cse-fr.txt` (8 lines, French) | 61 s | Minutes in French, all facts right (13 Dec, 2 000 €, Julie 7 Nov, Karim 14 Nov, chèques vacances postponed, 20 Nov 14:00). Same small fault: actions repeated as decisions |
| `notes/ami-es2004a-price-excerpt.txt` (383 words) | 54 s | **Price right this time**: "25 Euros, equivalent to approximately 17 Pounds" (the "17 €" of the first test came from this Pounds conversion) |
| `audio/synthetic-team-meeting-en.wav` (35 s) | 120 s | Whisper + minutes right: launch 15 Nov, Paul by 31 Oct, Marie books the room (no date said in the audio → empty, correct), budget postponed, next meeting 6 Nov 10:00. Name heard as "Sarah" instead of "Sara" |
| `audio/ami-es2004a-intro-28s.wav` (28 s) | 58 s | Transcription fine, but the **agenda points became actions** ("Get to know each other", "Tool training"…) |
| `photos/flipchart-todo-list-de.jpg` (German) | 243 s | All 7 owners and dates read correctly (year 2026 added by the model). But the tasks were **translated into French**, one badly ("Halle ausräumen" → "Austérification de la salle"); the minutes should stay in German |
| `photos/whiteboard-spring-break-en.jpg` | 182 s | Topics read, but **4 attendees invented** ("Alice, Bob, Charlie, David") and "SketchUp video → NKim" missed |
| `photos/osm-france-board-small-fr.jpg` | 203 s | Weak: topic headings used as attendees and as task owners |

**Bug found and fixed:** short typed notes (under 150 words) were not saved as meeting notes, so "write the minutes" answered "no notes yet" (both short notes files failed on the first run). Now a paste of 4+ lines and 30+ words also counts as notes.

**Still open (model quality, not fixed):** invented attendees on photos, language changed on the German flipchart, agenda items taken as actions, actions repeated as decisions. Photos still take 3–4 minutes even when small.

## 2026-10-23 · Manual test in the chat page (user)

| Test | Result |
|---|---|
| German flipchart photo, sent in the **same chat** right after the English notes test had been approved | **Wrong draft**: "Weekly team meeting" (Marie, Paul, Sara). The old English notes were still in the session, so the minutes were written from both (134 words, detected as English) and the photo was ignored |
| Same photo in a **new chat** | Right: photo read in 121 s, minutes in German, all 7 tasks with owner and date, no invented attendees |

**Fixed:** once the minutes of a chat are approved and sent, the next notes, recording or photo start a new meeting automatically (old notes and draft are dropped; the right panel shows "New meeting started"). Before approval, notes still add up, so several photos of one meeting still work. New unit test; 9 tests pass.

## Still to test

- Full 17.5-min audio recording (expected ~15 min for Whisper on this CPU)
- Photos: GLAM board (hard)
- A week of real use: the Google sign-in in "Testing" mode expires about every 7 days
