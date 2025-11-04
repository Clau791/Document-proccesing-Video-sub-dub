
import re

SIMPLE_MAP = {
    ("en","ro"): {
        "the": "—",
        "and": "și",
        "of": "de",
        "to": "la",
        "a": "un",
        "is": "este",
    }
}

def pseudo_translate(text: str, src: str, dst: str) -> str:
    """
    Extremely naive "translation": applies a few word swaps and tags the output.
    Replace this function with a call to a real MT engine.
    """
    key = (src.lower(), dst.lower())
    mapping = SIMPLE_MAP.get(key, {})
    out = text
    for w, repl in mapping.items():
        out = re.sub(rf"\b{re.escape(w)}\b", repl, out, flags=re.IGNORECASE)
    return f"[{src}->{dst} PSEUDO]\n\n" + out
