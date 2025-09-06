# backend/main.py
import os
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Servicios existentes (tuyos)
from backend.services.scraping import extraer_texto
from backend.services.resumen import resumir               # resumen básico (no IA)

# API Key desde variables de entorno (configúrala en Railway)
API_KEY = os.getenv("API_KEY")

app = FastAPI(title="EduAssist API")

# CORS (en prod restringe a tu dominio de Vercel)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # p. ej. ["https://tu-app.vercel.app"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Archivos estáticos para MP3
STATIC_DIR = os.path.join("backend", "static")
AUDIO_DIR  = os.path.join(STATIC_DIR, "audio")
os.makedirs(AUDIO_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# --- Dependencia de API Key
def require_api_key(x_api_key: str = Header(default=None, alias="X-API-Key")):
    # Si definiste API_KEY en el entorno, exige que coincida
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="API key inválida")
    return True

# --- Modelos
class UrlInput(BaseModel):
    url: str

class ResumenInput(BaseModel):
    texto: str
    modo: str = "summary"   # "summary" | "auto" | "full" (lo usa tu servicio)

class TtsInput(BaseModel):
    texto: str
    lang: str = "es"        # "es" | "en"

class ProInput(BaseModel):
    texto: str
    modelo: str = "llama3.1:8b"  # modelo de Ollama

# --- Rutas básicas
@app.get("/")
def root():
    return {
        "ok": True,
        "msg": "EduAssist API. Visita /docs para probar los endpoints."
    }

@app.get("/health")
def health():
    return {"ok": True}

# --- Analizar (scraping)
@app.post("/analizar")
def analizar(payload: UrlInput, _=Depends(require_api_key)):
    try:
        return extraer_texto(payload.url)   # Debe devolver {"texto": "..."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# --- Resumen clásico (no IA generativa)
@app.post("/resumir")
def resumir_endpoint(payload: ResumenInput, _=Depends(require_api_key)):
    texto = (payload.texto or "").strip()
    if not texto:
        raise HTTPException(status_code=400, detail="Texto vacío")
    try:
        return {"resumen": resumir(texto, payload.modo)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Resumen PRO con Ollama (opcional, corre local en tu Mac)
@app.post("/resumir-pro")
def resumir_pro(payload: ProInput, _=Depends(require_api_key)):
    """
    Llama a Ollama local (http://localhost:11434) para un resumen de mayor calidad.
    En Railway no funcionará a menos que tengas un servidor con Ollama expuesto.
    """
    import requests
    texto = (payload.texto or "").strip()
    if not texto:
        raise HTTPException(status_code=400, detail="Texto vacío")

    prompt = (
        "Resume en español, en 6-8 oraciones claras y fieles al texto:\n\n"
        + texto[:6000]
    )
    try:
        r = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": payload.modelo, "prompt": prompt, "stream": False},
            timeout=60,
        )
        r.raise_for_status()
        data = r.json()
        resumen = (data.get("response") or "").strip()
        if not resumen:
            raise ValueError("Respuesta vacía de Ollama")
        return {"resumen": resumen}
    except Exception as e:
        # No rompas el flujo si no hay Ollama
        return {"resumen": f"[PRO] No se pudo usar Ollama: {e}"}

# --- Texto a voz: genera MP3 y devuelve URL pública
@app.post("/tts")
def tts_endpoint(payload: TtsInput, _=Depends(require_api_key)):
    """
    Genera un MP3 con gTTS y lo sirve desde /static/audio/<id>.mp3
    """
    from gtts import gTTS

    texto = (payload.texto or "").strip()
    if not texto:
        raise HTTPException(status_code=400, detail="Texto vacío")

    file_id = f"audio-{uuid4().hex}.mp3"
    out_path = os.path.join(AUDIO_DIR, file_id)

    try:
        tts = gTTS(text=texto, lang=payload.lang)
        tts.save(out_path)
        return {"url": f"/static/audio/{file_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"No se pudo generar audio: {e}")