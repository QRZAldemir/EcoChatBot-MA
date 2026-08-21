"""
================================================================================
PONTO DE ENTRADA DA APLICAÇÃO (MAIN APP) - ECOCHAT MARCX API
================================================================================
Autor: Aldemir Queiroz da Silva
Versão: 1.0.0
Data de Criação: 03 de Julho de 2026
================================================================================
FINALIDADE DO SCRIPT:
Este script atua como o núcleo da aplicação backend construída com FastAPI. 
Suas responsabilidades incluem:
1. Inicializar a instância principal do FastAPI com metadados da API.
2. Carregar variáveis de ambiente críticas para a configuração da aplicação.
3. Configurar middlewares de segurança e cross-origin (CORS) para comunicação 
   com o frontend (Angular).
4. Registrar e agrupar os módulos de rotas (routers) que compõem os endpoints 
   da API, organizando-os por domínios (Usuários, Departamentos, IA, etc.).
5. Expor endpoints básicos de verificação de status (Root e Health Check).
================================================================================
"""

import os
from typing import Dict, List

from dotenv import load_dotenv
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ==============================================================================
# 1. CARREGAMENTO DE VARIÁVEIS DE AMBIENTE
# ==============================================================================
# O load_dotenv() deve ser chamado o mais cedo possível. Isso garante que todas 
# as configurações sensíveis (URLs de banco, chaves de API, etc.) estejam 
# disponíveis antes da importação de outros módulos que dependam delas.
load_dotenv()

# ==============================================================================
# 2. IMPORTAÇÃO DOS ROUTERS (CONTROLADORES DE ROTA)
# ==============================================================================
# Cada módulo importado representa um domínio de negócio ou funcionalidade 
# específica da API. O uso de parênteses permite quebrar a linha (PEP 8).
from app.routers import (
    auth,
    usuarios,
    departamentos,
    canais,
    conexoes,
    contatos,
    email,
    campanhas,
    arquivos,
    ia,
    mensagem,
    menus,
    modelos_mensagem,
    atendimento,
    webhook,
    audio
)
from app.routers.tenant import atendimentos as tenant_atendimentos
from app.routers.tenant import usuarios as tenant_usuarios
from app.security import obter_usuario_atual

# ==============================================================================
# 3. CONFIGURAÇÃO DA INSTÂNCIA FASTAPI
# ==============================================================================
# A variável 'app' é o coração da aplicação. Ela recebe metadados que são 
# automaticamente expostos na documentação interativa (Swagger UI / OpenAPI).
app = FastAPI(
    title="EcoChat Marcx API",
    description="API para sistema de atendimento inteligente do Hospital Marcx",
    version="1.0.0",
    docs_url="/docs",      # URL para o Swagger UI (Documentação interativa)
    redoc_url="/redoc"     # URL para o ReDoc (Documentação alternativa)
)

# ==============================================================================
# 4. CONFIGURAÇÃO DE MIDDLEWARE (CORS)
# ==============================================================================
# O CORS (Cross-Origin Resource Sharing) é essencial para permitir que o 
# frontend (Angular) faça requisições HTTP para este backend.
# 
# MELHORIA DE ENGENHARIA: A URL do frontend foi movida para uma variável de 
# ambiente (FRONTEND_URL). Isso evita "hardcoding" e permite que o mesmo código 
# rode em Dev, Homologação e Produção apenas alterando o arquivo .env.
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:4200")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],  # Domínios permitidos para acessar a API
    allow_credentials=True,        # Permite envio de cookies/cabeçalhos de auth
    allow_methods=["*"],           # Permite todos os métodos HTTP (GET, POST, PUT, etc.)
    allow_headers=["*"],           # Permite todos os cabeçalhos personalizados
)

# ==============================================================================
# 5. REGISTRO DE ROTAS (ROUTERS)
# ==============================================================================
# MELHORIA DE ENGENHARIA (DRY - Don't Repeat Yourself): Em vez de chamar 
# app.include_router() 8 vezes de forma repetitiva, agrupamos os routers em 
# uma lista de tuplas. Se amanhã você precisar adicionar 10 novos módulos, 
# basta inserir novas linhas nesta lista, mantendo o código limpo e escalável.
#
# NOTA DE ENGENHARIA (tags sem acentuação): as tags abaixo alimentam tanto o
# Swagger UI (/docs) quanto o gerador de cliente TypeScript para o Angular
# (openapi-typescript-codegen, ver frontend/package.json -> "generate:api").
# Esse gerador usa a tag para nomear a classe do service (ex.: tag
# "Usuários" -> "UsuRiosService" — a translieração de acentos quebra o
# identificador). Por isso as tags são mantidas em ASCII aqui.
#
# NOTA DE SEGURANÇA (protegido=True): exige um JWT válido (ver
# app/security.py::obter_usuario_atual) — reservado às rotas que a
# verificação em código confirmou serem usadas *apenas* pelo painel Angular
# /admin/* (nenhuma chamada do widget de chat público nem do bot_service).
# canais/menus/modelos-mensagem ficam de fora por enquanto: misturam leitura
# pública (widget de chat, sem login) com escrita administrativa — proteger
# o router inteiro quebraria o chat; ver docs/Skill sobre Autenticação.md.
ROUTERS_CONFIG: List[tuple] = [
    (auth, "/api/auth", "Autenticacao", False),
    (usuarios, "/api/usuarios", "Usuarios", True),
    (departamentos, "/api/departamentos", "Departamentos", True),
    (canais, "/api/canais", "Canais", False),
    (conexoes, "/api/conexoes", "Conexoes", True),
    (contatos, "/api/contatos", "Contatos", True),
    (email, "/api/emails", "Email", True),
    (campanhas, "/api/campanhas", "Campanhas", True),
    (arquivos, "/api/arquivos", "Arquivos", True),
    (ia, "/api/ia", "Inteligencia Artificial", False),
    (mensagem, "/api/mensagem", "Mensagens", False),
    (menus, "/api/menus", "Menus", False),
    (modelos_mensagem, "/api/modelos-mensagem", "Modelos de Mensagem", False),
    (atendimento, "/api/atendimento", "Atendimento", True),
    (webhook, "/api/webhook", "Webhook", False),
    (audio, "/api/audio", "Audio", False),
    (tenant_atendimentos, "/api", "Tenant Atendimentos", True),
    (tenant_usuarios, "/api", "Tenant Usuarios", True)
]

for router_module, prefix, tag, protegido in ROUTERS_CONFIG:
    app.include_router(
        router_module.router,
        prefix=prefix,
        tags=[tag],
        dependencies=[Depends(obter_usuario_atual)] if protegido else [],
    )

# ==============================================================================
# 6. ENDPOINTS BÁSICOS (HEALTH CHECK & ROOT)
# ==============================================================================

@app.get("/", tags=["Root"])
def read_root() -> Dict[str, str]:
    """
    Endpoint raiz. Serve como uma mensagem de boas-vindas e confirmação 
    de que a API está respondendo a requisições HTTP.
    """
    return {"message": "EcoChat Marcx API - Backend Python FastAPI"}

@app.get("/health", tags=["Monitoramento"])
def health_check() -> Dict[str, str]:
    """
    Endpoint de Health Check.
    Utilizado por orquestradores de contêineres (Docker, Kubernetes) ou 
    ferramentas de monitoramento (UptimeRobot, Datadog) para verificar se 
    a aplicação está viva e apta a receber tráfego.
    """
    return {"status": "healthy"}