"""
================================================================================
MÓDULO: app/routers/empresas.py
AUTOR: Aldemir Queiroz
DATA: 2026
VERSÃO: 1.0.0 (Implementação inicial do CRUD de Empresas/Tenants)

DESCRIÇÃO:
    Gerencia o ciclo de vida das empresas (tenants) do sistema, incluindo:
    - Criação de novas empresas com usuário administrador inicial
    - Listagem e consulta de empresas
    - Atualização de planos, limites e status
    - Integração com Evolution API v2 para criação de instâncias WhatsApp

ARQUITETURA MULTI-TENANT:
    - Super admins têm acesso global a todas as empresas
    - Usuários normais só podem acessar sua própria empresa (isolamento por empresa_id)
    - Cada empresa pode ter múltiplas instâncias de chatbot (WhatsApp)

INTEGRAÇÃO EXTERNA:
    - Evolution API v2: Criação de instâncias WhatsApp via HTTP
    - Variáveis de ambiente necessárias:
        * EVOLUTION_API_URL: URL base da Evolution API (ex: http://localhost:8080)
        * EVOLUTION_API_KEY: Chave de autenticação global da Evolution API

REGISTRO EM main.py:
    app.include_router(empresas.router, prefix="/api/empresas", tags=["Empresas"])

DEPENDÊNCIAS:
    - httpx: Cliente HTTP assíncrono para integração com Evolution API
================================================================================
"""

import logging
import os
from typing import List, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.database import get_db
# `Empresa` e `InstanciaChatbot` só existem na camada moderna; a legada
# (`app/models/__init__.py`) não as exporta. `Usuario` é o alias canônico
# definido em empresa_models.py.
from app.models.empresa_models import Empresa, InstanciaChatbot, Usuario
from app.security import exigir_nivel, obter_usuario_atual
from app.services.auth_service import hash_senha

router = APIRouter()
logger = logging.getLogger(__name__)

# ==============================================================================
# CONFIGURAÇÕES DA EVOLUTION API
# ==============================================================================

EVOLUTION_API_URL = os.getenv("EVOLUTION_API_URL", "http://localhost:8080")
EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_KEY", "")

if not EVOLUTION_API_KEY:
    logger.warning(
        "empresas | EVOLUTION_API_KEY não configurada. "
        "A criação de instâncias WhatsApp falhará até que a variável seja definida."
    )


# ==============================================================================
# SCHEMAS PYDANTIC (CONTRATOS DE DADOS)
# ==============================================================================

class EmpresaCreate(BaseModel):
    """Schema para criação de nova empresa + administrador inicial."""
    nome: str = Field(..., min_length=2, max_length=255, description="Nome fantasia da empresa")
    cnpj_cpf: Optional[str] = Field(None, max_length=20, description="CNPJ ou CPF (opcional)")
    email_contato: EmailStr = Field(..., description="E-mail de contato da empresa")
    telefone: Optional[str] = Field(None, max_length=30, description="Telefone de contato")
    plano: str = Field(default="starter", description="Plano contratado (starter, pro, enterprise)")
    max_instancias: int = Field(default=1, ge=1, description="Limite de instâncias permitidas")
    
    # Dados do administrador inicial
    admin_nome: str = Field(..., min_length=2, max_length=255, description="Nome do administrador")
    admin_email: EmailStr = Field(..., description="E-mail do administrador")
    admin_senha: str = Field(..., min_length=6, description="Senha do administrador (mínimo 6 caracteres)")


class EmpresaUpdate(BaseModel):
    """Schema para atualização de empresa (apenas campos editáveis)."""
    plano: Optional[str] = Field(None, description="Novo plano (starter, pro, enterprise)")
    max_instancias: Optional[int] = Field(None, ge=1, description="Novo limite de instâncias")
    ativo: Optional[bool] = Field(None, description="Status ativo/inativo")


class EmpresaResponse(BaseModel):
    """Schema de resposta com dados da empresa."""
    id: int
    nome: str
    cnpj_cpf: Optional[str]
    email_contato: str
    telefone: Optional[str]
    plano: str
    max_instancias: int
    ativo: bool
    created_at: str
    
    class Config:
        from_attributes = True


class InstanciaCreateRequest(BaseModel):
    """Schema para criação de instância WhatsApp."""
    nome_instancia: str = Field(
        ...,
        min_length=3,
        max_length=100,
        description="Nome identificador da instância (ex: empresa_x_suporte)",
        pattern=r"^[a-zA-Z0-9_\-]+$"  # Apenas alfanuméricos, hífens e underscores
    )
    webhook_url: Optional[str] = Field(None, description="URL de webhook para receber eventos")


class InstanciaResponse(BaseModel):
    """Schema de resposta com dados da instância criada."""
    id: int
    nome_instancia: str
    numero_whatsapp: Optional[str]
    status_conexao: str
    webhook_url: Optional[str]
    ativo: bool
    qrcode_base64: Optional[str] = Field(None, description="QR Code em base64 para pareamento")
    
    class Config:
        from_attributes = True


# ==============================================================================
# FUNÇÕES AUXILIARES
# ==============================================================================

def _verificar_acesso_empresa(usuario: Usuario, empresa_id: int) -> None:
    """
    Verifica se o usuário tem acesso à empresa especificada.
    
    Regras:
    - Super admins têm acesso a todas as empresas
    - Usuários normais só podem acessar sua própria empresa
    
    Raises:
        HTTPException 403: Se o usuário não tiver acesso à empresa.
    """
    # Verifica se o usuário é super_admin (nível "administrador" ou superior)
    is_super_admin = usuario.nivel and usuario.nivel.nome.lower() in ("administrador", "super_admin")
    
    if not is_super_admin and usuario.empresa_id != empresa_id:
        logger.warning(
            "empresas | Tentativa de acesso não autorizado | user_id=%s | empresa_id=%s | empresa_alvo=%s",
            usuario.id, usuario.empresa_id, empresa_id
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem permissão para acessar esta empresa."
        )


async def _criar_instancia_evolution(nome_instancia: str, webhook_url: Optional[str] = None) -> dict:
    """
    Cria uma nova instância na Evolution API v2.
    
    Args:
        nome_instancia (str): Nome identificador da instância.
        webhook_url (str, optional): URL de webhook para receber eventos.
        
    Returns:
        dict: Resposta da Evolution API contendo dados da instância e QR Code.
        
    Raises:
        HTTPException 502: Se houver falha na comunicação com a Evolution API.
    """
    if not EVOLUTION_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Serviço de criação de instâncias não configurado."
        )
    
    url = f"{EVOLUTION_API_URL}/instance/create"
    
    payload = {
        "instanceName": nome_instancia,
        "integration": "WHATSAPP-BAILEYS",
        "qrcode": True,
    }
    
    if webhook_url:
        payload["webhook"] = {
            "enabled": True,
            "url": webhook_url,
            "events": ["MESSAGES_UPSERT", "MESSAGES_UPDATE", "CONNECTION_UPDATE"]
        }
    
    headers = {
        "apikey": EVOLUTION_API_KEY,
        "Content-Type": "application/json"
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            
            if response.status_code not in (200, 201):
                logger.error(
                    "empresas | Falha na Evolution API | status=%s | response=%s",
                    response.status_code, response.text
                )
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Falha ao criar instância na Evolution API: {response.text}"
                )
            
            return response.json()
            
    except httpx.TimeoutException:
        logger.error("empresas | Timeout na comunicação com Evolution API")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Timeout na comunicação com a Evolution API."
        )
    except httpx.RequestError as e:
        logger.error("empresas | Erro de rede na comunicação com Evolution API: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Erro de rede ao comunicar com a Evolution API."
        )


# ==============================================================================
# ENDPOINT: CRIAR EMPRESA + ADMINISTRADOR INICIAL
# ==============================================================================

@router.post(
    "/",
    response_model=EmpresaResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(exigir_nivel("administrador", "super_admin"))]
)
async def criar_empresa(
    dados: EmpresaCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obter_usuario_atual)
):
    """
    Cria uma nova empresa (tenant) e seu usuário administrador inicial.
    
    Esta operação é transacional: se falhar ao criar o administrador, a empresa
    não será criada (rollback automático).
    
    Fluxo:
    1. Valida se o CNPJ/CPF já existe (se fornecido).
    2. Valida se o email do administrador já existe.
    3. Cria a empresa.
    4. Cria o usuário administrador vinculado à empresa.
    5. Retorna os dados da empresa criada.
    
    Args:
        dados (EmpresaCreate): Dados da empresa e do administrador.
        db (Session): Sessão do banco de dados.
        usuario (Usuario): Usuário autenticado (deve ser super_admin).
        
    Returns:
        EmpresaResponse: Dados da empresa criada.
        
    Raises:
        HTTPException 409: Se o CNPJ/CPF ou email já estiverem cadastrados.
    """
    logger.info(
        "empresas | Criação de empresa solicitada | user_id=%s | nome=%s",
        usuario.id, dados.nome
    )
    
    # ── 1. VALIDAÇÃO DE DUPLICATAS ──
    if dados.cnpj_cpf:
        empresa_existente = db.query(Empresa).filter(Empresa.cnpj_cpf == dados.cnpj_cpf).first()
        if empresa_existente:
            logger.warning(
                "empresas | Tentativa de criar empresa com CNPJ/CPF duplicado | cnpj=%s",
                dados.cnpj_cpf
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Já existe uma empresa com este CNPJ/CPF."
            )
    
    admin_existente = db.query(Usuario).filter(Usuario.email == dados.admin_email).first()
    if admin_existente:
        logger.warning(
            "empresas | Tentativa de criar administrador com email duplicado | email=%s",
            dados.admin_email
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe um usuário com este e-mail."
        )
    
    # ── 2. CRIAÇÃO DA EMPRESA ──
    try:
        empresa = Empresa(
            nome=dados.nome,
            cnpj_cpf=dados.cnpj_cpf,
            email_contato=dados.email_contato,
            telefone=dados.telefone,
            plano=dados.plano,
            max_instancias=dados.max_instancias,
            ativo=True
        )
        db.add(empresa)
        db.flush()  # Gera o ID da empresa sem fazer commit ainda
        
        # ── 3. CRIAÇÃO DO ADMINISTRADOR INICIAL ──
        admin = Usuario(
            empresa_id=empresa.id,
            nome=dados.admin_nome,
            email=dados.admin_email,
            senha_hash=hash_senha(dados.admin_senha),
            perfil="administrador",  # Perfil mais alto dentro da empresa
            ativo=True
        )
        db.add(admin)
        
        # ── 4. COMMIT TRANSACIONAL ──
        db.commit()
        db.refresh(empresa)
        
        logger.info(
            "empresas | Empresa criada com sucesso | empresa_id=%s | admin_id=%s",
            empresa.id, admin.id
        )
        
        return empresa
        
    except Exception as e:
        db.rollback()
        logger.exception("empresas | Falha ao criar empresa: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Falha interna ao criar a empresa."
        )


# ==============================================================================
# ENDPOINT: LISTAR TODAS AS EMPRESAS (SUPER ADMIN)
# ==============================================================================

@router.get(
    "/",
    response_model=List[EmpresaResponse],
    dependencies=[Depends(exigir_nivel("administrador", "super_admin"))]
)
async def listar_empresas(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obter_usuario_atual)
):
    """
    Lista todas as empresas cadastradas no sistema.
    
    Restrito a super admins (nível "administrador" ou "super_admin").
    
    Returns:
        List[EmpresaResponse]: Lista de todas as empresas.
    """
    logger.info("empresas | Listagem de empresas solicitada | user_id=%s", usuario.id)
    
    empresas = db.query(Empresa).order_by(Empresa.created_at.desc()).all()
    
    return empresas


# ==============================================================================
# ENDPOINT: DETALHES DA EMPRESA
# ==============================================================================

@router.get(
    "/{empresa_id}",
    response_model=EmpresaResponse,
)
async def obter_empresa(
    empresa_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obter_usuario_atual)
):
    """
    Obtém os detalhes de uma empresa específica.
    
    Controle de acesso:
    - Super admins podem ver qualquer empresa
    - Usuários normais só podem ver sua própria empresa
    
    Args:
        empresa_id (int): ID da empresa.
        
    Returns:
        EmpresaResponse: Dados da empresa.
        
    Raises:
        HTTPException 404: Se a empresa não for encontrada.
        HTTPException 403: Se o usuário não tiver acesso à empresa.
    """
    empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()
    
    if not empresa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empresa não encontrada."
        )
    
    # Verifica se o usuário tem acesso a esta empresa
    _verificar_acesso_empresa(usuario, empresa_id)
    
    logger.info(
        "empresas | Consulta de empresa | user_id=%s | empresa_id=%s",
        usuario.id, empresa_id
    )
    
    return empresa


# ==============================================================================
# ENDPOINT: ATUALIZAR EMPRESA
# ==============================================================================

@router.put(
    "/{empresa_id}",
    response_model=EmpresaResponse,
    dependencies=[Depends(exigir_nivel("administrador", "super_admin"))]
)
async def atualizar_empresa(
    empresa_id: int,
    dados: EmpresaUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obter_usuario_atual)
):
    """
    Atualiza os dados de uma empresa (plano, limite de instâncias, status).
    
    Restrito a super admins.
    
    Args:
        empresa_id (int): ID da empresa.
        dados (EmpresaUpdate): Campos a serem atualizados.
        
    Returns:
        EmpresaResponse: Dados atualizados da empresa.
        
    Raises:
        HTTPException 404: Se a empresa não for encontrada.
    """
    empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()
    
    if not empresa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empresa não encontrada."
        )
    
    logger.info(
        "empresas | Atualização de empresa | user_id=%s | empresa_id=%s | campos=%s",
        usuario.id, empresa_id, list(dados.dict(exclude_unset=True).keys())
    )
    
    # Atualiza apenas os campos fornecidos
    if dados.plano is not None:
        empresa.plano = dados.plano
    if dados.max_instancias is not None:
        empresa.max_instancias = dados.max_instancias
    if dados.ativo is not None:
        empresa.ativo = dados.ativo
    
    db.commit()
    db.refresh(empresa)
    
    logger.info("empresas | Empresa atualizada com sucesso | empresa_id=%s", empresa_id)
    
    return empresa


# ==============================================================================
# ENDPOINT: CRIAR INSTÂNCIA WHATSAPP (EVOLUTION API)
# ==============================================================================

@router.post(
    "/{empresa_id}/instancia",
    response_model=InstanciaResponse,
    status_code=status.HTTP_201_CREATED,
)
async def criar_instancia(
    empresa_id: int,
    dados: InstanciaCreateRequest,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obter_usuario_atual)
):
    """
    Cria uma nova instância WhatsApp na Evolution API v2.
    
    Controle de acesso:
    - Super admins podem criar instâncias para qualquer empresa
    - Administradores da empresa podem criar instâncias para sua própria empresa
    
    Fluxo:
    1. Valida se a empresa existe e está ativa.
    2. Valida se a empresa não excedeu o limite de instâncias.
    3. Valida se o nome da instância já existe.
    4. Chama a Evolution API para criar a instância.
    5. Salva os dados da instância no banco de dados.
    6. Retorna os dados da instância com o QR Code.
    
    Args:
        empresa_id (int): ID da empresa.
        dados (InstanciaCreateRequest): Dados da instância.
        
    Returns:
        InstanciaResponse: Dados da instância criada com QR Code.
        
    Raises:
        HTTPException 404: Se a empresa não for encontrada.
        HTTPException 403: Se o usuário não tiver acesso à empresa.
        HTTPException 409: Se o nome da instância já existir ou limite foi excedido.
        HTTPException 502: Se houver falha na comunicação com a Evolution API.
    """
    # ── 1. VALIDAÇÃO DA EMPRESA ──
    empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()
    
    if not empresa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empresa não encontrada."
        )
    
    if not empresa.ativo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Empresa inativa."
        )
    
    # ── 2. CONTROLE DE ACESSO ──
    # Super admins ou administradores da própria empresa podem criar instâncias
    is_super_admin = usuario.nivel and usuario.nivel.nome.lower() in ("administrador", "super_admin")
    is_admin_da_empresa = (usuario.empresa_id == empresa_id and usuario.perfil == "administrador")
    
    if not (is_super_admin or is_admin_da_empresa):
        logger.warning(
            "empresas | Tentativa de criar instância sem permissão | user_id=%s | empresa_id=%s",
            usuario.id, empresa_id
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem permissão para criar instâncias nesta empresa."
        )
    
    # ── 3. VALIDAÇÃO DE LIMITE DE INSTÂNCIAS ──
    quantidade_instancias = db.query(InstanciaChatbot).filter(
        InstanciaChatbot.empresa_id == empresa_id,
        InstanciaChatbot.ativo == True
    ).count()
    
    if quantidade_instancias >= empresa.max_instancias:
        logger.warning(
            "empresas | Limite de instâncias excedido | empresa_id=%s | max=%d | atual=%d",
            empresa_id, empresa.max_instancias, quantidade_instancias
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Limite de instâncias excedido. Máximo permitido: {empresa.max_instancias}."
        )
    
    # ── 4. VALIDAÇÃO DE NOME DA INSTÂNCIA ──
    instancia_existente = db.query(InstanciaChatbot).filter(
        InstanciaChatbot.nome_instancia == dados.nome_instancia
    ).first()
    
    if instancia_existente:
        logger.warning(
            "empresas | Tentativa de criar instância com nome duplicado | nome=%s",
            dados.nome_instancia
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe uma instância com este nome."
        )
    
    # ── 5. CHAMADA À EVOLUTION API ──
    logger.info(
        "empresas | Criando instância na Evolution API | empresa_id=%s | nome=%s",
        empresa_id, dados.nome_instancia
    )
    
    try:
        resultado_evolution = await _criar_instancia_evolution(
            nome_instancia=dados.nome_instancia,
            webhook_url=dados.webhook_url
        )
    except HTTPException:
        raise  # Re-raise HTTP exceptions from the helper function
    except Exception as e:
        logger.exception("empresas | Erro inesperado ao criar instância: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao criar a instância."
        )
    
    # ── 6. SALVAR NO BANCO DE DADOS ──
    try:
        instancia = InstanciaChatbot(
            empresa_id=empresa_id,
            nome_instancia=dados.nome_instancia,
            webhook_url=dados.webhook_url,
            status_conexao="aguardando_pareamento",
            ativo=True
        )
        db.add(instancia)
        db.commit()
        db.refresh(instancia)
        
        logger.info(
            "empresas | Instância criada com sucesso | empresa_id=%s | instancia_id=%s | nome=%s",
            empresa_id, instancia.id, dados.nome_instancia
        )
        
        # Extrai o QR Code da resposta da Evolution API
        qrcode_base64 = None
        if "qrcode" in resultado_evolution and "base64" in resultado_evolution["qrcode"]:
            qrcode_base64 = resultado_evolution["qrcode"]["base64"]
        
        # Retorna a resposta com o QR Code
        return InstanciaResponse(
            id=instancia.id,
            nome_instancia=instancia.nome_instancia,
            numero_whatsapp=instancia.numero_whatsapp,
            status_conexao=instancia.status_conexao,
            webhook_url=instancia.webhook_url,
            ativo=instancia.ativo,
            qrcode_base64=qrcode_base64
        )
        
    except Exception as e:
        db.rollback()
        logger.exception("empresas | Falha ao salvar instância no banco: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Falha interna ao salvar a instância."
        )