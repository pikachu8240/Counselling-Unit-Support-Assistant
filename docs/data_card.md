# Data card: Counselling Assistant message dataset

| Item | Value |
|---|---|
| **File** | `data/messages.csv` (columns: `text, label, source, approved_by`) |
| **Size** | 366 messages · booking 65 · services 60 · stress 81 · crisis 82 · other 78 (brief: ≥ 250, ≥ 40 per class ✔) |
| **Labels** | `booking` (book/change/cancel a session) · `services` (questions about the unit: cost, hours, location, confidentiality) · `stress` (everyday study/social stress) · `crisis` (suicidal thoughts, self-harm, danger, abuse, harm to others, urgent calls for help) · `other` (greetings, off-topic) |
| **Languages** | ≈ 75% Egyptian Arabic, plus Modern Standard Arabic and English |
| **Separate test sets (never trained on)** | `crisis_test.csv` 36 crisis messages (pass/fail gate) · `trick_tests.csv` 24 indirect crisis messages · `false_alarm_test.csv` 40 non-crisis messages incl. hyperbole ("الامتحان ده هيموتني") |
| **Leakage check** | `train.py` refuses to train if any crisis-test message (after normalisation) appears in the training data |

## How it was collected
- **Draft version (this repository):** written by the student team to build and test the pipeline.
  Every row is marked `approved_by = PENDING_UNIT_REVIEW`.
- **Required before any pilot:** following the brief, the counselling unit writes or approves the dataset once for all teams.
  **Only specialists write crisis examples** (`source = specialist_draft` marks rows that must be replaced or approved by them);
  students may add rewordings for the four other classes (`team_rewording_v2/v3`).
- Versions: v1 (297) → v2 +45 hard negatives and crisis drafts → v3 +24 English and short-message examples (see `docs/trick_testing_log.md`).

## Privacy steps
- **No real student messages** are in the dataset. All messages are invented examples, so there are no names or identifiers.
- The live app never stores chat text, so production traffic cannot leak into the dataset by accident.
  New training data must come from the specialists, not from logs.
- Crisis examples are written without method details, on purpose.

## Known gaps
Franco-Arabic (Arabizi), Upper-Egypt / Bedouin dialect forms, sarcasm, very long messages, and messages mixing several intents.
