"""Evaluate the assistant.  Usage:  python evaluate.py   (run train.py first)

Produces in reports/:
  metrics.json             all numbers shown on the staff Evaluation page
  confusion_matrix.png     5x5 confusion matrix on the hold-out split
  crisis_test_results.csv  per-message result on the crisis test set
  trick_results.csv        per-message result of the "trick" (indirect) tests
  false_alarm_results.csv  per-message result on non-crisis messages

PASS/FAIL gate: crisis recall on data/crisis_test.csv must be 100%.
The script exits with code 1 when the gate fails.
"""
import json
import os
import random
import sys
import tempfile

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import (accuracy_score, classification_report,
                             confusion_matrix)
from sklearn.model_selection import StratifiedKFold, cross_val_predict, train_test_split

import config
from core.crisis import KeywordLayer
from core.model import CRISIS, LABELS, Assistant, build_pipeline
from train import choose_threshold, load_training

SEED = 42
R = config.REPORTS_DIR


def read(name):
    return pd.read_csv(os.path.join(config.BASE_DIR, "data", name), encoding="utf-8-sig")


def holdout_assistant(train_df, kind):
    """Train a fresh model on the training split only (threshold from its own CV)."""
    X, y = train_df["text"].values, train_df["label"].values
    kw = KeywordLayer(config.KEYWORDS_PATH)
    kw_hit = np.array([bool(kw.hits(t)) for t in X])
    cv = StratifiedKFold(5, shuffle=True, random_state=SEED)
    proba = cross_val_predict(build_pipeline(kind), X, y, cv=cv, method="predict_proba")
    p_crisis = proba[:, sorted(set(y)).index(CRISIS)]
    thr = choose_threshold(y, p_crisis, kw_hit)
    pipe = build_pipeline(kind).fit(X, y)
    tmp = os.path.join(tempfile.gettempdir(), "holdout_model.joblib")
    joblib.dump({"pipeline": pipe, "threshold": thr, "model_name": kind}, tmp)
    return Assistant(tmp, config.KEYWORDS_PATH, config.LOW_CONFIDENCE)


def run_set(assistant, texts):
    rows = []
    for t in texts:
        a = assistant.analyze(t)
        rows.append({"text": t, "flagged_crisis": a["is_crisis"], "layer": a["layer"] or "",
                     "p_crisis": round(a["p_crisis"], 3),
                     "keyword_hits": "; ".join(a["keyword_hits"]),
                     "predicted_intent": a["intent"]})
    return pd.DataFrame(rows)


# --- robustness perturbations (typing variations a real student might make)
def p_elongate(t):
    w = t.split()
    if not w:
        return t
    i = random.randrange(len(w))
    if len(w[i]) > 2:
        w[i] = w[i][:-1] + w[i][-2] * 3 + w[i][-1]
    return " ".join(w)


def p_punct(t):
    return t + " ؟!!..." if random.random() < .5 else "... " + t + " !!"


def p_typo(t):
    """swap two adjacent letters inside one random long word"""
    w = t.split()
    long_words = [i for i, x in enumerate(w) if len(x) > 4]
    if not long_words:
        return t
    i = random.choice(long_words)
    j = random.randrange(1, len(w[i]) - 2)
    s = list(w[i]); s[j], s[j + 1] = s[j + 1], s[j]
    w[i] = "".join(s)
    return " ".join(w)


def p_no_hamza(t):
    return t.replace("أ", "ا").replace("إ", "ا").replace("ة", "ه").replace("ى", "ي")


PERTURBATIONS = {"elongation": p_elongate, "punctuation": p_punct,
                 "typo_swap": p_typo, "no_hamza": p_no_hamza}


def main():
    random.seed(SEED)
    os.makedirs(R, exist_ok=True)
    bundle = joblib.load(config.MODEL_PATH)
    kind = bundle["model_name"]
    deployed = Assistant(config.MODEL_PATH, config.KEYWORDS_PATH, config.LOW_CONFIDENCE)
    metrics = {"model": kind, "threshold": bundle["threshold"],
               "n_train_messages": bundle.get("n_train")}

    # ---------------------------------------------------------- 1. hold-out
    df = load_training()
    tr, te = train_test_split(df, test_size=0.25, stratify=df["label"], random_state=SEED)
    ho = holdout_assistant(tr, kind)
    y_true = te["label"].tolist()
    y_pred = [ho.analyze(t)["intent"] for t in te["text"]]
    y_model_only = list(ho.pipeline.predict(te["text"]))
    rep = classification_report(y_true, y_pred, labels=LABELS, output_dict=True, zero_division=0)
    metrics["holdout"] = {
        "n_test": len(te),
        "accuracy_two_layer": accuracy_score(y_true, y_pred),
        "accuracy_model_only": accuracy_score(y_true, y_model_only),
        "per_class": {l: {k: round(rep[l][k], 3) for k in ("precision", "recall", "f1-score", "support")}
                      for l in LABELS},
        "macro_f1": round(rep["macro avg"]["f1-score"], 3),
    }
    cm = confusion_matrix(y_true, y_pred, labels=LABELS)
    fig, ax = plt.subplots(figsize=(6.2, 5.2), dpi=130)
    ax.imshow(cm, cmap="Blues")
    ax.set_xticks(range(5), LABELS, rotation=30, ha="right"); ax.set_yticks(range(5), LABELS)
    for i in range(5):
        for j in range(5):
            ax.text(j, i, cm[i, j], ha="center", va="center",
                    color="white" if cm[i, j] > cm.max() / 2 else "#1f2937", fontsize=12)
    ax.set_xlabel("Predicted (two-layer system)"); ax.set_ylabel("True label")
    ax.set_title(f"Confusion matrix – hold-out 25% ({kind})")
    fig.tight_layout(); fig.savefig(os.path.join(R, "confusion_matrix.png")); plt.close(fig)
    metrics["holdout"]["confusion_matrix"] = cm.tolist()

    # ---------------------------------------------------------- 2. crisis test set (gate)
    ct = run_set(deployed, read("crisis_test.csv")["text"])
    ct.to_csv(os.path.join(R, "crisis_test_results.csv"), index=False, encoding="utf-8-sig")
    recall = float(ct["flagged_crisis"].mean())
    metrics["crisis_test"] = {
        "n": len(ct), "recall": recall, "missed": ct.loc[~ct.flagged_crisis, "text"].tolist(),
        "caught_by": ct["layer"].value_counts().to_dict(),
        "keyword_layer_alone_recall": float(ct["layer"].isin(["keyword", "both"]).mean()),
        "model_layer_alone_recall": float(ct["layer"].isin(["model", "both"]).mean()),
        "PASS": recall == 1.0,
    }

    # ---------------------------------------------------------- 3. false alarms
    fa = run_set(deployed, read("false_alarm_test.csv")["text"])
    fa.to_csv(os.path.join(R, "false_alarm_results.csv"), index=False, encoding="utf-8-sig")
    ho_non = [t for t, l in zip(te["text"], y_true) if l != CRISIS]
    ho_flags = [ho.analyze(t)["is_crisis"] for t in ho_non]
    metrics["false_alarms"] = {
        "false_alarm_set_n": len(fa),
        "false_alarm_set_rate": float(fa["flagged_crisis"].mean()),
        "false_alarm_set_flagged": fa.loc[fa.flagged_crisis, "text"].tolist(),
        "holdout_non_crisis_n": len(ho_non),
        "holdout_non_crisis_rate": float(np.mean(ho_flags)),
    }

    # ---------------------------------------------------------- 4. trick tests
    tk = run_set(deployed, read("trick_tests.csv")["text"])
    tk.to_csv(os.path.join(R, "trick_results.csv"), index=False, encoding="utf-8-sig")
    metrics["trick_tests"] = {"n": len(tk), "recall": float(tk["flagged_crisis"].mean()),
                              "missed": tk.loc[~tk.flagged_crisis, "text"].tolist()}

    # ---------------------------------------------------------- 5. robustness
    crisis_texts = read("crisis_test.csv")["text"].tolist()
    rob = {}
    for name, fn in PERTURBATIONS.items():
        pert_c = [fn(t) for t in crisis_texts]
        pert_h = [fn(t) for t in te["text"]]
        rob[name] = {
            "crisis_recall": float(np.mean([deployed.analyze(t)["is_crisis"] for t in pert_c])),
            "holdout_accuracy": float(np.mean([ho.analyze(t)["intent"] == l
                                               for t, l in zip(pert_h, y_true)])),
            "missed_crisis": [t for t in pert_c if not deployed.analyze(t)["is_crisis"]],
        }
    metrics["robustness"] = rob

    with open(os.path.join(R, "metrics.json"), "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)

    # ---------------------------------------------------------- summary
    h = metrics["holdout"]
    print(f"Hold-out accuracy (two-layer): {h['accuracy_two_layer']:.3f}   macro-F1: {h['macro_f1']}")
    print(f"Crisis test recall: {recall:.0%}  ({len(ct)} messages)  -> "
          f"{'PASS' if recall == 1 else 'FAIL'}")
    print(f"False-alarm rate: {metrics['false_alarms']['false_alarm_set_rate']:.1%} on the "
          f"false-alarm set, {metrics['false_alarms']['holdout_non_crisis_rate']:.1%} on hold-out non-crisis")
    print(f"Trick tests: {metrics['trick_tests']['recall']:.0%} caught; missed: {metrics['trick_tests']['missed']}")
    for k, v in rob.items():
        print(f"Robustness {k:12s} crisis recall {v['crisis_recall']:.0%}  accuracy {v['holdout_accuracy']:.3f}")
    if recall < 1.0:
        print("GATE FAILED – missed:", metrics["crisis_test"]["missed"])
        sys.exit(1)


if __name__ == "__main__":
    main()
