"""Layer 1 of the crisis check: the specialists' keyword list.

`data/crisis_keywords.txt` is written and owned by the unit's specialists.
One phrase per line; lines starting with '#' are comments. A line starting
with 're:' is treated as a regular expression (applied to normalised text,
padded with one space on each side).

Matching is done on normalised text:
  1. exact substring  -> Arabic prefixes such as ب / ه / و still match
  2. typo-tolerant    -> a phrase also matches when one of its words of 4+
     letters appears with two neighbouring letters swapped (انتحار / انتحرا)
     or, for words of 6+ letters, one letter missing. This keeps the
     keyword layer safe against fast, emotional typing.
"""
import re
from .text_clean import normalize

_PREFIXES = ("وال", "بال", "فال", "لل", "ال", "و", "ب", "ف", "ه", "ل")


def _strip(tok: str) -> str:
    for p in _PREFIXES:
        if tok.startswith(p) and len(tok) - len(p) >= 3:
            return tok[len(p):]
    return tok


def _near(a: str, b: str) -> bool:
    """True if a == b, or b is a with one adjacent swap / one deletion."""
    if a == b:
        return True
    if len(a) < 4:
        return False
    if len(a) == len(b):
        diff = [i for i in range(len(a)) if a[i] != b[i]]
        return (len(diff) == 2 and diff[1] == diff[0] + 1
                and a[diff[0]] == b[diff[1]] and a[diff[1]] == b[diff[0]])
    if len(a) >= 6 and len(b) == len(a) - 1:
        return any(a[:i] + a[i + 1:] == b for i in range(len(a)))
    return False


def _tok_match(kw_tok: str, tok: str) -> bool:
    return (_near(kw_tok, tok) or _near(kw_tok, _strip(tok))
            or _near(_strip(kw_tok), _strip(tok)))


class KeywordLayer:
    def __init__(self, path: str):
        self.path = path
        self.reload()

    def reload(self):
        phrases, patterns = [], []
        with open(self.path, encoding="utf-8") as f:
            for raw in f:
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue
                if line.startswith("re:"):
                    patterns.append(re.compile(line[3:].strip()))
                else:
                    n = normalize(line)
                    if n:
                        phrases.append(n)
        self.phrases = sorted(set(phrases))
        self.phrase_tokens = [p.split() for p in self.phrases]
        self.patterns = patterns

    def hits(self, text: str) -> list:
        """Return keywords/patterns found in *text* (empty list = no hit)."""
        norm = normalize(text)
        t = " " + norm + " "
        found = [p for p in self.phrases if p in t]
        found += ["re:" + p.pattern for p in self.patterns if p.search(t)]
        if found:
            return found
        # typo-tolerant pass (only when nothing matched exactly)
        toks = norm.split()
        for phrase, ptoks in zip(self.phrases, self.phrase_tokens):
            n = len(ptoks)
            for i in range(len(toks) - n + 1):
                if all(_tok_match(k, w) for k, w in zip(ptoks, toks[i:i + n])):
                    found.append(phrase + " (typo)")
                    break
        return found
