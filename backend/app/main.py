"""
================================================================================
PONTO DE ENTRADA DA APLICAÇÃO (MAIN APP) - ECOCHAT MARCX API
================================================================================
Autor: Aldemir Queiroz da Silva
Versão: 1.1.0 (Adicionado router de Empresas/Tenants)
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
   da API, organizando-os por domínios (Empresas, Usuários, Departamentos, IA, etc.).
5. Expor endpoints básicos de verificação de status (Root e Health Check).
================================================================================
"""

import os
from typing import Dict, List, Optional

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
    empresas,       # <--- NOVO: Router de gestão de empresas e tenants
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
from app.security import exigir_nivel_minimo, obter_usuario_atual

# ==============================================================================
# 3. CONFIGURAÇÃO DA INSTÂNCIA FASTAPI
# ==============================================================================
# A variável 'app' é o coração da aplicação. Ela recebe metadados que são 
# automaticamente expostos na documentação interativa (Swagger UI / OpenAPI).
app = FastAPI(
    title="EcoChat Marcx API",
    description="API omnichannel de atendimento (WhatsApp, filas, campanhas e menus interativos)",
    version="1.1.0",
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
# app.include_router() diversas vezes de forma repetitiva, agrupamos os routers em 
# uma lista de tuplas. Se amanhã você precisar adicionar novos módulos, 
# basta inserir novas linhas nesta lista, mantendo o código limpo e escalável.
#
# NOTA DE ENGENHARIA (tags sem acentuação): as tags abaixo alimentam tanto o
# Swagger UI (/docs) quanto o gerador de cliente TypeScript para o Angular
# (openapi-typescript-codegen, ver frontend/package.json -> "generate:api").
# Esse gerador usa a tag para nomear a classe do service (ex.: tag
# "Usuarios" -> "UsuariosService"). Acentos ou barras quebram o identificador.
# Por isso, usamos "Empresas" em vez de "Empresas / Tenants".
#
# NOTA DE SEGURANÇA:
#   protegido=True  → JWT em todas as rotas (obter_usuario_atual)
#   nivel_minimo    → JWT + RBAC (exigir_nivel_minimo); implica protegido
# Routers mistos (GET público do /chat + escrita admin) ficam False/None
# aqui; o nível da escrita é declarado no próprio endpoint.
# webhook não usa JWT — autentica com WEBHOOK_SECRET (obrigatório).
#
# Hierarquia: atendente < supervisor < gerente < administrador
ROUTERS_CONFIG: List[tuple] = [
    (auth, "/api/auth", "Autenticacao", False, None),
    (empresas, "/api/empresas", "Empresas", True, "administrador"),  # <--- NOVO: Protegido, exige nível administrador
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
    (webhook, "/api/webhook", "Webhook", False, None),
    (audio, "/api/audio", "Audio", False, None),
]


def _deps_router(protegido: bool, nivel_minimo: Optional[str]):
    if nivel_minimo:
        return [Depends(exigir_nivel_minimo(nivel_minimo))]
    if protegido:
        return [Depends(obter_usuario_atual)]
    return []


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