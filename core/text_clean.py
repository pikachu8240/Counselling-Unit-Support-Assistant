"""Arabic / English text cleaning with Python `re`.

The same `normalize()` is used for training, prediction and the crisis
keyword list, so a keyword written by a specialist with hamza or diacritics
still matches a student's message typed without them.
"""
import re

_DIACRITICS = re.compile(r"[ؐ-ًؚ-ٰٟۖ-ۭ]")
_TATWEEL = "ـ"
_ALEF = re.compile(r"[إأآٱا]")
_ARABIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
_PUNCT = re.compile(r"[^\w\s]|_")
_REPEAT = re.compile(r"(\w)\1{2,}")          # مخنوووق -> مخنوق , sooo -> so
_SPACES = re.compile(r"\s+")
_ARABIC_CHAR = re.compile(r"[؀-ۿ]")
_LATIN_CHAR = re.compile(r"[A-Za-z]")


def normalize(text: str) -> str:
    """Return a cleaned, normalised version of *text*."""
    if not isinstance(text, str):
        return ""
    t = text.lower().translate(_ARABIC_DIGITS)
    t = _DIACRITICS.sub("", t).replace(_TATWEEL, "")
    t = _ALEF.sub("ا", t)
    t = (t.replace("ى", "ي").replace("ة", "ه")
          .replace("ؤ", "و").replace("ئ", "ي").replace("ء", ""))
    t = t.replace("’", "'").replace("'", "")       # don't -> dont
    t = _PUNCT.sub(" ", t)
    t = _REPEAT.sub(r"\1", t)
    return _SPACES.sub(" ", t).strip()


def detect_language(text: str) -> str:
    """'ar' if the message is mostly Arabic letters, otherwise 'en'."""
    ar = len(_ARABIC_CHAR.findall(text or ""))
    en = len(_LATIN_CHAR.findall(text or ""))
    return "en" if en > ar else "ar"
