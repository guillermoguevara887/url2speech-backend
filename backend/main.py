# backend/main.py

import os
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from backend.services.scraping import extraer_texto
from backend.services.resumen import resumir

# API Key desde variables de entorno
API_KEY = os.getenv("API_KEY")

app = FastAPI(title="EduAssist API")

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # en producción restringe a tu dominio
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependencia para validar API Key
def require_api_key(x_api_key: str = Header(default=None, alias="X-API-Key")):
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="API key inválida")
    return True

# Modelos de entrada
class UrlInput(BaseModel):
    url: str

class ResumenInput(BaseModel):
    texto: str
    modo: str = "summary"   # auto|summary|full

# Ruta raíz
@app.get("/")
def root():
    return {
        "ok": True,
        "msg": "Bienvenido a EduAssist API. Visita /docs para probar los endpoints."
    }

# Ruta de healthcheck
@app.get("/health")
def health():
    return {"ok": True}

# Endpoint para analizar una URL (scraping)
@app.post("/analizar")
def analizar(payload: UrlInput, _=Depends(require_api_key)):
    try:
        return extraer_texto(payload.url)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Endpoint para resumir texto
@app.post("/resumir")
def resumir_endpoint(payload: ResumenInput, _=Depends(require_api_key)):
    if not payload.texto.strip():
        raise HTTPException(status_code=400, detail="Texto vacío")
    try:
        return {"resumen": resumir(payload.texto, payload.modo)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
