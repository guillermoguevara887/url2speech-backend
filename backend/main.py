# backend/main.py

import os
from io import BytesIO
from typing import Literal

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from gtts import gTTS

from backend.services.scraping import extraer_texto
from backend.services.resumen import resumir
from backend.services.quiz_basic import generar_quiz_basico

# ---------- CONFIG / AUTH ----------
API_KEY = os.getenv("API_KEY")  # opcional: define en Railway Variables

app = FastAPI(title="EduAssist API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # en prod: restringe a tu dominio de Vercel
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def require_api_key(x_api_key: str = Header(default=None, alias="X-API-Key")):
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="API key inválida")
    return True

# ---------- MODELOS ----------
class UrlInput(BaseModel):
    url: str

class ResumenInput(BaseModel):
    texto: str
    modo: Literal["auto", "summary", "full"] = "summary"

class QuizIn(BaseModel):
    texto: str
    num: int = 4

class TtsInput(BaseModel):
    texto: str
    lang: Literal["es", "en"] = "es"

# ---------- RUTAS ----------
@app.get("/")
def root():
    return {"ok": True, "msg": "Bienvenido a EduAssist API. Visita /docs para probar los endpoints."}

@app.get("/health")
def health():
    return {"ok": True}

# Scraping
@app.post("/analizar")
def analizar(payload: UrlInput, _=Depends(require_api_key)):
    try:
        return extraer_texto(payload.url)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Resumen
@app.post("/resumir")
def resumir_endpoint(payload: ResumenInput, _=Depends(require_api_key)):
    if not payload.texto.strip():
        raise HTTPException(status_code=400, detail="Texto vacío")
    try:
        return {"resumen": resumir(payload.texto, payload.modo)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Quiz básico
@app.post("/quiz-basic")
def quiz_basic(body: QuizIn, _=Depends(require_api_key)):
    if not body.texto.strip():
        raise HTTPException(status_code=400, detail="Texto vacío")
    try:
        return generar_quiz_basico(body.texto, body.num)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# TTS (MP3)
@app.post("/tts")
def tts_endpoint(body: TtsInput, _=Depends(require_api_key)):
    texto = body.texto.strip()
    if not texto:
        raise HTTPException(status_code=400, detail="Texto vacío")

    try:
        buf = BytesIO()
        gTTS(text=texto, lang=body.lang, slow=False).write_to_fp(buf)
        buf.seek(0)
        return StreamingResponse(
            buf,
            media_type="audio/mpeg",
            headers={"Content-Disposition": 'inline; filename="speech.mp3"'},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS error: {e}")