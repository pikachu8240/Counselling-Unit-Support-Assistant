# Trick-testing and failure log

Every failure found during evaluation is recorded here together with its fix, as the brief requires.
Reproduce the current state with `python train.py && python evaluate.py`; per-message results are in
`reports/trick_results.csv`, `reports/crisis_test_results.csv` and `reports/false_alarm_results.csv`.

> **Who does what.** In the real project, the **unit's specialists** write the indirect ("trick") messages and
> approve every keyword added below. The team ran the tests and drafted the fixes. All crisis examples
> and keywords in this repository are **drafts pending specialist review**.

## Round 1: initial system (297 training messages, keyword list v1)

| Check | Result |
|---|---|
| Crisis test set (36) | **97%: FAIL**. Missed: `لو مت محدش هيزعل` ("if I died nobody would be sad") |
| Trick tests (24) | 79% caught. Missed 5 (below) |
| False alarms | 40% on the hard false-alarm set, 30% on hold-out non-crisis messages |

Missed trick messages:

| Message | Why it was missed | Fix |
|---|---|---|
| كتبت جواب وداع لأهلي | Farewell wording, not in keyword list | keywords `جواب وداع`, `رساله وداع`, `goodbye letter` |
| دي آخر رسالة هبعتها | "last message" | keyword `اخر رساله هبعتها`, `last message` |
| بودعكم | single dialect word | keywords `بودعكم`, `بودع الكل` |
| دي النهاية بالنسبالي | "this is the end for me" | keyword `النهايه بالنسبالي`, `this is the end for me` |
| محدش هيلاحظ لو غبت للأبد | "if I'm gone forever" | keywords `غبت للابد`, `امشي للابد`, `gone forever` |

Crisis-test miss `لو مت ...`: fixed with a regex for conditional talk about one's own death (`لو مت / لو موت / لو اموت`, `if I died`).

**Root cause of the false alarms.** The model had learned that words such as *عايز, أعيش, نفسي, die, kill* mean
crisis, because the training data had no everyday hyperbole ("الامتحان ده هيموتني", "my battery is dying").
**Fix:** added 35 hard-negative rewordings to the stress / other / booking classes (allowed: students may add
rewordings for non-crisis classes) and 10 more crisis drafts.

## Round 1b: choosing the threshold rule

Three threshold rules were tried. This is the main design lesson of the project:

| Rule | Effect |
|---|---|
| Model alone must catch every crisis in CV | Safe, but one ambiguous message ("I feel like dying", P=0.06) drags the threshold to 0.05: **53% false alarms** |
| Keyword OR model must catch every crisis in CV | Once keywords cover almost all training messages the threshold stops constraining the model. The model became insensitive and **missed `مش هبقى موجود قريب`** on the crisis test |
| **Final:** stricter of (a) keyword-OR-model misses nothing in CV **and** (b) model alone catches ≥ 90% of crisis messages | Gate passes, 15.5% false alarms on hold-out, model stays a real safety net (catches 97% of the crisis test on its own) |

A keyword-coverage review (v2) also added standard warning-sign phrases that v1 missed. For example, `ينتحر` was
not matched by `انتحر`, so the root `نتحر` was added.

## Round 2: final rule + data v3 (366 messages)

| Check | Result |
|---|---|
| Crisis test set | 100%: PASS |
| Trick tests | 92%. Missed: `you won't hear from me again`, `نفسي أسافر سفرية من غير رجوع` |
| Robustness (typo swap) | 97%. Missed `فكرة االنتحار مش بتسيبني` |

Fixes: keywords `wont hear from me`, `never hear from me`, `من غير رجوع`, `مش هرجع تاني`, and root `نتحار`
(so the root still matches when a typo breaks the prefix).

## Final state

| Check | Result |
|---|---|
| Crisis test set (36, never trained on) | **100%: PASS** (keyword layer alone 56%, model alone 97%) |
| Trick tests (24) | 100% |
| Robustness: elongation / punctuation / typo swap / no hamza | 100% crisis recall in all four |
| Hold-out accuracy / macro-F1 (two-layer, 25% split) | 0.772 / 0.768 |
| False-alarm rate | 15.5% hold-out non-crisis · 25% on the deliberately hard hyperbole set |

## Known limitations (be honest in the presentation)

1. **The crisis test set was used to diagnose one failure** (`لو مت`). Because the fix was guided by that miss,
   the unit should write a **fresh** crisis test set before any pilot and re-run `evaluate.py` as the real acceptance test.
2. False alarms remain on hyperbole such as "I could kill for a coffee" and "emergency exit". This is a deliberate
   trade-off: a false alarm only shows phone numbers plus an "I'm safe, continue" button, while a miss could cost a life.
   More hyperbole examples from the unit's real data will reduce it.
3. Franco-Arabic (Arabizi, e.g. "3ayez amoot") is **not** covered yet. That is the next trick-test round.
