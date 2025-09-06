import re
from collections import Counter
SPLIT = re.compile(r'[.?!\n]+')

def resumir(texto: str, modo: str = "summary") -> str:
    sents = [s.strip() for s in SPLIT.split(texto) if s.strip()]
    if not sents: return ""
    words = re.findall(r'\w{3,}', texto.lower(), flags=re.UNICODE)
    frec = Counter(words)
    scored = []
    for s in sents:
        toks = re.findall(r'\w{3,}', s.lower(), flags=re.UNICODE)
        score = sum(frec.get(t,0) for t in toks)/(len(toks) or 1)
        scored.append((score,s))
    scored.sort(reverse=True)
    k = {"full":len(sents),"summary":5,"auto":5}.get(modo,5)
    out = ". ".join(s for _,s in scored[:k])
    return (out + ".") if out and not out.endswith(".") else out
