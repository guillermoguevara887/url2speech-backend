import requests
from bs4 import BeautifulSoup

def extraer_texto(url: str) -> dict:
    headers = {"User-Agent": "Mozilla/5.0 (EduAssist/1.0)"}
    r = requests.get(url, headers=headers, timeout=25)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    for t in soup(["script","style","noscript"]): t.decompose()
    title = soup.title.string.strip() if soup.title else url
    text = " ".join(soup.get_text(separator=" ").split())
    return {"titulo": title, "texto": text}
