# ==============================================================================
# PROJETO: EcoChatBot-MA
# MÓDULO: app.schemas.contato_schemas
# AUTOR: Aldemir Queiroz
# DATA: 2026-09-29
# VERSÃO: 3.1.0 (Padronização de canal_id e documentação de relacionamentos)
# ==============================================================================
"""
FUNCIONALIDADE
--------------
Define os Data Transfer Objects (DTOs) para o domínio de Contatos e, 
especificamente, para o vínculo de identidade por canal (ContatoCanal). 
Isola a lógica de múltiplos identificadores (ex: mesmo cliente no WhatsApp 
e no Telegram) da entidade principal de Contato.

CAMADA
------
Camada de Apresentação / DTO (Data Transfer Object).
Garante que a vinculação de um identificador de canal a um contato respeite 
as regras de formato antes de atingir a camada de Service.

SEGURANÇA E MULTI-TENANCY
-------------------------
A validação de que o `canal_id` pertence à `empresa_id` da requisição é 
responsabilidade exclusiva da camada de Service. O schema valida apenas 
a unicidade e o formato do identificador.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


# ==============================================================================
# SCHEMAS DE VÍNCULO CONTATO-CANAL (ContatoCanal)
# ==============================================================================

class ContatoCanalCreate(BaseModel):
    """
    DTO para criação de um novo vínculo de identidade por canal.
    
    RELACIONAMENTOS:
    - `contato_id`: Relaciona-se com a tabela `contatos`. O cliente mestre.
    - `canal_id`: Relaciona-se com a tabela `canais`. O canal específico onde 
      este identificador foi encontrado (ex: instância WhatsApp X).
    """
    # RELACIONAMENTO: Vincula este registro ao contato mestre.
    contato_id: int = Field(..., description="ID do contato mestre")
    
    # RELACIONAMENTO: Vincula este identificador a um canal contratado específico.
    canal_id: int = Field(..., description="ID do Canal vinculado (ex: instância WhatsApp)")
    
    identificador: str = Field(
        ..., 
        max_length=120, 
        description="Identificador único no canal (ex: remoteJid '5511999999999@s.whatsapp.net')"
    )
    
    push_name: Optional[str] = Field(
        None, 
        max_length=150, 
        description="Nome exibido pelo aplicativo no canal (ex: nome salvo no WhatsApp do cliente)"
    )


class ContatoCanalResponse(BaseModel):
    """
    DTO de resposta para o vínculo Contato-Canal.
    """
    id: int
    
    # RELACIONAMENTOS REPRESENTADOS (via ID)
    contato_id: int
    canal_id: int
    
    identificador: str
    push_name: Optional[str] = None
    criado_em: datetime
    atualizado_em: datetime

    model_config = ConfigDict(from_attributes=True)


# ==============================================================================
# SCHEMAS DE CONTATO (Resumo para uso aninhado)
# ==============================================================================

class ContatoResumo(BaseModel):
    """
    DTO de representação resumida de um Contato.
    Utilizado como objeto aninhado em respostas de Atendimento ou Canal.
    """
    id: int
    nome: str
    telefone_principal: Optional[str] = None
    email: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)