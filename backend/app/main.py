from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

# Carregar variáveis de ambiente
load_dotenv()

# Importar routers
from app.routers import usuarios, departamentos, canais, ia

# Criar aplicação FastAPI
app = FastAPI(
    title="EcoChat Mackenzie API",
    description="API para sistema de atendimento inteligente do Hospital Mackenzie",
    version="1.0.0"
)

# Configurar CORS para permitir requisições do frontend Angular
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],  # Frontend Angular
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(usuarios.router, prefix="/api/usuarios", tags=["Usuários"])
app.include_router(departamentos.router, prefix="/api/departamentos", tags=["Departamentos"])
app.include_router(canais.router, prefix="/api/canais", tags=["Canais"])
app.include_router(ia.router, prefix="/api/ia", tags=["Inteligência Artificial"])

@app.get("/")
def read_root():
    return {"message": "EcoChat Mackenzie API - Backend Python FastAPI"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
