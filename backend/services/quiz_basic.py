# backend/services/quiz_basic.py
import re, random

SENT_SPLIT = re.compile(r'(?<=[.!?])\s+|\n+')

def _extraer_oraciones(texto: str):
    sents = [s.strip() for s in SENT_SPLIT.split(texto) if s.strip()]
    # Preferimos oraciones “medio largas”
    sents = [s for s in sents if 40 <= len(s) <= 240]
    return sents

def _keywords_candidatas(oracion: str):
    # Nombres propios y términos largos (heurístico simple)
    props = re.findall(r"\b[A-ZÁÉÍÓÚÑ][a-záéíóúñ]{3,}\b", oracion)
    largos = re.findall(r"\b[a-záéíóúñ]{6,}\b", oracion.lower())
    # quitamos duplicados manteniendo orden
    vistos = set()
    pool = []
    for w in props + largos:
        lw = w.lower()
        if lw not in vistos:
            vistos.add(lw)
            pool.append(w)
    return pool

def _distractores(oracion: str, respuesta: str):
    candidatos = [w for w in re.findall(r"\b\w{5,}\b", oracion) if w.lower() != respuesta.lower()]
    random.shuffle(candidatos)
    distract = []
    for w in candidatos:
        if w.lower() != respuesta.lower() and w not in distract:
            distract.append(w)
        if len(distract) == 3:
            break
    generic = ["Proceso académico", "Reglamento", "Plan de estudios", "Investigación", "Calendario", "Admisiones"]
    while len(distract) < 3:
        distract.append(random.choice(generic))
    return distract

def generar_quiz_basico(texto: str, num: int = 4):
    sents = _extraer_oraciones(texto)
    if not sents:
        return {"items": []}
    random.seed(42)  # reproducible para demo
    preguntas = []
    for s in sents[: num * 2]:
        keys = _keywords_candidatas(s)
        if not keys:
            continue
        ans = keys[0]
        opciones = _distractores(s, ans) + [ans]
        random.shuffle(opciones)
        preguntas.append({
            "pregunta": f"¿Qué término está más relacionado con esta afirmación?\n“{s}”",
            "opciones": opciones,
            "respuesta": ans
        })
        if len(preguntas) >= num:
            break
    return {"items": preguntas}