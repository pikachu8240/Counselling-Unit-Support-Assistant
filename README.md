# Counselling Unit Support Assistant (AI Lab, Project 2)

A 24/7 "front door" for the faculty's counselling and guidance unit. It explains the unit's services, books a session
**without asking for a name**, shows awareness articles, and at **any sign of crisis** stops the conversation and shows
the unit's contacts and the national mental-health hotline **16328**. It is not a therapist: it never diagnoses and
never gives treatment advice.

## Quick start (Windows / VS Code)
```bash
python -m venv venv
venv\Scripts\activate            # macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
python train.py                  # compares Naive Bayes vs Logistic Regression, picks the crisis threshold
python evaluate.py               # metrics, confusion matrix, crisis-recall PASS/FAIL gate
python app.py                    # http://127.0.0.1:5000
python -m pytest -q              # 9 automated tests
```
Staff page: `/staff/login`, user `staff`, password `change-me-now`. **Change it before any real use:**
```bash
python -c "from werkzeug.security import generate_password_hash as g; print(g('NEW-PASSWORD'))"
set STAFF_PASSWORD_HASH=<output>        &  set SECRET_KEY=<long random string>
```
Replace the placeholder unit contacts in `config.py` (`UNIT = {...}`).

## Brief requirements → where they are
| Requirement | Implementation |
|---|---|
| Welcome, chat (menu + free text), booking form, awareness pages, staff page with login | `templates/`, `app.py` routes `/`, `/chat`, `/awareness`, `/staff` |
| Red emergency banner on every page (unit phone, 16328, "Talk to a person") | `templates/base.html` |
| Assistant introduces itself as a program | chat intro, home page, footer |
| Intent classifier, 5 classes, NB vs LR | `core/model.py`, `train.py` (5-fold CV comparison; LR selected) |
| Two-layer crisis check (keywords OR model), threshold so no crisis is missed | `core/crisis.py`, `Assistant.analyze()`, `train.choose_threshold()` |
| Crisis check runs first on every message | `app.api_chat()` |
| ≥ 250 messages, ≥ 40 per class; separate crisis test set ≥ 30 | `data/messages.csv` (366), `data/crisis_test.csv` (36), leakage check in `train.py` |
| Accuracy, confusion matrix, crisis recall = 100% (pass/fail), false-alarm rate | `evaluate.py` → `reports/`, page `/staff/evaluation` |
| "Trick" testing, failures recorded and fixed | `data/trick_tests.csv`, `docs/trick_testing_log.md` |
| `bookings.xlsx`: Bookings / Stats / Visits; no names, no chat text | `core/excel_db.py` (single writer `log_to_excel()`, schema-enforced) |
| One-page privacy statement | `docs/privacy_statement.md`, page `/privacy` |
| Conversation flowchart | `docs/conversation_flowchart.png` (source `flowchart.dot`) |
| Data card | `docs/data_card.md` |
| Presentation (crisis path + normal booking) | `docs/presentation_demo_script.md` |
| Bonus: Egyptian dialect | dialect-heavy data, Arabic normalisation, char n-grams, typo-tolerant keywords |
| Bonus: accessibility | font size, high contrast, skip link, `aria-live` chat, keyboard focus, RTL, mobile layout |

## Results (`python evaluate.py`)
| Metric | Value |
|---|---|
| Crisis recall on crisis test set (36, unseen) | **100%: PASS** (keywords alone 56%, model alone 97%) |
| Trick tests (24 indirect messages) | 100% |
| Hold-out accuracy / macro-F1 (two-layer) | 0.772 / 0.768 |
| False-alarm rate | 15.5% hold-out non-crisis, 25% on the hard hyperbole set |
| Robustness (elongation, punctuation, typo, no-hamza) | 100% crisis recall in all four |

## Project structure
```
app.py              Flask app (pages, chat API, booking, staff area)
config.py           contacts, staff login, paths
train.py            model comparison + threshold selection
evaluate.py         full evaluation + PASS/FAIL gate
core/text_clean.py  Arabic/English normalisation (re)
core/crisis.py      Layer 1: specialists' keyword list (typo-tolerant)
core/model.py       Layer 2 + intent classifier, Assistant.analyze()
core/content.py     approved responses + awareness articles (drafts for unit approval)
core/excel_db.py    bookings.xlsx, single write function log_to_excel()
data/               training data, test sets, crisis_keywords.txt
docs/               data card, privacy statement, flowchart, trick-testing log, demo script, screenshots
reports/            generated metrics, confusion matrix, per-message results
tests/              pytest suite
instance/           bookings.xlsx (created at runtime, stays on the unit's computer)
```

## GitHub sync and the project file
- **`Counselling-Unit-Support-Assistant.md`** is the living project document: live data statistics, latest results,
  file inventory and a **change log with the date and time of every change**. It is regenerated automatically.
- Every push to `main` runs `.github/workflows/update-project.yml`: it retrains and re-evaluates when data or model code
  changed, then rebuilds the project MD and commits it.
- Local changes: double-click **`sync.bat`** (Windows) or run `./sync.sh`, type a short description, done.
- `instance/bookings.xlsx` (real bookings) is git-ignored and never leaves the unit's computer.

## Important before any pilot
All responses, awareness texts, crisis examples and keywords are **drafts** and must be approved by the unit's specialists.
The unit should also write a **fresh crisis test set** for final acceptance (see the limitations in `docs/trick_testing_log.md`).
Deploy only with the unit's approval.
