# The AI part: where it is, what it does, how to test it

## Where it lives
| File | Role |
|---|---|
| `core/text_clean.py` | **Step 1: cleaning.** `normalize()` lower-cases, removes diacritics and tatweel, unifies alef/ya/ta-marbuta/hamza forms, removes punctuation and collapses repeated letters (`مخنوووق` → `مخنوق`). `detect_language()` picks the Arabic or English reply. |
| `core/crisis.py` | **Layer 1: the specialists' keyword list.** Reads `data/crisis_keywords.txt` (124 entries). Matches on cleaned text, also inside words (`بفكر انتحر`), with typo tolerance (two swapped letters, or one missing letter in long words). |
| `core/model.py` | **Layer 2 + intent classifier.** `build_pipeline()` = TF-IDF on words (1–2 grams) + TF-IDF on characters (2–5 grams) → Logistic Regression or Naive Bayes. `Assistant.analyze()` makes the final decision; `Assistant.explain()` shows every step. |
| `train.py` | Compares Naive Bayes vs Logistic Regression (5-fold cross-validation), picks the better one, chooses the **crisis threshold** and saves `models/intent_model.joblib`. |
| `evaluate.py` | Hold-out accuracy, per-class metrics, confusion matrix, **crisis-test PASS/FAIL**, false-alarm rate, trick tests, robustness. Writes `reports/`. |
| `app.py` → `api_chat()` | Calls `assistant.analyze()` on **every message, before anything else**. |

## What it does with one message
```
message ─► normalize() ─┬─► Layer 1: keyword list hit? ───────────────┐
                        └─► Layer 2: model → P(5 classes)            │
                                       P(crisis) ≥ 0.2485 ? ──────────┤
                                                                      ▼
                               either says crisis?  ── yes ─► CRISIS screen (16328 + unit)
                                       │ no
                                       ▼
                    best of booking / services / stress / other
                    (confidence < 0.40 → show the menu instead of guessing)
```
- **Why two layers:** keywords catch explicit phrases instantly and predictably. The model catches **indirect wording** no one wrote a keyword for. On the crisis test set, keywords alone catch 56%, the model alone 97%, and both together 100%.
- **Why char n-grams:** Egyptian spelling varies (`عايز/عاوز`, `ازاي/إزاي`) and students make typos. Character pieces still match.
- **Why the threshold is low (0.2485):** it is set so no crisis training message is missed in cross-validation, and the model alone still catches ≥ 90%. A false alarm only shows phone numbers; a miss could cost a life.

## How to test it (3 ways)
1. **Staff test page:** run `python app.py`, log in at `/staff/login`, click **«جرّب الذكاء الاصطناعي»** (`/staff/try`). Type any message to see cleaning, the keyword hits, all 5 probabilities and the final decision. Nothing is stored.
2. **Command line:**
   ```bash
   python try_model.py                        # interactive
   python try_model.py "الامتحان ده هيموتني"   # one message
   python try_model.py --file my_tests.txt    # many messages + summary table
   ```
3. **Full evaluation:** `python train.py && python evaluate.py`, then open `/staff/evaluation` (confusion matrix, PASS/FAIL, trick tests, robustness).

## Test ideas (try to break it)
| Try | What should happen |
|---|---|
| Hyperbole: `الامتحان ده هيموتني`, `I could kill for a coffee` | Ideally **not** crisis (stress/other). Some still are; that is the false-alarm trade-off |
| Indirect: `وزعت حاجاتي على صحابي`, `مش هتشوفوني تاني` | **Crisis** (usually caught by the model) |
| Typos/elongation: `انتحاار`, `عايزز امووت` | **Crisis** (cleaning + typo tolerance) |
| Franco-Arabic: `3ayez amoot` | ⚠️ Probably **missed**: known gap, write it down |
| Mixed: `عايز احجز عشان مش قادر انام من القلق` | booking (or stress), never crisis |
| Off-topic: `مين كسب الماتش` | other → the assistant says it only helps with the unit |

Every crisis message that is **missed** must be recorded in `docs/trick_testing_log.md` and fixed: a keyword the specialists approve, and/or new training rewordings. Then rerun `train.py` and `evaluate.py` (GitHub does this automatically after a push).
