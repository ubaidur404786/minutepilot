# Quick test data

Very small files for fast tests (a few seconds to about two minutes each, instead of 5–15 minutes
with the full public files). Where each file comes from and its license: `../SOURCES.md`, section *Quick test set*.

Run them all (stack running, models downloaded):
```
python test-data/quick/run_quick_tests.py           # everything
python test-data/quick/run_quick_tests.py notes     # only names containing "notes" (also: audio, photo)
```
Or by hand in the chat page (http://localhost:8000): paste a notes file, or attach an audio file or photo
with **Attach audio / photos**, and write "Please write the minutes of this meeting."
Nothing is approved by the script: no email, task or event is created.

## Files and what a good answer contains

| File | Size | What is in it | A good draft has |
|---|---|---|---|
| `notes/team-meeting-en.txt` | 10 lines | Synthetic English team meeting | Decision: website launch on 15 Nov. Actions: Paul → design to printer by 31 Oct; Marie → book room by 7 Nov; Sara → check translations before 10 Nov. Postponed: party budget. Next meeting 2026-11-06 10:00 |
| `notes/reunion-cse-fr.txt` | 8 lines | Synthetic French CSE meeting | Minutes **in French**. Décision : arbre de Noël le 13 décembre, budget 2 000 €. Actions : Julie → salle avant le 7 nov. ; Karim → 3 devis traiteur pour le 14 nov. Reporté : chèques vacances. Prochaine réunion 2026-11-20 14:00 |
| `notes/ami-es2004a-price-excerpt.txt` | 383 words | Real meeting excerpt (AMI ES2004a, QMSum transcript) | Selling price **25 Euros** (the 17 is the same price in Pounds: a trap), production cost 12.50 €, profit aim 50 million €, market: international, all ages |
| `audio/synthetic-team-meeting-en.wav` | 35 s | The English team meeting read by two Windows voices | Same facts as the English notes (launch 15 Nov; Paul → printer by 31 Oct; Marie → room; budget postponed; next meeting 6 Nov 10:00) |
| `audio/ami-es2004a-intro-28s.wav` | 28 s | Real meeting (AMI ES2004a, 0:20–0:48 of the 90 s clip) | Speaker: Sarah, project manager, first meeting; agenda: get to know each other, tool training, project plan, own ideas; 25 minutes. Few or no actions (it is only the intro) |
| `photos/flipchart-todo-list-de.jpg` | 580×800 | Handwritten **German** to-do table on a flipchart (was / wer / bis) | 7 actions with owners and dates: Halle ausräumen – Müller – 29.9.; Band engagieren – Huber – 1.4. (ticked); Bühnentechnik besorgen – Mayer – 15.4.; Catering bestellen – Metzger – 15.8.; Produktpräsentation erstellen – Chef – 1.7.; Tische, Stühle aufstellen – Abt. Logistik – 30.9.; Deko aufhängen – Blum – 30.9. (no year on the board) |
| `photos/whiteboard-spring-break-en.jpg` | 1024×768 | English whiteboard list, blue marker, slight angle | "Spring Break" list: "Coke" chart – Group 1, "Page Turner RGM", CDIO, token symbols → keywords, "photo booth", forces keywords, mechanism symbols; "SketchUp video → NKim" |
| `photos/osm-france-board-small-fr.jpg` | 768×1024 | The OSM France board photo (French), made smaller | Topic headings (Budget, Groupes locaux, Visibilité, Durabilité…). Mostly topics, few or no actions |

The real results of these tests are in `docs/test-results.md`.
