"""
================================================================================
PONTO DE ENTRADA DA APLICAÇÃO (MAIN APP) - ECOCHAT MARCX API
================================================================================
Autor: Aldemir Queiroz da Silva
Versão: 2.0.0 (Unificação completa: Dashboard, Segurança Avançada e CORS Multi-origem)
Data de Criação: 03 de Julho de 2026
Última Atualização: 18 de Setembro de 2026
================================================================================
FINALIDADE DO SCRIPT:
Núcleo unificado da aplicação backend FastAPI que:
1. Inicializa a API com metadados e documentação OpenAPI
2. Configura segurança (CORS, headers de proteção)
3. Registra todos os módulos de negócio (routers) com RBAC
4. Integra o Dashboard Analítico como módulo nativo
5. Expõe endpoints de monitoramento e health check
================================================================================
"""

import os
from typing import Dict, List, Optional

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

# ==============================================================================
# 1. CARREGAMENTO DE VARIÁVEIS DE AMBIENTE
# ==============================================================================
# CRÍTICO: Deve ser executado antes de qualquer importação que use .env
load_dotenv()

# ==============================================================================
# 2. IMPORTAÇÃO DOS ROUTERS (MÓDULOS DE NEGÓCIO)
# ==============================================================================
# Cada router representa um domínio do sistema. 
# O padrão DRY (Don't Repeat Yourself) é aplicado via lista de tuplas.
from app.routers import (
    auth,               # Autenticação e gestão de tokens JWT
    empresas,           # Gestão multi-tenant (empresas/clientes)
    usuarios,           # CRUD de usuários e perfis
    departamentos,      # Estrutura organizacional
    canais,             # Canais omnichannel (WhatsApp, Telegram, etc.)
    conexoes,           # Configurações de conexão com APIs externas
    contatos,           # Base de contatos e CRM
    email,              # Disparo e gestão de e-mails
    campanhas,          # Campanhas de marketing e broadcast
    arquivos,           # Upload e gestão de mídia
    ia,                 # Integrações com IA (OpenAI, Gemini)
    mensagem,           # Envio e recebimento de mensagens
    menus,              # Menus interativos e URA
    modelos_mensagem,   # Templates de mensagem
    atendimento,        # Gestão de tickets e atendimento humano
    dashboard,          #  NOVO: Dashboard analítico e KPIs
    webhook,            # Recebimento de webhooks (Meta, Telegram)
    audio,              # Processamento de áudio (STT/TTS)
)
from app.security import exigir_nivel_minimo, obter_usuario_atual

# ==============================================================================
# 3. CONFIGURAÇÃO DA INSTÂNCIA FASTAPI
# ==============================================================================
app = FastAPI(
    title="EcoChat Marcx API",
    description=(
        "API omnichannel de atendimento digital unificando WhatsApp, Telegram, "
        "Instagram e voz. Inclui automação via n8n, IA generativa e dashboard analítico."
    ),
    version="2.0.0",
    docs_url="/docs",           # Swagger UI (documentação interativa)
    redoc_url="/redoc",         # ReDoc (documentação alternativa)
    openapi_url="/openapi.json" # Especificação OpenAPI
)

# ==============================================================================
# 4. CONFIGURAÇÃO DE MIDDLEWARE (SEGURANÇA E CORS)
# ==============================================================================

# 4.1 - CORS (Cross-Origin Resource Sharing)
# PERMITE MÚLTIPLAS ORIGENS: Ex: Admin Panel + Web Chat Widget de clientes
FRONTEND_URLS = os.getenv("FRONTEND_URLS", "http://localhost:4200").split(",")
# Remove espaços em branco e URLs vazias
FRONTEND_URLS = [url.strip() for url in FRONTEND_URLS if url.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_URLS,      # Domínios explícitos permitidos (NUNCA use "*")
    allow_credentials=True,           # Permite cookies e headers de autenticação
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Requested-With", "X-Request-ID"],
    expose_headers=["X-Request-ID"],  # Headers que o frontend pode ler
)

# 4.2 - HEADERS DE SEGURANÇA (Proteção contra ataques comuns)
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """
    Injeta headers de segurança em todas as respostas HTTP.
    Protege contra: XSS, Clickjacking, MIME sniffing, e força HTTPS.
    """
    response: Response = await call_next(request)
    
    # Previne que o navegador interprete conteúdo de forma incorreta
    response.headers["X-Content-Type-Options"] = "nosniff"
    
    # Previne clickjacking (incorporação em iframes maliciosos)
    response.headers["X-Frame-Options"] = "DENY"
    
    # Proteção contra XSS (Cross-Site Scripting)
    response.headers["X-XSS-Protection"] = "1; mode=block"
    
    # Força uso de HTTPS por 1 ano (HSTS - CRÍTICO para webhooks da Meta)
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    # Política de referência (previne vazamento de dados sensíveis na URL)
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    return response

# ==============================================================================
# 5. REGISTRO DE ROTAS (ROUTERS) COM RBAC
# ==============================================================================
# ESTRUTURA DA TUPLA: (router_module, prefix, tag, protegido, nivel_minimo)
#
# - router_module: módulo Python importado (ex: auth, usuarios)
# - prefix: prefixo da URL (ex: /api/auth)
# - tag: categoria na documentação Swagger (SEM ACENTOS para gerar TypeScript)
# - protegido: True = exige JWT, False = público
# - nivel_minimo: None = qualquer usuário logado, "gerente" = RBAC
#
# HIERARQUIA DE ACESSO: atendente < supervisor < gerente < administrador
#
ROUTERS_CONFIG: List[tuple] = [
    (auth, "/api/auth", "Autenticacao", False, None),
    (empresas, "/api/empresas", "Empresas", True, "administrador"),
    (usuarios, "/api/usuarios", "Usuarios", True, None),
    (departamentos, "/api/departamentos", "Departamentos", True, None),
    (canais, "/api/canais", "Canais", False, None),
    (conexoes, "/api/conexoes", "Conexoes", True, "administrador"),
    (contatos, "/api/contatos", "Contatos", True, "gerente"),
    (email, "/api/emails", "Email", True, "gerente"),
    (campanhas, "/api/campanhas", "Campanhas", True, "gerente"),
    (arquivos, "/api/arquivos", "Arquivos", True, "atendente"),
    (ia, "/api/ia", "Inteligencia Artificial", True, "gerente"),
    (mensagem, "/api/mensagem", "Mensagens", True, "atendente"),
    (menus, "/api/menus", "Menus", False, None),
    (modelos_mensagem, "/api/modelos-mensagem", "Modelos de Mensagem", False, None),
    (atendimento, "/api/atendimento", "Atendimento", True, "atendente"),
    (dashboard, "/api/dashboard", "Dashboard", True, "gerente"),  # 🆕 NOVO
    (webhook, "/api/webhook", "Webhook", False, None),
    (audio, "/api/audio", "Audio", False, None),
]


def _deps_router(protegido: bool, nivel_minimo: Optional[str]):
    """
    Fábrica de dependências para routers.
    
    Args:
        protegido: Se True, exige autenticação JWT
        nivel_minimo: Se definido, exige nível hierárquico mínimo (RBAC)
    
    Returns:
        Lista de dependências FastAPI ou lista vazia
    """
    if nivel_minimo:
        # RBAC: exige JWT + nível hierárquico específico
        return [Depends(exigir_nivel_minimo(nivel_minimo))]
    if protegido:
        # Apenas JWT válido necessário
        return [Depends(obter_usuario_atual)]
    # Rota pública (ex: webhook, login)
    return []


# Registro dinâmico de todos os routers
for router_module, prefix, tag, protegido, nivel_minimo in ROUTERS_CONFIG:
    app.include_router(
        router_module.router,
        prefix=prefix,
        tags=[tag],
        dependencies=_deps_router(protegido, nivel_minimo),
    )

# ==============================================================================
# 6. ENDPOINTS BÁSICOS (HEALTH CHECK & ROOT)
# ==============================================================================

@app.get("/", tags=["Root"])
def read_root() -> Dict[str, str]:
    """
    Endpoint raiz. Confirma que a API está operacional.
    """
    return {
        "message": "EcoChat Marcx API - Backend Python FastAPI v2.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", tags=["Monitoramento"])
def health_check() -> Dict[str, str]:
    """
    Health Check para orquestradores (Docker, Kubernetes) e monitoramento.
    Retorna status da aplicação para ferramentas como UptimeRobot, Datadog.
    """
    return {
        "status": "healthy",
        "version": "2.0.0",
        "timestamp": "2026-09-18T00:00:00Z"  # Em produção, use datetime.now(timezone.utc)
    }


# ==============================================================================
# 7. EXECUÇÃO DIRETA (DESENVOLVIMENTO)
# ==============================================================================
if __name__ == "__main__":
    import uvicorn
    # Em produção, use: uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,        # Auto-reload em desenvolvimento
        workers=1           # Em produção, use múltiplos workers
    )