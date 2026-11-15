"""Generate Counselling-Unit-Support-Assistant.md, the single living document of the project.

It is rebuilt automatically by GitHub Actions on every push (and by sync.bat / sync.sh locally),
so it always reflects the CURRENT repository:
  * overview, how to run, requirement map
  * live dataset statistics (counts per class, test sets, keywords)
  * latest evaluation results (reports/metrics.json)
  * full file inventory with sizes and last-change time
  * complete change log: every commit with date, time (Cairo), author, message and files changed

Usage:  python tools/build_project_md.py        (standard library only)
"""
import csv
import json
import os
import subprocess
from collections import Counter
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "Counselling-Unit-Support-Assistant.md")
CAIRO = timezone(timedelta(hours=2))   # Egypt (EET, no DST)
MD_NAME = os.path.basename(OUT)
SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", "venv", "instance", ".github"}


def now_cairo():
    return datetime.now(CAIRO).strftime("%Y-%m-%d %H:%M")


def git(*args):
    try:
        return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True,
                              encoding="utf-8", check=True).stdout
    except Exception:
        return ""


def to_cairo(iso):
    try:
        return datetime.fromisoformat(iso).astimezone(CAIRO)
    except ValueError:
        return None


def read_csv(name):
    p = os.path.join(ROOT, "data", name)
    if not os.path.exists(p):
        return []
    with open(p, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def human(n):
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


# ------------------------------------------------------------------ sections
def section_data():
    rows = read_csv("messages.csv")
    c = Counter(r["label"] for r in rows)
    src = Counter(r.get("source", "") for r in rows)
    pending = sum(1 for r in rows if r.get("approved_by", "") == "PENDING_UNIT_REVIEW")
    kw_path = os.path.join(ROOT, "data", "crisis_keywords.txt")
    kws = []
    if os.path.exists(kw_path):
        kws = [l.strip() for l in open(kw_path, encoding="utf-8")
               if l.strip() and not l.strip().startswith("#")]
    lines = [
        "| Dataset | File | Messages | Notes |",
        "|---|---|---|---|",
        f"| Training data | `data/messages.csv` | **{len(rows)}** | "
        + " · ".join(f"{k} {v}" for k, v in sorted(c.items())) + " |",
        f"| Crisis test set (never trained on, PASS/FAIL gate) | `data/crisis_test.csv` | {len(read_csv('crisis_test.csv'))} | all `crisis` |",
        f"| Trick tests (indirect wording) | `data/trick_tests.csv` | {len(read_csv('trick_tests.csv'))} | all `crisis` |",
        f"| False-alarm set (non-crisis, hyperbole) | `data/false_alarm_test.csv` | {len(read_csv('false_alarm_test.csv'))} | all `not_crisis` |",
        f"| Crisis keyword list (Layer 1) | `data/crisis_keywords.txt` | {len(kws)} entries | owned by the unit's specialists |",
        "",
        f"Brief check: ≥ 250 messages → **{'✅' if len(rows) >= 250 else '❌'}** · "
        f"≥ 40 per class → **{'✅' if c and min(c.values()) >= 40 else '❌'}** · "
        f"crisis test ≥ 30 → **{'✅' if len(read_csv('crisis_test.csv')) >= 30 else '❌'}**",
        "",
        f"Sources: " + ", ".join(f"`{k}` {v}" for k, v in sorted(src.items()))
        + f" · rows still pending specialist approval: **{pending}**",
    ]
    return "\n".join(lines)


def section_results():
    p = os.path.join(ROOT, "reports", "metrics.json")
    if not os.path.exists(p):
        return "_No evaluation yet. Run `python train.py && python evaluate.py`._"
    m = json.load(open(p, encoding="utf-8"))
    mt = datetime.fromtimestamp(os.path.getmtime(p), CAIRO).strftime("%Y-%m-%d %H:%M")
    ct, fa, h = m["crisis_test"], m["false_alarms"], m["holdout"]
    out = [
        f"_From `reports/metrics.json` (evaluation generated {mt} Cairo)._",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| **Crisis recall on crisis test set (pass/fail)** | **{ct['recall']:.0%}: {'PASS ✅' if ct['PASS'] else 'FAIL ❌'}** ({ct['n']} messages) |",
        f"| Caught by keyword layer alone / model alone | {ct['keyword_layer_alone_recall']:.0%} / {ct['model_layer_alone_recall']:.0%} |",
        f"| Selected model / crisis threshold | {m['model']} / {m['threshold']} |",
        f"| Hold-out accuracy (two-layer) / macro-F1 | {h['accuracy_two_layer']:.3f} / {h['macro_f1']} |",
        f"| False-alarm rate: hold-out non-crisis | {fa['holdout_non_crisis_rate']:.1%} |",
        f"| False-alarm rate: hard hyperbole set | {fa['false_alarm_set_rate']:.1%} |",
        f"| Trick tests caught | {m['trick_tests']['recall']:.0%} of {m['trick_tests']['n']} |",
        "",
        "Per class (hold-out):",
        "",
        "| Class | Precision | Recall | F1 | n |",
        "|---|---|---|---|---|",
    ]
    for k, r in h["per_class"].items():
        out.append(f"| {k} | {r['precision']} | {r['recall']} | {r['f1-score']} | {int(r['support'])} |")
    out += ["", "Robustness (crisis recall under perturbation): "
            + " · ".join(f"{k} {v['crisis_recall']:.0%}" for k, v in m["robustness"].items())]
    if ct["missed"]:
        out += ["", "⚠️ Missed crisis messages: " + "; ".join(ct["missed"])]
    out += ["", "![Confusion matrix](reports/confusion_matrix.png)"]
    return "\n".join(out)


def section_files():
    # last-change time per file from git
    last = {}
    log = git("log", "--name-only", "--format=@@%cI")
    current = None
    for line in log.splitlines():
        if line.startswith("@@"):
            current = line[2:]
        elif line.strip() and line not in last:
            last[line] = current
    rows = ["| File | Size | Last changed (Cairo) |", "|---|---|---|"]
    total = 0
    for d, dirs, files in os.walk(ROOT):
        dirs[:] = sorted(x for x in dirs if x not in SKIP_DIRS)
        for f in sorted(files):
            full = os.path.join(d, f)
            rel = os.path.relpath(full, ROOT).replace(os.sep, "/")
            if rel == MD_NAME or f.endswith(".pyc"):
                continue
            size = os.path.getsize(full)
            total += size
            t = to_cairo(last[rel]).strftime("%Y-%m-%d %H:%M") if rel in last and to_cairo(last[rel]) else "not committed yet"
            rows.append(f"| `{rel}` | {human(size)} | {t} |")
    rows.append(f"| **Total** | **{human(total)}** | |")
    return "\n".join(rows)


def section_changelog():
    sep = "\x1f"
    log = git("log", f"--format=%H{sep}%cI{sep}%an{sep}%s", "--name-status")
    if not log.strip():
        return "_No commits yet._"
    entries, cur = [], None
    for line in log.splitlines():
        if sep in line:
            h, iso, author, subject = line.split(sep, 3)
            cur = {"h": h[:7], "t": to_cairo(iso), "a": author, "s": subject, "files": []}
            entries.append(cur)
        elif line.strip() and cur is not None:
            parts = line.split("\t")
            status = {"A": "added", "M": "modified", "D": "deleted"}.get(parts[0][:1], parts[0])
            if parts[-1] != MD_NAME:
                cur["files"].append(f"{status} `{parts[-1]}`")
    out = [f"Total changes recorded: **{len(entries)}** (newest first, times in Cairo, UTC+2)", ""]
    for e in entries:
        if e["s"].startswith("docs: auto-update project MD") and not e["files"]:
            continue
        out.append(f"### {e['t']:%Y-%m-%d} · {e['t']:%H:%M} | {e['s']}")
        out.append(f"`{e['h']}` by {e['a']}")
        if e["files"]:
            shown = e["files"][:25]
            out.append("")
            out += [f"- {x}" for x in shown]
            if len(e["files"]) > 25:
                out.append(f"- … and {len(e['files']) - 25} more files")
        out.append("")
    return "\n".join(out)


STATIC_TOP = """# Counselling Unit Support Assistant (AI Lab, Project 2)

> **Last updated: {updated} (Cairo time)**. This file is regenerated automatically on every change pushed to the repository.

A 24/7 "front door" for the faculty's counselling and guidance unit. It explains the unit's services, books a session
**without asking for a name**, shows awareness articles, and at **any sign of crisis** stops the conversation and shows
the unit's contacts and the national mental-health hotline **16328**. It is not a therapist: it never diagnoses and never
gives treatment advice.

## Contents
1. [Quick start](#1-quick-start)
2. [How it works](#2-how-it-works)
3. [Brief requirements → implementation](#3-brief-requirements--implementation)
4. [Data (live statistics)](#4-data-live-statistics)
5. [Latest results](#5-latest-results)
6. [Privacy](#6-privacy)
7. [How updates work (GitHub sync)](#7-how-updates-work-github-sync)
8. [Documents](#8-documents)
9. [File inventory](#9-file-inventory)
10. [Change log (every change with date and time)](#10-change-log-every-change-with-date-and-time)

## 1. Quick start
```bash
git clone https://github.com/pikachu8240/Counselling-Unit-Support-Assistant.git
cd Counselling-Unit-Support-Assistant
python -m venv venv && venv\\Scripts\\activate      # macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
python train.py        # NB vs LR comparison + crisis threshold
python evaluate.py     # metrics + PASS/FAIL gate
python app.py          # http://127.0.0.1:5000
python -m pytest -q    # automated tests
```
Staff page: `/staff/login`. Default user `staff` / password `change-me-now` (change via `STAFF_PASSWORD_HASH`, see README).
Replace the placeholder unit contacts in `config.py`.

## 2. How it works
![Conversation flowchart](docs/conversation_flowchart.png)

1. Every page shows a red emergency banner (16328, unit phone, "Talk to a person"). The assistant says it is a program.
2. **Every message is checked for crisis first**, with two layers:
   **Layer 1** is the specialists' keyword list (normalised Arabic/English, typo-tolerant) and **Layer 2** is the intent
   model's P(crisis) ≥ threshold. If either fires, the conversation stops and real contacts are shown.
3. Otherwise the message is classified as booking / services / stress / other and answered **only** from approved content,
   or the booking form opens (day, time, contact method, contact; no name).
4. Staff log in to see bookings and anonymous counts only.

## 3. Brief requirements → implementation
| Requirement | Where |
|---|---|
| Welcome, chat (menu + free text), booking form, awareness pages, staff page with login | `app.py`, `templates/` |
| Intent classifier, 5 classes, Naive Bayes vs Logistic Regression | `core/model.py`, `train.py` |
| Two-layer crisis check, threshold so no crisis is missed | `core/crisis.py`, `train.choose_threshold()` |
| ≥ 250 messages / ≥ 40 per class / separate crisis test ≥ 30 | `data/` (see section 4) |
| Accuracy, confusion matrix, crisis recall 100% gate, false-alarm rate | `evaluate.py`, `reports/`, page `/staff/evaluation` |
| Trick testing, failures recorded and fixed | `data/trick_tests.csv`, `docs/trick_testing_log.md` |
| `bookings.xlsx` (Bookings / Stats / Visits), no names, no chat text | `core/excel_db.py`, single writer `log_to_excel()` |
| Privacy statement · data card · flowchart · demo script | `docs/` |
| Bonus: Egyptian dialect, accessibility | Arabic normalisation + char n-grams; font size, contrast, ARIA, RTL, mobile |
"""

STATIC_MID = """## 6. Privacy
- Stored (in `instance/bookings.xlsx` on the unit's computer **only**, never in this repository): booking ID, request time,
  preferred day/time, contact method, contact, status · daily intent totals · page visits (page + date) · helpful yes/no.
- **Never stored:** names, chat text, IP, device or location. `log_to_excel()` refuses any field outside this schema.
- `instance/` is git-ignored on purpose, so real student bookings can never be pushed to GitHub.
- Full statement: [`docs/privacy_statement.md`](docs/privacy_statement.md)

## 7. How updates work (GitHub sync)
- **Any change pushed to `main`** (code, interface, data, docs) triggers the GitHub Action
  `.github/workflows/update-project.yml`, which:
  1. retrains and re-evaluates the model **if data or model code changed** and commits the new `models/` and `reports/`;
  2. regenerates **this file** (statistics, results, file inventory, change log with date and time) and commits it.
- From your laptop: run **`sync.bat`** (Windows) or **`./sync.sh`**. It asks for a short description, commits everything,
  pushes, and the Action updates this file within about a minute.
- To share the project: **Code → Download ZIP** on GitHub, or `git clone`. Everything (data, model, reports, docs) is included.

## 8. Documents
| Document | Content |
|---|---|
| [`README.md`](README.md) | Setup and structure |
| [`docs/data_card.md`](docs/data_card.md) | Data source, size, labels, collection, privacy |
| [`docs/privacy_statement.md`](docs/privacy_statement.md) | One-page privacy statement |
| [`docs/trick_testing_log.md`](docs/trick_testing_log.md) | Every failure found and how it was fixed |
| [`docs/presentation_demo_script.md`](docs/presentation_demo_script.md) | 10-minute demo plan |
| [`docs/conversation_flowchart.png`](docs/conversation_flowchart.png) | Conversation flowchart (source `flowchart.dot`) |
| [`docs/screenshots/`](docs/screenshots) | Screenshots of every page |
"""


def build():
    md = "\n\n".join([
        STATIC_TOP.format(updated=now_cairo()).rstrip(),
        "## 4. Data (live statistics)\n" + section_data(),
        "## 5. Latest results\n" + section_results(),
        STATIC_MID.rstrip(),
        "## 9. File inventory\n" + section_files(),
        "## 10. Change log (every change with date and time)\n" + section_changelog(),
    ]) + "\n"
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(md)
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    build()
