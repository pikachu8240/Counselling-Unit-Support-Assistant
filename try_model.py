"""Try the AI from the command line.  Usage:
    python try_model.py                      # interactive: type messages, Enter on empty line to quit
    python try_model.py "قلقان من الامتحان"   # one message
    python try_model.py --file my_tests.txt  # one message per line, prints a summary table

Shows, for every message: the cleaned text, Layer 1 (keyword hits), Layer 2
(probability of each of the 5 classes vs the crisis threshold) and the final
decision. Nothing is saved.
"""
import sys

import config
from core.model import Assistant

A = Assistant(config.MODEL_PATH, config.KEYWORDS_PATH, config.LOW_CONFIDENCE)


def show(text):
    e = A.explain(text)
    d = e["decision"]
    print("\n" + "=" * 60)
    print(f"Message      : {text}")
    print(f"Cleaned      : {e['normalized']}   (language: {e['language']})")
    print(f"Layer 1 (keywords): {'CRISIS' if e['keyword_says_crisis'] else 'no hit'}"
          + (f"  -> {', '.join(e['keyword_hits'])}" if e["keyword_hits"] else ""))
    print(f"Layer 2 (model)   : P(crisis) = {e['p_crisis']:.3f}  vs threshold {e['threshold']}"
          f"  -> {'CRISIS' if e['model_says_crisis'] else 'below threshold'}")
    for c, p in e["probabilities"].items():
        print(f"    {c:9s} {p:5.3f} " + "#" * int(p * 40))
    if d["is_crisis"]:
        print(f">>> DECISION: CRISIS  (caught by: {d['layer']})  -> show 16328 + unit contacts")
    else:
        extra = "  (low confidence -> show menu)" if d.get("low_confidence") else ""
        print(f">>> DECISION: {d['intent']}  (confidence {d['confidence']:.2f}){extra}")
    return d


def main(argv):
    if len(argv) > 1 and argv[1] == "--file":
        lines = [l.strip() for l in open(argv[2], encoding="utf-8") if l.strip()]
        rows = [(t, show(t)) for t in lines]
        print("\nSUMMARY")
        for t, d in rows:
            print(f"  {d['intent']:9s} {'(' + d['layer'] + ')' if d['layer'] else '':10s} {t}")
        return
    if len(argv) > 1:
        show(" ".join(argv[1:]))
        return
    print(f"Model: {A.model_name}  |  crisis threshold: {A.threshold}  |  keywords: {len(A.keywords.phrases)}")
    print("Type a message (Arabic or English). Empty line = quit.")
    while True:
        try:
            t = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not t:
            break
        show(t)


if __name__ == "__main__":
    main(sys.argv)
