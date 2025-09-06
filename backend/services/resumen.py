import re
from collections import Counter

SPLIT = re.compile(r'(?<=[.?!])\s+|\n+')  # conserva fin de oración
STOP = set("""
de la los las un una y o a en del al para por con su sus es son fue fueron
como que se lo le les sus este esta estos estas entre sobre desde contra
""".split())

def resumir(texto: str, modo: str = "summary") -> str:
    sents = [s.strip() for s in SPLIT.split(texto) if s.strip()]
    if not sents:
        return ""

    words = re.findall(r'\w{3,}', texto.lower(), flags=re.UNICODE)
    frec = Counter(w for w in words if w not in STOP)

    scored = []
    for idx, s in enumerate(sents):
        toks = [w for w in re.findall(r'\w{3,}', s.lower(), flags=re.UNICODE) if w not in STOP]
        score = sum(frec.get(t, 0) for t in toks) / (len(toks) or 1)
        scored.append((score, idx, s))

    scored.sort(key=lambda x: x[0], reverse=True)
    k = {"full": len(sents), "summary": 5, "auto": 5}.get(modo, 5)
    top = sorted(scored[:k], key=lambda x: x[1])  # reordenamos por posición original

    out = " ".join(s for _, _, s in top)
    return (out + ".") if out and not out.endswith(".") else out