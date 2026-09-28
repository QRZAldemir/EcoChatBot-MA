# ==============================================================================
# PROJETO: EcoChatBot-MA
# MÓDULO: app.schemas.menu_schemas
# AUTOR: Aldemir Queiroz
# DATA: 2026-09-29
# VERSÃO: 2.1.0 (Padronização de canal_id e documentação de relacionamentos)
# ==============================================================================
"""
FUNCIONALIDADE
--------------
Define os Data Transfer Objects (DTOs) e esquemas de validação/serialização 
Pydantic para o domínio de Menu e MenuItem. Garante a integridade dos dados 
na fronteira da API, validando a estrutura de navegação (URA/Chatbot) antes 
de persistir no banco.

CAMADA
------
Camada de Apresentação / DTO (Data Transfer Object).
Atua como contrato entre o Router (FastAPI) e o Service (Lógica de Negócio).

SEGURANÇA E MULTI-TENANCY
-------------------------
A validação de que o `canal_id` ou `fallback_departamento_id` pertence à 
`empresa_id` da requisição é responsabilidade exclusiva da camada de Service. 
O schema valida apenas a integridade e o tipo dos dados de entrada/saída.
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field, ConfigDict


# ==============================================================================
# SCHEMAS DE ITEM DE MENU (MenuItem)
# ==============================================================================

class MenuItemCreate(BaseModel):
    """
    DTO para criação de um novo Item de Menu.
    
    RELACIONAMENTOS:
    - `menu_id`: Relaciona-se com a tabela `menus`. (Geralmente injetado pelo service).
    - `departamento_id`: Relaciona-se com a tabela `departamentos`. Define quem atenderá.
    - `roteiro_id`: Relaciona-se com a tabela `roteiros`. Opcional; se nulo, transfere direto.
    """
    ordem: int = Field(..., ge=1, description="Sequência de exibição do item")
    titulo: str = Field(..., max_length=150, description="Texto da opção (ex: '1. Financeiro')")
    descricao: Optional[str] = Field(None, description="Texto secundário explicativo")
    
    # RELACIONAMENTO: Vincula o item ao departamento que receberá o atendimento.
    departamento_id: int = Field(..., description="ID do departamento de destino")
    
    # RELACIONAMENTO: Vincula o item a um roteiro de respostas (opcional).
    roteiro_id: Optional[int] = Field(None, description="ID do roteiro a ser carregado")
    
    atalho: Optional[str] = Field(None, max_length=20, description="Tecla ou palavra-chave de atalho")
    transfere_direto: bool = Field(default=False, description="Se true, ignora roteiro e transfere")
    ativo: bool = Field(default=True)


class MenuItemResponse(BaseModel):
    """DTO de resposta para um Item de Menu."""
    id: int
    ordem: int
    titulo: str
    descricao: Optional[str] = None
    atalho: Optional[str] = None
    transfere_direto: bool
    ativo: bool
    
    # RELACIONAMENTOS REPRESENTADOS (via ID)
    departamento_id: int
    roteiro_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


# ==============================================================================
# SCHEMAS DE MENU (Menu)
# ==============================================================================

class MenuCreate(BaseModel):
    """
    DTO para criação de um novo Menu.
    
    RELACIONAMENTOS:
    - `canal_id`: Relaciona-se com a tabela `canais`. Se nulo, o menu é o padrão (default) da empresa.
    - `fallback_departamento_id`: Relaciona-se com a tabela `departamentos`. Destino em caso de erro/timeout.
    """
    nome: str = Field(..., max_length=120, description="Nome identificador do menu")
    saudacao: Optional[str] = Field(None, description="Mensagem de boas-vindas")
    rodape: Optional[str] = Field(None, description="Mensagem de rodapé ou instrução de fallback")
    
    tempo_espera_seg: int = Field(default=300, ge=10, description="Tempo máximo de inatividade (segundos)")
    tentativas_max: int = Field(default=3, ge=1, description="Número máximo de tentativas antes do fallback")
    
    # RELACIONAMENTO: Vincula o menu a um canal específico (ex: WhatsApp da Unidade A).
    canal_id: Optional[int] = Field(None, description="ID do Canal vinculado (nulo para menu default da empresa)")
    
    # RELACIONAMENTO: Vincula ao departamento que receberá o atendimento em caso de falha na URA.
    fallback_departamento_id: Optional[int] = Field(None, description="ID do departamento de fallback")
    
    ativo: bool = Field(default=True)
    itens: List[MenuItemCreate] = Field(default=[], description="Lista de opções do menu")


class MenuUpdate(BaseModel):
    """DTO para atualização parcial de um Menu."""
    nome: Optional[str] = Field(None, max_length=120)
    saudacao: Optional[str] = None
    rodape: Optional[str] = None
    tempo_espera_seg: Optional[int] = Field(None, ge=10)
    tentativas_max: Optional[int] = Field(None, ge=1)
    canal_id: Optional[int] = None
    fallback_departamento_id: Optional[int] = None
    ativo: Optional[bool] = None


class MenuResponse(BaseModel):
    """
    DTO de resposta padrão para listagens de Menu.
    """
    id: int
    nome: str
    saudacao: Optional[str] = None
    rodape: Optional[str] = None
    tempo_espera_seg: int
    tentativas_max: int
    ativo: bool
    
    # RELACIONAMENTOS REPRESENTADOS (via ID)
    canal_id: Optional[int] = None
    fallback_departamento_id: Optional[int] = None
    
    itens: List[MenuItemResponse] = []

    model_config = ConfigDict(from_attributes=True)


class MenuDetalhado(BaseModel):
    """
    DTO de resposta para consulta individual de Menu, incluindo metadados de criação.
    """
    id: int
    nome: str
    saudacao: Optional[str] = None
    rodape: Optional[str] = None
    tempo_espera_seg: int
    tentativas_max: int
    ativo: bool
    
    # RELACIONAMENTOS REPRESENTADOS (via ID)
    canal_id: Optional[int] = None
    fallback_departamento_id: Optional[int] = None
    
    criado_em: str
    atualizado_em: str
    
    itens: List[MenuItemResponse] = []

    model_config = ConfigDict(from_attributes=True)