"""
================================================================================
PROJETO: EcoChatBot-MA - Omnichannel SaaS
MÓDULO: routers/conexoes.py
AUTOR: Aldemir Queiroz
DATA: 2026-09-29
VERSÃO: 2.0.0 - Endpoints de Status e Reconexão em Tempo Real
================================================================================

PROPÓSITO:
Gerenciar o ciclo de vida das instâncias WhatsApp/WABA via Evolution API.
Implementa monitoramento em tempo real e reconexão automática.

ENDPOINTS IMPLEMENTADOS:
    GET    /api/v1/conexoes              → Listar todas as conexões
    GET    /api/v1/conexoes/{id}         → Obter detalhes de uma conexão
    GET    /api/v1/conexoes/{id}/status  → Status em tempo real ⭐ NOVO
    POST   /api/v1/conexoes/{id}/reconectar → Reconectar instância ⭐ NOVO
    POST   /api/v1/conexoes              → Criar nova conexão
    PUT    /api/v1/conexoes/{id}         → Atualizar conexão
    DELETE /api/v1/conexoes/{id}         → Deletar conexão
    POST   /api/v1/conexoes/{id}/desconectar → Logout
================================================================================
"""

import logging
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ResourceNotFoundError, TenantIsolationError
from app.deps import get_current_empresa, get_db
from app.models.conexao_models import Conexao
from app.models.enums import StatusConexao
from app.schemas.conexao import (
    ConexaoCreate,
    ConexaoReconectarResponse,
    ConexaoStatusResponse,
    ConexaoUpdate,
)
from app.services.evolution_api_client import EvolutionApiClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/conexoes", tags=["Conexões - Status e Reconexão"])


# ==============================================================================
# ENDPOINT: STATUS EM TEMPO REAL
# ==============================================================================

@router.get(
    "/{conexao_id}/status",
    response_model=ConexaoStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Obter status em tempo real da conexão",
    description=(
        "Consulta o estado atual da conexão com a Evolution API.\n\n"
        "**Estados possíveis:**\n"
        "- `desconectado`: Instância não está conectada\n"
        "- `conectando`: Tentativa de conexão em andamento\n"
        "- `conectado`: Sessão ativa e funcional\n"
        "- `aguardando_qrcode`: Aguardando leitura do QR Code\n"
        "- `erro`: Falha na conexão (verificar mensagem)\n\n"
        "Este endpoint é ideal para polling no frontend Angular."
    ),
    responses={
        200: {"description": "Status obtido com sucesso"},
        404: {"description": "Conexão não encontrada"},
        403: {"description": "Acesso negado (violação de tenant)"},
        502: {"description": "Erro na comunicação com Evolution API"},
    },
)
async def get_conexao_status(
    conexao_id: int,
    db: AsyncSession = Depends(get_db),
    empresa_atual = Depends(get_current_empresa),
):
    """
    **Endpoint de Status em Tempo Real**
    
    Permite que o Angular consulte periodicamente (polling) o estado da
    instância para exibir ao usuário se está:
    - Aguardando QR Code
    - Conectado
    - Desconectado
    - Com erro
    
    **Fluxo:**
    1. Busca o registro de conexão no banco (anti-IDOR: filtra por empresa_id)
    2. Consulta a Evolution API para obter o estado real
    3. Atualiza o registro local se necessário
    4. Retorna status completo, incluindo QR Code se disponível
    """
    # 1. Buscar conexão no banco (com isolamento de tenant)
    query = select(Conexao).where(
        Conexao.id == conexao_id,
        Conexao.empresa_id == empresa_atual.id,  # Anti-IDOR
    )
    result = await db.execute(query)
    conexao = result.scalar_one_or_none()
    
    if not conexao:
        raise ResourceNotFoundError(
            recurso="Conexão",
            identificador=str(conexao_id),
        )
    
    # 2. Consultar Evolution API para status real-time
    evolution_client = EvolutionApiClient(db, empresa_atual.id)
    
    try:
        status_api = await evolution_client.get_connection_state(
            instance_name=f"instancia_{conexao.id}"
        )
        
        # 3. Mapear estado da Evolution API para nosso enum
        state = status_api.get("state", "close")
        
        if state == "open":
            novo_status = StatusConexao.CONECTADO
            mensagem = "Conexão estabelecida com sucesso"
        elif state == "connecting":
            novo_status = StatusConexao.CONECTANDO
            mensagem = "Estabelecendo conexão..."
        else:  # close
            # Verificar se tem QR Code disponível
            qr_code = status_api.get("qrCode", {})
            if qr_code and qr_code.get("base64"):
                novo_status = StatusConexao.AGUARDANDO_QRCODE
                mensagem = "Aguardando leitura do QR Code"
            else:
                novo_status = StatusConexao.DESCONECTADO
                mensagem = "Desconectado"
        
        # 4. Atualizar registro local se status mudou
        if conexao.status != novo_status.value:
            conexao.status = novo_status.value
            conexao.mensagem = mensagem
            conexao.encerrada_em = datetime.utcnow() if novo_status != StatusConexao.CONECTADO else None
            
            if novo_status == StatusConexao.CONECTADO:
                conexao.iniciada_em = datetime.utcnow()
            
            await db.commit()
            await db.refresh(conexao)
        
        # 5. Montar resposta
        response_data = {
            "id": conexao.id,
            "canal_contratado_id": conexao.canal_contratado_id,
            "status": novo_status,
            "mensagem": mensagem,
            "iniciada_em": conexao.iniciada_em,
            "encerrada_em": conexao.encerrada_em,
            "tentativas": conexao.tentativas,
            "instance_id": f"instancia_{conexao.id}",
        }
        
        # Incluir QR Code se disponível
        if novo_status == StatusConexao.AGUARDANDO_QRCODE:
            response_data["qr_code"] = qr_code.get("base64")
        
        return ConexaoStatusResponse(**response_data)
        
    except HTTPException:
        # Se a Evolution API falhar, retorna status do banco
        logger.warning(
            "Falha ao consultar Evolution API para conexao_id=%d. Retornando status local.",
            conexao_id,
        )
        return ConexaoStatusResponse(
            id=conexao.id,
            canal_contratado_id=conexao.canal_contratado_id,
            status=StatusConexao(conexao.status),
            mensagem=conexao.mensagem or "Status indisponível",
            iniciada_em=conexao.iniciada_em,
            encerrada_em=conexao.encerrada_em,
            tentativas=conexao.tentativas,
        )


# ==============================================================================
# ENDPOINT: RECONEXÃO
# ==============================================================================

@router.post(
    "/{conexao_id}/reconectar",
    response_model=ConexaoReconectarResponse,
    status_code=status.HTTP_200_OK,
    summary="Reconectar instância",
    description=(
        "Solicita reconexão da instância com a Evolution API.\n\n"
        "**O que acontece:**\n"
        "1. A instância é desconectada (logout suave)\n"
        "2. Uma nova sessão é iniciada\n"
        "3. Se necessário, um novo QR Code é gerado\n"
        "4. O registro NO BANCO É PRESERVADO (não é deletado)\n\n"
        "Ideal para quando o WhatsApp cai e precisa reconectar rapidamente."
    ),
    responses={
        200: {"description": "Reconexão solicitada com sucesso"},
        404: {"description": "Conexão não encontrada"},
        403: {"description": "Acesso negado (violação de tenant)"},
        502: {"description": "Erro na comunicação com Evolution API"},
    },
)
async def reconectar_conexao(
    conexao_id: int,
    db: AsyncSession = Depends(get_db),
    empresa_atual = Depends(get_current_empresa),
):
    """
    **Endpoint de Reconexão**
    
    Permite que o usuário solicite manualmente uma reconexão sem precisar
    deletar e recriar a instância. Isso preserva:
    - Histórico de mensagens
    - Configurações da instância
    - Webhooks registrados
    - Relacionamento com o CanalContratado
    
    **Diferença entre RECONNECT e DELETE+CREATE:**
    - RECONNECT: Mantém o registro, apenas renova a sessão
    - DELETE+CREATE: Apaga tudo e cria do zero (perde histórico)
    """
    # 1. Buscar conexão (com isolamento de tenant)
    query = select(Conexao).where(
        Conexao.id == conexao_id,
        Conexao.empresa_id == empresa_atual.id,  # Anti-IDOR
    )
    result = await db.execute(query)
    conexao = result.scalar_one_or_none()
    
    if not conexao:
        raise ResourceNotFoundError(
            recurso="Conexão",
            identificador=str(conexao_id),
        )
    
    # 2. Verificar se já está conectando/conectado
    if conexao.status in [StatusConexao.CONECTANDO.value, StatusConexao.CONECTADO.value]:
        logger.info("Conexão %d já está ativa. Ignorando reconexão.", conexao_id)
        return ConexaoReconectarResponse(
            mensagem="Conexão já está ativa. Reconexão não necessária.",
            status=StatusConexao(conexao.status),
        )
    
    # 3. Atualizar status para "conectando"
    conexao.status = StatusConexao.CONECTANDO.value
    conexao.mensagem = "Iniciando reconexão..."
    conexao.tentativas += 1
    conexao.iniciada_em = datetime.utcnow()
    
    await db.commit()
    
    # 4. Solicitar reconexão na Evolution API
    evolution_client = EvolutionApiClient(db, empresa_atual.id)
    instance_name = f"instancia_{conexao.id}"
    
    try:
        # Primeiro tenta reconectar
        await evolution_client.reconnect(instance_name)
        
        # Atualiza status
        conexao.status = StatusConexao.CONECTANDO.value
        conexao.mensagem = "Reconexão solicitada. Aguardando QR Code ou conexão automática."
        await db.commit()
        await db.refresh(conexao)
        
        logger.info("Reconexão solicitada para conexao_id=%d", conexao_id)
        
        return ConexaoReconectarResponse(
            mensagem="Reconexão solicitada com sucesso. Aguarde o QR Code ou conexão automática.",
            status=StatusConexao.CONECTANDO,
            reconectado_em=conexao.iniciada_em,
        )
        
    except HTTPException as e:
        # Se falhar, tenta gerar QR Code do zero
        logger.warning(
            "Reconnect falhou para conexao_id=%d. Tentando gerar QR Code...",
            conexao_id,
        )
        
        try:
            await evolution_client.connect(instance_name)
            
            conexao.status = StatusConexao.AGUARDANDO_QRCODE.value
            conexao.mensagem = "QR Code gerado. Aguardando leitura."
            await db.commit()
            await db.refresh(conexao)
            
            return ConexaoReconectarResponse(
                mensagem="QR Code gerado com sucesso. Escaneie para conectar.",
                status=StatusConexao.AGUARDANDO_QRCODE,
                reconectado_em=conexao.iniciada_em,
            )
            
        except Exception as e2:
            logger.exception("Falha ao reconectar conexao_id=%d: %s", conexao_id, str(e2))
            
            conexao.status = StatusConexao.ERRO.value
            conexao.mensagem = f"Falha na reconexão: {str(e2)}"
            await db.commit()
            
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Falha na reconexão: {str(e2)}",
            ) from e2


# ==============================================================================
# OUTROS ENDPOINTS (CRUD básico)
# ==============================================================================

@router.get("/", response_model=List[ConexaoStatusResponse])
async def listar_conexoes(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    empresa_atual = Depends(get_current_empresa),
):
    """Lista todas as conexões da empresa."""
    query = select(Conexao).where(
        Conexao.empresa_id == empresa_atual.id
    ).offset(skip).limit(limit)
    
    result = await db.execute(query)
    conexoes = result.scalars().all()
    
    return [
        ConexaoStatusResponse(
            id=c.id,
            canal_contratado_id=c.canal_contratado_id,
            status=StatusConexao(c.status),
            mensagem=c.mensagem,
            iniciada_em=c.iniciada_em,
            encerrada_em=c.encerrada_em,
            tentativas=c.tentativas,
        )
        for c in conexoes
    ]


@router.post("/", status_code=status.HTTP_201_CREATED)
async def criar_conexao(
    data: ConexaoCreate,
    db: AsyncSession = Depends(get_db),
    empresa_atual = Depends(get_current_empresa),
):
    """Cria nova conexão com a Evolution API."""
    evolution_client = EvolutionApiClient(db, empresa_atual.id)
    
    # Criar instância na Evolution API
    instance_data = await evolution_client.create_instance(
        instance_name=f"instancia_{data.canal_contratado_id}",
        webhook_url=data.webhook_url,
    )
    
    # Criar registro no banco
    nova_conexao = Conexao(
        canal_contratado_id=data.canal_contratado_id,
        empresa_id=empresa_atual.id,
        status=StatusConexao.AGUARDANDO_QRCODE.value,
        mensagem="Instância criada. Aguardando leitura do QR Code.",
        iniciada_em=datetime.utcnow(),
    )
    
    db.add(nova_conexao)
    await db.commit()
    await db.refresh(nova_conexao)
    
    return {"id": nova_conexao.id, "message": "Conexão criada com sucesso"}


@router.delete("/{conexao_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deletar_conexao(
    conexao_id: int,
    db: AsyncSession = Depends(get_db),
    empresa_atual = Depends(get_current_empresa),
):
    """Deleta conexão (apenas se necessário)."""
    query = select(Conexao).where(
        Conexao.id == conexao_id,
        Conexao.empresa_id == empresa_atual.id,
    )
    result = await db.execute(query)
    conexao = result.scalar_one_or_none()
    
    if not conexao:
        raise ResourceNotFoundError(recurso="Conexão", identificador=str(conexao_id))
    
    # Deletar na Evolution API primeiro
    evolution_client = EvolutionApiClient(db, empresa_atual.id)
    await evolution_client.delete_instance(f"instancia_{conexao.id}")
    
    # Deletar no banco (soft delete via mixin)
    await db.delete(conexao)
    await db.commit()