"""Layer 2 of the crisis check + the 5-class intent classifier.

The classifier is a scikit-learn Pipeline (TF-IDF on words + character
n-grams -> Naive Bayes or Logistic Regression). Character n-grams make the
model tolerant of Egyptian-dialect spelling variation and typos.

Decision rule (two layers, OR):
    crisis  <=>  keyword_layer_hit  OR  P(crisis) >= threshold
The threshold is chosen in train.py so that, in cross-validation, the model
alone misses no crisis example (the keyword layer is an extra safety net).
"""
import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import ComplementNB
from sklearn.pipeline import FeatureUnion, Pipeline

from .crisis import KeywordLayer
from .text_clean import normalize

LABELS = ["booking", "services", "stress", "crisis", "other"]
CRISIS = "crisis"


def build_pipeline(kind: str) -> Pipeline:
    features = FeatureUnion([
        ("word", TfidfVectorizer(preprocessor=normalize, ngram_range=(1, 2),
                                 sublinear_tf=True, min_df=1)),
        ("char", TfidfVectorizer(preprocessor=normalize, analyzer="char_wb",
                                 ngram_range=(2, 5), sublinear_tf=True, min_df=1)),
    ])
    if kind == "naive_bayes":
        clf = ComplementNB(alpha=0.3)
    elif kind == "logistic_regression":
        clf = LogisticRegression(C=30, max_iter=3000, class_weight="balanced")
    else:
        raise ValueError(kind)
    return Pipeline([("features", features), ("clf", clf)])


class Assistant:
    """Loads the saved model + keyword list and analyses one message."""

    def __init__(self, model_path: str, keywords_path: str, low_conf: float = 0.4):
        bundle = joblib.load(model_path)
        self.pipeline = bundle["pipeline"]
        self.threshold = bundle["threshold"]
        self.model_name = bundle["model_name"]
        self.keywords = KeywordLayer(keywords_path)
        self.low_conf = low_conf
        self.classes = list(self.pipeline.classes_)
        self.crisis_idx = self.classes.index(CRISIS)

    def explain(self, text: str) -> dict:
        """Full breakdown for testing: cleaned text, keyword hits, every class
        probability and the final decision. Used by try_model.py and /staff/try."""
        from .text_clean import detect_language, normalize
        proba = self.pipeline.predict_proba([text])[0]
        result = self.analyze(text)
        return {
            "normalized": normalize(text),
            "language": detect_language(text),
            "keyword_hits": self.keywords.hits(text),
            "probabilities": {c: round(float(p), 3) for c, p in
                              sorted(zip(self.classes, proba), key=lambda x: -x[1])},
            "p_crisis": round(result["p_crisis"], 3),
            "threshold": self.threshold,
            "model_says_crisis": result["p_crisis"] >= self.threshold,
            "keyword_says_crisis": bool(self.keywords.hits(text)),
            "decision": result,
        }

    def analyze(self, text: str) -> dict:
        kw = self.keywords.hits(text)
        proba = self.pipeline.predict_proba([text])[0]
        p_crisis = float(proba[self.crisis_idx])
        model_flag = p_crisis >= self.threshold

        if kw or model_flag:
            layer = "both" if (kw and model_flag) else ("keyword" if kw else "model")
            return {"intent": CRISIS, "is_crisis": True, "layer": layer,
                    "p_crisis": p_crisis, "keyword_hits": kw, "confidence": 1.0}

        # not a crisis -> best of the remaining four classes
        masked = proba.copy()
        masked[self.crisis_idx] = 0.0
        masked = masked / masked.sum()
        best = int(np.argmax(masked))
        conf = float(masked[best])
        intent = self.classes[best]
        return {"intent": intent, "is_crisis": False, "layer": None,
                "p_crisis": p_crisis, "keyword_hits": [], "confidence": conf,
                "low_confidence": conf < self.low_conf}
