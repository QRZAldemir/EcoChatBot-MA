from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.security import exigir_nivel, exigir_nivel_minimo
from app.services.usuario_service import UsuarioService
from app.schemas import UsuarioCreate, UsuarioUpdate, UsuarioResponse, UsuarioListItem

router = APIRouter()

@router.get("/", response_model=List[UsuarioListItem], dependencies=[Depends(exigir_nivel_minimo("supervisor"))])
def listar_usuarios(
    nome: Optional[str] = Query(None),
    departamentoId: Optional[int] = Query(None),
    canalId: Optional[int] = Query(None),
    nivel: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    usuarios = UsuarioService.listar_usuarios(
        db=db,
        nome=nome,
        departamento_id=departamentoId,
        canal_id=canalId,
        nivel=nivel,
        status=status
    )
    return [
        UsuarioListItem(
            id=u.id,
            nome=u.nome,
            email=u.email,
            telefone=u.telefone,
            ativo=u.ativo,
            nivel_nome=u.nivel.nome if u.nivel else None,
            departamento_nome=u.departamento.nome if u.departamento else None,
            canal_nome=u.canal.nome if u.canal else None
        )
        for u in usuarios
    ]

@router.get("/{usuario_id}", response_model=UsuarioResponse, dependencies=[Depends(exigir_nivel_minimo("supervisor"))])
def buscar_usuario(usuario_id: int, db: Session = Depends(get_db)):
    usuario = UsuarioService.buscar_por_id(db, usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return usuario

@router.post("/", response_model=UsuarioResponse, status_code=201, dependencies=[Depends(exigir_nivel_minimo("gerente"))])
def criar_usuario(usuario: UsuarioCreate, db: Session = Depends(get_db)):
    return UsuarioService.criar_usuario(db, usuario)

@router.put("/{usuario_id}", response_model=UsuarioResponse, dependencies=[Depends(exigir_nivel_minimo("gerente"))])
def atualizar_usuario(usuario_id: int, usuario: UsuarioUpdate, db: Session = Depends(get_db)):
    usuario_atualizado = UsuarioService.atualizar_usuario(db, usuario_id, usuario)
    if not usuario_atualizado:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return usuario_atualizado

@router.delete("/{usuario_id}", status_code=204, dependencies=[Depends(exigir_nivel("administrador"))])
def deletar_usuario(usuario_id: int, db: Session = Depends(get_db)):
    sucesso = UsuarioService.deletar_usuario(db, usuario_id)
    if not sucesso:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return None


from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import Usuario, UsuarioConexao, Conexao, Empresa
from app.schemas.usuario_schema import UsuarioCreate, UsuarioUpdate, UsuarioResponse
from app.core.security import get_password_hash

router = APIRouter(prefix="/api/usuarios", tags=["Usuários"])

@router.post("/", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
def criar_usuario(usuario_in: UsuarioCreate, db: Session = Depends(get_db)):
    # Verifica se email já existe
    if db.query(Usuario).filter(Usuario.email == usuario_in.email).first():
        raise HTTPException(status_code=400, detail="E-mail já cadastrado")
    
    # Cria o usuário
    db_usuario = Usuario(
        nome=usuario_in.nome,
        email=usuario_in.email,
        telefone=usuario_in.telefone,
        senha=get_password_hash(usuario_in.senha),
        nivel_id=usuario_in.nivel_id,
        departamento_id=usuario_in.departamento_id,
        empresa_id=usuario_in.empresa_id,
        conexao_padrao_id=usuario_in.conexao_padrao_id,
        ativo=usuario_in.ativo
    )
    db.add(db_usuario)
    db.commit()
    db.refresh(db_usuario)
    
    # Vincula as conexões selecionadas
    for conexao_id in usuario_in.conexoes_ids:
        # Valida se a conexão pertence à mesma empresa do usuário
        conexao = db.query(Conexao).filter(Conexao.id == conexao_id, Conexao.empresa_id == usuario_in.empresa_id).first()
        if conexao:
            db.add(UsuarioConexao(usuario_id=db_usuario.id, conexao_id=conexao_id))
    
    db.commit()
    db.refresh(db_usuario)
    return db_usuario

@router.get("/", response_model=List[UsuarioResponse])
def listar_usuarios(
    empresa_id: int, 
    departamento_id: int = None, 
    busca: str = None, 
    db: Session = Depends(get_db)
):
    query = db.query(Usuario).filter(Usuario.empresa_id == empresa_id)
    
    if departamento_id:
        query = query.filter(Usuario.departamento_id == departamento_id)
    if busca:
        query = query.filter(Usuario.nome.ilike(f"%{busca}%"))
        
    return query.all()

@router.put("/{usuario_id}", response_model=UsuarioResponse)
def atualizar_usuario(usuario_id: int, usuario_in: UsuarioUpdate, db: Session = Depends(get_db)):
    db_usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not db_usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    # Atualiza campos básicos
    for var, value in vars(usuario_in).items():
        if value is not None and var not in ['conexoes_ids']:
            setattr(db_usuario, var, value)
            
    # Atualiza senha se fornecida
    if usuario_in.senha:
        db_usuario.senha = get_password_hash(usuario_in.senha)
        
    # Atualiza conexões vinculadas (se fornecidas)
    if usuario_in.conexoes_ids is not None:
        # Remove vínculos antigos
        db.query(UsuarioConexao).filter(UsuarioConexao.usuario_id == usuario_id).delete()
        # Adiciona novos
        for conexao_id in usuario_in.conexoes_ids:
            conexao = db.query(Conexao).filter(Conexao.id == conexao_id, Conexao.empresa_id == db_usuario.empresa_id).first()
            if conexao:
                db.add(UsuarioConexao(usuario_id=usuario_id, conexao_id=conexao_id))
                
    db.commit()
    db.refresh(db_usuario)
    return db_usuario
    # =============================================================================
#  ARQUIVO.....: app/routers/usuarios_routers.py
#  AUTOR.......: Aldemir Queiroz
#  EMAIL.......: aldemir.queiroz@empresa.com
#  PROJETO.....: Sistema Multi-Tenant de Atendimento (WhatsApp Meta API)
#  MÓDULO......: Router de Usuários (FastAPI)
#  VERSÃO......: 2.1.0
#  CRIADO EM...: 2024-01-15
#  ATUALIZADO..: 2025-01-20
#  LINGUAGEM...: Python 3.11+
#  FRAMEWORK...: FastAPI + SQLAlchemy + Pydantic v2
# -----------------------------------------------------------------------------
#  DESCRIÇÃO...:
#      Endpoints REST para gerenciamento de usuários em ambiente multi-tenant.
#      Este router é a CAMADA DE TRANSPORTE: valida entrada via schemas,
#      aplica controle de acesso por nível, delega toda regra de negócio ao
#      UsuarioService e serializa a resposta. NÃO acessa o banco diretamente.
#
#  REGRA CRÍTICA DE NEGÓCIO:
#      🚨 Todo usuário DEVE estar vinculado a UMA empresa (empresa_id),
#         e essa empresa DEVE possuir id_telefone_meta válido e ativo
#         (número registrado na Meta / WhatsApp Business API).
#         Sem empresa + id_telefone_meta, o usuário NÃO pode ser criado
#         nem operar no sistema.
#
#  REGRAS ADICIONAIS:
#      - empresa_id é IMUTÁVEL após a criação (não existe no Update).
#      - Email é único POR EMPRESA (não global).
#      - Gestor/supervisor só enxerga e cria usuários da PRÓPRIA empresa.
#      - Admin global pode escolher a empresa no body.
#      - Delete é SOFT DELETE (mantém histórico e auditoria).
#
#  ENDPOINTS:
#      GET    /usuarios             -> lista paginada (nível >= supervisor)
#      GET    /usuarios/{id}        -> detalhe (nível >= supervisor)
#      POST   /usuarios             -> cria (nível >= gerente)
#      PUT    /usuarios/{id}        -> atualiza (nível >= gerente)
#      DELETE /usuarios/{id}        -> soft delete (nível administrador)
#
#  DEPENDÊNCIAS:
#      - app.database.get_db
#      - app.security.exigir_nivel / exigir_nivel_minimo / get_current_user
#      - app.services.usuario_service.UsuarioService
#      - app.schemas.usuario (UsuarioCreate, UsuarioUpdate, UsuarioResponse,
#                             UsuarioListResponse, UsuarioListItem)
#
#  USADO POR:
#      - app/main.py (include_router)
#
#  OBSERVAÇÕES:
#      - empresa_id NUNCA vem do query string em rotas de listagem/busca;
#        é sempre extraído do token (current_user.empresa_id) para evitar
#        spoofing entre tenants.
#      - Erros de negócio (404, 409, 422) são levantados pelo SERVICE e
#        propagados como HTTPException automaticamente.
#      - Paginação limitada a 100 itens por página para proteger o banco.
#
#  LICENÇA.....: Proprietária — uso interno. Proibida redistribuição.
# =============================================================================

"""
Router de Usuários — camada HTTP (FastAPI).

Este módulo faz a ponte entre o cliente (frontend/mobile) e a camada de
serviço (`UsuarioService`). Aqui só mora:

    - Declaração de rotas e verbos HTTP.
    - Dependências (DB, autenticação, nível de acesso).
    - Conversão de erros de negócio em HTTPException.
    - Documentação OpenAPI (summary, description, responses).

Toda a regra de negócio (hash de senha, validação de empresa + Meta,
vínculo de conexões, unicidade de email por empresa, isolamento
multi-tenant) vive em `UsuarioService`.
"""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.security import exigir_nivel, exigir_nivel_minimo, get_current_user
from app.services.usuario_service import UsuarioService
from app.schemas.usuario import (
    UsuarioCreate,
    UsuarioUpdate,
    UsuarioResponse,
    UsuarioListResponse,
    UsuarioListItem,
)


# =============================================================================
# CONFIGURAÇÃO DO ROUTER
# Prefixo, tags e respostas de erro comuns centralizados.
# =============================================================================

router = APIRouter(
    prefix="/usuarios",
    tags=["Usuários"],
    responses={
        401: {"description": "Não autenticado"},
        403: {"description": "Sem permissão para o nível exigido"},
        404: {"description": "Usuário não encontrado"},
        409: {"description": "Conflito (ex.: e-mail já cadastrado)"},
        422: {"description": "Empresa sem id_telefone_meta configurado na Meta"},
    },
)


# =============================================================================
# ENDPOINTS — LEITURA
# =============================================================================

@router.get(
    "/",
    response_model=UsuarioListResponse,
    summary="Lista usuários (paginado)",
    description=(
        "Retorna usuários da empresa do solicitante com paginação e filtros. "
        "O `empresa_id` é sempre extraído do token — nunca do query string — "
        "para garantir isolamento multi-tenant. "
        "Requer nível mínimo: **supervisor**."
    ),
    dependencies=[Depends(exigir_nivel_minimo("supervisor"))],
)
def listar_usuarios(
    nome: Optional[str] = Query(
        None, max_length=100, description="Filtro por nome (case-insensitive)"
    ),
    departamento_id: Optional[int] = Query(
        None, description="Filtro por departamento"
    ),
    canal_id: Optional[int] = Query(
        None, description="Filtro por canal"
    ),
    nivel: Optional[str] = Query(
        None, max_length=20,
        description="Nome do nível (atendente|supervisor|gerente|administrador)"
    ),
    status_: Optional[str] = Query(
        None, alias="status", max_length=20,
        description="Status do usuário (ativo|inativo|suspenso)"
    ),
    page: int = Query(1, ge=1, description="Página (1-based)"),
    limit: int = Query(20, ge=1, le=100, description="Itens por página (máx 100)"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Lista usuários paginados da empresa do usuário autenticado.

    Filtros opcionais: nome, departamento, canal, nível e status.
    Retorna um envelope com `total`, `page`, `limit` e `data`.
    """
    total, usuarios = UsuarioService.listar_usuarios(
        db=db,
        empresa_id=current_user.empresa_id,   # 🔒 sempre do token
        nome=nome,
        departamento_id=departamento_id,
        canal_id=canal_id,
        nivel=nivel,
        status=status_,
        page=page,
        limit=limit,
    )

    data: List[UsuarioListItem] = [
        UsuarioListItem(
            id=u.id,
            nome=u.nome,
            email=u.email,
            telefone=u.telefone,
            ativo=u.ativo,
            empresa_id=u.empresa_id,
            nivel_nome=u.nivel.nome if u.nivel else None,
            departamento_nome=u.departamento.nome if u.departamento else None,
            canal_nome=u.canal.nome if u.canal else None,
        )
        for u in usuarios
    ]

    return UsuarioListResponse(total=total, page=page, limit=limit, data=data)


@router.get(
    "/{usuario_id}",
    response_model=UsuarioResponse,
    summary="Busca usuário por ID",
    description=(
        "Retorna dados completos de um usuário, incluindo a empresa vinculada "
        "e o `id_telefone_meta` (número registrado na Meta/WhatsApp Business). "
        "Requer nível mínimo: **supervisor**."
    ),
    dependencies=[Depends(exigir_nivel_minimo("supervisor"))],
)
def buscar_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Busca um usuário pelo ID dentro da mesma empresa do solicitante."""
    usuario = UsuarioService.buscar_por_id(
        db=db,
        usuario_id=usuario_id,
        empresa_id=current_user.empresa_id,
    )
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado",
        )
    return usuario


# =============================================================================
# ENDPOINTS — ESCRITA
# =============================================================================

@router.post(
    "/",
    response_model=UsuarioResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cria usuário",
    description=(
        "Cria um usuário vinculado a uma empresa. A empresa **DEVE** possuir "
        "`id_telefone_meta` ativo (número registrado na Meta/WhatsApp Business "
        "API), caso contrário retorna 422. "
        "Gestor/supervisor só pode criar na própria empresa; admin global "
        "pode escolher a empresa no body. "
        "Requer nível mínimo: **gerente**."
    ),
    dependencies=[Depends(exigir_nivel_minimo("gerente"))],
)
def criar_usuario(
    usuario: UsuarioCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Cria um usuário.

    Regras aplicadas no `UsuarioService`:
        1. Empresa existe e está ativa.
        2. Empresa possui `id_telefone_meta` válido na Meta.
        3. Gestor/supervisor só cria na própria empresa.
        4. Email único dentro da empresa (multi-tenant).
        5. Senha recebe hash (bcrypt/argon2).
        6. Conexões são validadas contra a empresa.
    """
    # 🔒 Gestor/supervisor só cria na própria empresa
    if (
        not getattr(current_user, "is_admin_global", False)
        and usuario.empresa_id != current_user.empresa_id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você só pode criar usuários na sua própria empresa",
        )

    return UsuarioService.criar_usuario(
        db=db,
        dados=usuario,
        empresa_id=usuario.empresa_id,
    )


@router.put(
    "/{usuario_id}",
    response_model=UsuarioResponse,
    summary="Atualiza usuário",
    description=(
        "Atualiza parcialmente um usuário (apenas campos enviados). "
        "O vínculo com a empresa (`empresa_id`) é **imutável** e não existe "
        "no payload de atualização. "
        "Requer nível mínimo: **gerente**."
    ),
    dependencies=[Depends(exigir_nivel_minimo("gerente"))],
)
def atualizar_usuario(
    usuario_id: int,
    usuario: UsuarioUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Atualiza um usuário.

    - `empresa_id` NÃO pode ser alterado (imutável por design).
    - Email, se alterado, é revalidado como único na empresa.
    - `conexoes_ids`, se enviado, reconcilia os vínculos (remove antigos,
      adiciona novos validados contra a empresa).
    """
    atualizado = UsuarioService.atualizar_usuario(
        db=db,
        usuario_id=usuario_id,
        dados=usuario,
        empresa_id=current_user.empresa_id,
    )
    if not atualizado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado",
        )
    return atualizado


@router.delete(
    "/{usuario_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove usuário (soft delete)",
    description=(
        "Realiza **soft delete** do usuário (marca `ativo=False` e "
        "`status='inativo'`), preservando histórico e auditoria. "
        "Requer nível: **administrador**."
    ),
    dependencies=[Depends(exigir_nivel("administrador"))],
)
def deletar_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Remove (soft delete) um usuário da empresa do solicitante.

    Retorna 204 em caso de sucesso, 404 se não existir na empresa.
    """
    sucesso = UsuarioService.deletar_usuario(
        db=db,
        usuario_id=usuario_id,
        empresa_id=current_user.empresa_id,
    )
    if not sucesso:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado",
        )
    return None


# =============================================================================
# FIM DO ARQUIVO — app/routers/usuarios_routers.py
# =============================================================================