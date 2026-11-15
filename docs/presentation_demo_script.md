# 10-minute presentation: demo script

Before you start: `python app.py`, open http://127.0.0.1:5000. Open `instance/bookings.xlsx` in a second window
**read-only**, or close it before booking (Excel locks the file).

| Time | What to show | What to say |
|---|---|---|
| 0:00–1:00 | Problem slide | Students avoid the unit because of stigma or because they don't know how to book. This is a 24/7 front door that is **not** a therapist. |
| 1:00–1:45 | Home page | Red banner on every page (16328, unit phone, "Talk to a person"). The assistant says it is a program. |
| 1:45–3:30 | **Normal booking** | Click *Our services*, then type `قلقان من الميدتيرم` (stress answer + awareness links + Book), then *Book* and pick a day, a time and WhatsApp. Get a booking ID. Point to the note: chat messages are not saved, no name asked. |
| 3:30–5:30 | **Crisis path** | Type an indirect message: `حاسس إن الدنيا من غيري هتبقى أحسن`. The conversation stops, the crisis panel shows real contacts, and the menu is disabled. Type `الوحدة بتفتح امتى`: still in crisis mode. Click *I'm safe now* to return to chat. Also show the 🆘 button. |
| 5:30–6:30 | Staff page | Log in. The booking appears with no name. Change its status. Show the KPI cards and charts, and say that only counts are stored. Open the Excel file: Bookings / Stats / Visits / Feedback. |
| 6:30–8:30 | Evaluation page | PASS banner (100% crisis recall on 36 unseen messages). **Two layers:** keywords alone 56%, model alone 97%, together 100%. Confusion matrix, NB vs LR comparison, robustness, trick tests, false-alarm list. |
| 8:30–9:30 | Trick-testing log | Round 1 FAIL and how it was fixed. The threshold-rule lesson. The honest limitations (fresh test set needed, Arabizi not covered yet). |
| 9:30–10:00 | Wrap-up | Privacy by design, pilot only with the unit's approval, next steps. |

Backup if the live demo fails: `python -m pytest -q` (9 tests, including the crisis path and the "no chat text stored" check)
and the screenshots in `docs/screenshots/`.
