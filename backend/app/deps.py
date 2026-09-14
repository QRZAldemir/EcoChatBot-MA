"""
================================================================================
MÓDULO: app/deps.py
AUTOR: Aldemir Queiroz da Silva
VERSÃO: 1.0.0
DATA: 03 de Julho de 2026

FINALIDADE:
    Centraliza as dependências de segurança e isolamento de tenant (empresa)
    para injeção automática nas rotas do FastAPI.

RESPONSABILIDADES:
    1. Configurar o esquema OAuth2 para extração do token JWT do header
       Authorization (Bearer).
    2. Decodificar e validar o token JWT, extraindo as claims de identidade
       (user_id) e de tenant (empresa_id).
    3. Prover a dependência `get_current_user_tenant` que:
       a) Autentica o usuário (token válido e não expirado).
       b) Autoriza o acesso com base no vínculo empresarial (multi-tenancy).
       c) Retorna um objeto tipado com o contexto de segurança da requisição.

CONCEITO CHAVE — MULTI-TENANCY:
    Cada empresa (tenant) possui seus próprios dados isolados. A dependência
    `get_current_user_tenant` garante que um usuário da Empresa A jamais
    consiga acessar dados da Empresa B, pois o `empresa_id` extraído do JWT
    é injetado automaticamente em todas as queries subsequentes.

DEPENDÊNCIAS:
    - app.database.get_db (sessão de banco de dados)
    - app.services.auth_service.decode_jwt_token (decodificação JWT)
================================================================================
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db

# Importação do serviço de autenticação JWT.
# NOTA PARA DESENVOLVEDORES: Este módulo (app/services/auth_service.py) deve
# implementar a função `decode_jwt_token(token: str) -> dict | None`, que:
#   - Retorna um dict com as claims do JWT se o token for válido.
#   - Retorna None ou levanta exceção se o token for inválido/expirado.
from app.services.auth_service import decode_jwt_token


# ==============================================================================
# 1. MODELO DE DADOS DO CONTEXTO DE SEGURANÇA
# ==============================================================================
# CORREÇÃO APLICADA: Substituído o retorno em `dict` por um modelo Pydantic.
#
# POR QUE ISSO IMPORTA?
# - Tipagem estática: IDEs (VS Code, PyCharm) oferecem autocompletar ao acessar
#   `current_user.empresa_id` em qualquer rota.
# - Documentação automática: O FastAPI exibe este modelo no Swagger/OpenAPI.
# - Imutabilidade: Com `frozen=True`, impede que alguma rota modifique
#   acidentalmente o contexto de segurança durante a requisição.
class TenantContext(BaseModel):
    """
    Contexto de segurança e isolamento de tenant extraído do JWT.
    Injetado automaticamente nas rotas que requerem autenticação.
    """
    user_id: int
    empresa_id: int | None
    is_super_admin: bool

    model_config = {"frozen": True}


# ==============================================================================
# 2. ESQUEMA OAUTH2 (EXTRAÇÃO DO TOKEN)
# ==============================================================================
# O OAuth2PasswordBearer instrui o FastAPI a:
# 1. Exigir o header `Authorization: Bearer <token>` nas rotas protegidas.
# 2. Exibir o botão "Authorize" no Swagger UI apontando para a URL de login.
#
# ATENÇÃO: O `tokenUrl` deve corresponder exatamente à rota de login da API.
# Se a rota mudar (ex: de "/api/usuarios/login" para "/api/v2/auth/login"),
# este valor DEVE ser atualizado, caso contrário a documentação Swagger quebrará.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/usuarios/login")


# ==============================================================================
# 3. DEPENDÊNCIA PRINCIPAL: AUTENTICAÇÃO + ISOLAMENTO DE TENANT
# ==============================================================================
def get_current_user_tenant(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> TenantContext:
    """
    Dependência FastAPI que autentica o usuário via JWT e extrai o contexto
    de tenant (empresa) para isolamento de dados.

    Fluxo de Execução:
    1. O FastAPI extrai o token do header Authorization (via oauth2_scheme).
    2. O token é decodificado e validado (assinatura, expiração).
    3. As claims `sub` (user_id), `empresa_id` e `nivel` são extraídas.
    4. Valida-se que o usuário possui vínculo empresarial ou é super_admin.
    5. Retorna um TenantContext imutável para uso na rota.

    Raises:
        HTTPException 401: Token ausente, inválido ou expirado.
        HTTPException 403: Usuário autenticado, mas sem empresa associada.

    Exemplo de uso em uma rota:
        @router.get("/pacientes")
        def listar_pacientes(
            current_user: TenantContext = Depends(get_current_user_tenant),
            db: Session = Depends(get_db),
        ):
            # current_user.empresa_id contém o ID da empresa do usuário logado
            return db.query(Paciente).filter(
                Paciente.empresa_id == current_user.empresa_id
            ).all()
    """

    # ── Passo 1: Decodificação e Validação do JWT ──────────────────────────
    # CORREÇÃO APLICADA: Envolve a chamada em try/except para tratar tokens
    # inválidos, expirados ou malformados. Sem isso, uma exceção não tratada
    # no decode_jwt_token resultaria em HTTP 500 (Internal Server Error),
    # expondo detalhes internos da aplicação ao cliente.
    try:
        payload = decode_jwt_token(token)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token inválido ou expirado: {exc}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # CORREÇÃO APLICADA: Verifica se o payload não é None.
    # Se decode_jwt_token retornar None (token inválido sem exceção),
    # a chamada payload.get() abaixo levantaria AttributeError.
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido: payload vazio.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # ── Passo 2: Extração das Claims ───────────────────────────────────────
    # Convenção JWT:
    #   - "sub" (subject): identificador único do usuário (user_id)
    #   - "empresa_id": claim customizada para multi-tenancy
    #   - "nivel": claim customizada para controle de permissão
    user_id = payload.get("sub")
    empresa_id = payload.get("empresa_id")
    nivel = payload.get("nivel", "")
    is_super_admin = nivel == "super_admin"

    # Validação: o campo "sub" é obrigatório em qualquer JWT válido
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido: identificador de usuário (sub) ausente.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # ── Passo 3: Validação de Autorização (Tenant) ─────────────────────────
    # Regra de Negócio: Todo usuário deve pertencer a uma empresa, EXCETO
    # super_admins que possuem acesso transversal a todos os tenants.
    if not empresa_id and not is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado: usuário sem empresa associada.",
        )

    # ── Passo 4: Retorno do Contexto Tipado ────────────────────────────────
    return TenantContext(
        user_id=int(user_id),
        empresa_id=int(empresa_id) if empresa_id else None,
        is_super_admin=is_super_admin,
    )