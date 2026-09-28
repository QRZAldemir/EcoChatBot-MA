# ==============================================================================
# PROJETO: EcoChatBot-MA
# MÓDULO: app.core.scope
# AUTOR: Aldemir Queiroz
# DATA: 2026-09-27
# VERSÃO: 1.0.0
# ==============================================================================
"""
FUNCIONALIDADE
--------------
Centraliza as validações de escopo e isolamento de dados (Data Isolation) 
para garantir a segurança multi-tenant em todo o backend.

OBJETIVO
--------
Prevenir vulnerabilidades de IDOR (Insecure Direct Object Reference) e 
vazamento de dados entre tenants (Cross-Tenant Data Leakage). 

REGRA DE OURO:
Nenhuma operação de leitura (GET) ou escrita (POST/PATCH/DELETE) em recursos 
sensíveis (Atendimentos, Conexões, Canais, Mensagens) deve ocorrer sem a 
validação explícita de que o recurso pertence à `empresa_id` do contexto atual.

FLUXO DE USO:
1. O Router injeta `CurrentEmpresa` (via Depends).
2. O Service chama uma função deste módulo antes de manipular o recurso.
3. Se a validação falhar, uma exceção de domínio é levantada, abortando a operação.
"""

import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import RecursoNaoEncontradoError, AcessoNegadoError
# Ajuste os imports dos modelos conforme a estrutura exata do seu projeto
from app.models.atendimento_models import Atendimento
from app.models.conexao_models import Conexao

logger = logging.getLogger(__name__)


async def validar_e_obter_atendimento_seguro(
    db: AsyncSession, 
    atendimento_id: int, 
    empresa_id: int
) -> Atendimento:
    """
    Busca um atendimento GARANTINDO que ele pertence à empresa especificada.
    
    :param db: Sessão assíncrona do SQLAlchemy.
    :param atendimento_id: ID do atendimento a ser buscado.
    :param empresa_id: ID da empresa (tenant) do usuário autenticado.
    :return: Instância do modelo Atendimento.
    :raises RecursoNaoEncontradoError: Se o atendimento não existir ou não pertencer à empresa.
    """
    stmt = select(Atendimento).where(
        Atendimento.id == atendimento_id,
        Atendimento.empresa_id == empresa_id  # <--- A BLINDAGEM MULTI-TENANT
    )
    
    result = await db.execute(stmt)
    atendimento = result.scalar_one_or_none()
    
    if not atendimento:
        # Log de auditoria: tentativa de acesso a recurso fora do escopo
        logger.warning(
            f"Tentativa de acesso a atendimento fora do escopo. "
            f"Atendimento ID: {atendimento_id}, Empresa Contexto: {empresa_id}"
        )
        # Mensagem genérica para não vazar informação sobre a existência do ID em outro tenant
        raise RecursoNaoEncontradoError("Atendimento não encontrado ou acesso negado.")
    
    return atendimento


async def validar_conexao_da_empresa(
    db: AsyncSession, 
    conexao_id: int, 
    empresa_id: int
) -> Conexao:
    """
    Valida se a conexão (instância WhatsApp/PABX/Telegram) pertence ao tenant.
    
    :param db: Sessão assíncrona do SQLAlchemy.
    :param conexao_id: ID da conexão a ser validada.
    :param empresa_id: ID da empresa (tenant) do usuário autenticado.
    :return: Instância do modelo Conexao.
    :raises AcessoNegadoError: Se a conexão não existir ou não pertencer à empresa.
    """
    stmt = select(Conexao).where(
        Conexao.id == conexao_id,
        Conexao.empresa_id == empresa_id  # <--- A BLINDAGEM MULTI-TENANT
    )
    
    result = await db.execute(stmt)
    conexao = result.scalar_one_or_none()
    
    if not conexao:
        logger.warning(
            f"Tentativa de uso de conexão fora do escopo. "
            f"Conexão ID: {conexao_id}, Empresa Contexto: {empresa_id}"
        )
        raise AcessoNegadoError("Conexão inválida ou não pertence a esta empresa.")
    
    return conexao


async def validar_canal_da_empresa(
    db: AsyncSession, 
    canal_id: int, 
    empresa_id: int
) -> 'Canal':  # Tipo string para evitar importação circular se não for estritamente necessário
    """
    Valida se um canal de atendimento pertence ao tenant.
    (Implementação similar às anteriores, pronta para uso em criação de atendimentos).
    """
    from app.models.canal_models import Canal
    
    stmt = select(Canal).where(
        Canal.id == canal_id,
        Canal.empresa_id == empresa_id
    )
    
    result = await db.execute(stmt)
    canal = result.scalar_one_or_none()
    
    if not canal:
        logger.warning(
            f"Tentativa de uso de canal fora do escopo. "
            f"Canal ID: {canal_id}, Empresa Contexto: {empresa_id}"
        )
        raise AcessoNegadoError("Canal inválido ou não pertence a esta empresa.")
    
    return canal