"""Train the intent classifier and choose the crisis threshold.

Usage:  python train.py

Steps
1. Load data/messages.csv and check it meets the brief (>=250 rows, >=40/class)
   and shares no message with the crisis test set (which is never trained on).
2. Compare Naive Bayes and Logistic Regression with 5-fold stratified CV.
3. Pick the model with the best macro-F1.
4. Choose the crisis threshold from out-of-fold probabilities so that
   (a) keyword OR model misses no crisis training message, and
   (b) the model alone still catches >= 90% of them (safety net for new
   wording). A safety margin is applied on top.
5. Fit on all training data and save models/intent_model.joblib.
"""
import json
import os

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import f1_score, recall_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict

import config
from core.crisis import KeywordLayer
from core.model import CRISIS, LABELS, build_pipeline
from core.text_clean import normalize

SAFETY_MARGIN = 0.8      # threshold = margin * (lowest crisis probability seen in CV)
MAX_THRESHOLD = 0.35     # never let the crisis threshold be higher than this
MODEL_ALONE_RECALL = 0.90  # model layer alone must catch >= 90% of crisis messages
SEED = 42


def load_training():
    df = pd.read_csv(os.path.join(config.BASE_DIR, "data", "messages.csv"), encoding="utf-8-sig")
    df = df.dropna(subset=["text", "label"])
    counts = df["label"].value_counts()
    assert len(df) >= 250, f"Need >= 250 messages, have {len(df)}"
    for lab in LABELS:
        assert counts.get(lab, 0) >= 40, f"Class {lab} has {counts.get(lab, 0)} < 40"

    test = pd.read_csv(os.path.join(config.BASE_DIR, "data", "crisis_test.csv"), encoding="utf-8-sig")
    overlap = set(df["text"].map(normalize)) & set(test["text"].map(normalize))
    assert not overlap, f"Crisis test messages leaked into training: {overlap}"
    return df


def choose_threshold(y, proba_crisis, kw_hit):
    """Crisis threshold for the model layer (two requirements, stricter wins).

    (a) No crisis is missed by the two-layer rule: every crisis message that
        the keyword list does NOT catch must be caught by the model.
    (b) The model must stay sensitive on its own, as the safety net for
        wording no keyword covers yet: it alone must catch at least
        MODEL_ALONE_RECALL of all crisis messages.
    Both are measured on out-of-fold (cross-validation) probabilities and a
    safety margin is applied. The lower (more sensitive) threshold is used.
    """
    crisis = y == CRISIS
    need_model = crisis & ~kw_hit
    thr_a = float(proba_crisis[need_model].min()) if need_model.any() else 1.0
    thr_b = float(np.quantile(proba_crisis[crisis], 1 - MODEL_ALONE_RECALL))
    return round(min(MAX_THRESHOLD, SAFETY_MARGIN * min(thr_a, thr_b)), 4)


def compare_models(X, y, cv, kw_hit):
    results = {}
    for kind in ["naive_bayes", "logistic_regression"]:
        pipe = build_pipeline(kind)
        proba = cross_val_predict(pipe, X, y, cv=cv, method="predict_proba")
        classes = sorted(set(y))                       # sklearn orders classes alphabetically
        pred = np.array(classes)[proba.argmax(1)]
        p_crisis = proba[:, classes.index(CRISIS)]
        thr = choose_threshold(y, p_crisis, kw_hit)
        flagged = (p_crisis >= thr) | kw_hit
        non_crisis = y != CRISIS
        results[kind] = {
            "cv_accuracy": float((pred == y).mean()),
            "cv_macro_f1": float(f1_score(y, pred, average="macro")),
            "cv_crisis_recall_argmax": float(recall_score(y == CRISIS, pred == CRISIS)),
            "threshold": thr,
            "cv_crisis_recall_two_layer": float(flagged[~non_crisis].mean()),
            "cv_false_alarm_rate_two_layer": float(flagged[non_crisis].mean()),
        }
        print(f"{kind:20s} acc={results[kind]['cv_accuracy']:.3f} "
              f"macroF1={results[kind]['cv_macro_f1']:.3f} thr={thr:.3f} "
              f"false-alarm={results[kind]['cv_false_alarm_rate_two_layer']:.3f}")
    return results


def main():
    df = load_training()
    X, y = df["text"].values, df["label"].values
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)

    print(f"Training messages: {len(df)}  per class: {df['label'].value_counts().to_dict()}")
    keywords = KeywordLayer(config.KEYWORDS_PATH)
    kw_hit = np.array([bool(keywords.hits(t)) for t in X])
    print(f"Keyword layer alone catches {kw_hit[y == CRISIS].mean():.0%} of crisis training messages")
    results = compare_models(X, y, cv, kw_hit)
    best = max(results, key=lambda k: (results[k]["cv_macro_f1"],
                                       -results[k]["cv_false_alarm_rate_two_layer"]))
    threshold = results[best]["threshold"]
    print(f"Selected model: {best}  crisis threshold: {threshold}")

    pipe = build_pipeline(best).fit(X, y)
    os.makedirs(os.path.dirname(config.MODEL_PATH), exist_ok=True)
    joblib.dump({"pipeline": pipe, "threshold": threshold, "model_name": best,
                 "labels": LABELS, "n_train": int(len(df))}, config.MODEL_PATH)

    os.makedirs(config.REPORTS_DIR, exist_ok=True)
    with open(os.path.join(config.REPORTS_DIR, "model_selection.json"), "w", encoding="utf-8") as f:
        json.dump({"selected": best, "threshold": threshold, "candidates": results,
                   "safety_margin": SAFETY_MARGIN, "model_alone_recall_target": MODEL_ALONE_RECALL, "max_threshold": MAX_THRESHOLD},
                  f, indent=2, ensure_ascii=False)
    print(f"Saved {config.MODEL_PATH}")


if __name__ == "__main__":
    main()
