import requests
from bs4 import BeautifulSoup

MAX_CHARS = 30000  # límite de seguridad

def extraer_texto(url: str) -> dict:
    headers = {"User-Agent": "Mozilla/5.0 (EduAssist/1.0)"}
    r = requests.get(url, headers=headers, timeout=25)
    r.raise_for_status()

    ctype = r.headers.get("Content-Type", "").lower()
    if "text/html" not in ctype:
        return {"titulo": url, "texto": ""}

    soup = BeautifulSoup(r.text, "html.parser")
    for t in soup(["script","style","noscript"]):
        t.decompose()

    title = soup.title.string.strip() if soup.title and soup.title.string else url
    text = " ".join(soup.get_text(separator=" ").split())
    if len(text) > MAX_CHARS:
        text = text[:MAX_CHARS]

    return {"titulo": title, "texto": text}