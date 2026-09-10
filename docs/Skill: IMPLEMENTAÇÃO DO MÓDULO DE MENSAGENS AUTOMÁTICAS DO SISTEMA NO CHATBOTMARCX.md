SKILL: IMPLEMENTAÇÃO DO MÓDULO DE MENSAGENS AUTOMÁTICAS DO SISTEMA NO CHATBOTMARCX
1. CONTEXTO E OBJETIVO
Você atuará como Arquiteto de Software Sênior especialista em Angular, Python (FastAPI), APIs RESTful e arquitetura multi-tenant. Esta skill tem como objetivo guiar a implementação do Módulo de Mensagens Automáticas do Sistema no ChatBotMarcx, que será integrado ao modulo_mensagem.html existente.
1.1. Diferença Crítica Entre os Módulos de Mensagem
É fundamental compreender a distinção entre os dois módulos de mensagens do sistema:
Critério
Mensagens Interativas (Módulo Existente)
Mensagens Automáticas do Sistema (Novo Módulo)
Propósito
Templates criados pelo usuário para menus de fluxo
Mensagens pré-definidas pelo sistema para eventos automáticos
Vinculação
Departamento + Canal de Atendimento
Tipo de evento do sistema (fixo)
Criação
Usuário cria quantas quiser
24 tipos pré-definidos, editáveis mas não deletáveis
Conteúdo
Texto + mídia + botões interativos
Apenas texto (com variáveis dinâmicas)
Exemplos
"SAUDAÇÕES", "AGENDAMENTO CIRÚRGICO"
"Boas-vindas", "Transferência para atendente", "Fila de atendimento"
Trigger
Cliente escolhe opção no menu
Evento do sistema (entrada na fila, transferência, etc.)
1.2. Stack Tecnológica
Frontend: Angular 17+ (Standalone Components)
Backend: Python com FastAPI
Banco de Dados: PostgreSQL 15+
ORM: SQLAlchemy 2.0
Validação: Pydantic v2
2. REFERÊNCIA VISUAL E FUNCIONAL (BASEADO NOS PRINTS)
2.1. Tela de Listagem (Print 1 e 4)
Filtros no topo:
Tipo: Dropdown com opção "Selecione" (filtro por tipo de mensagem)
Status: Dropdown com opção "Ativo" (filtro por status)
Botão "+ Novo" em vermelho no canto superior direito
Tabela "Mensagens automáticas do sistema":
Colunas: Tipo | Mensagem | Status | Ações
Status exibido como badge verde "✓ ATIVO"
Ação: ícone de lápis vermelho (editar)
Paginação completa: « < 1 2 3 > »
Rodapé: "Listado X de 24 registro(s)"
Tipos de mensagens identificados (24 no total):
Página 1 (10 tipos):
Boas-vindas → "👻 Seja bem-vindo!"
Encerrar → "Atendimento encerrado."
Opção inválida → "Opção inválida."
Pesquisa → (vazio no print)
Transferência para departamento → "Você foi transferido para o departamento %nomeDepartamento%. Caso deseje finalizar o atendimento digite: encerrar atendimento e confirme"
Transferência para atendente → "Você foi transferido para o atendente %nomeAtendente%.*"
Solicitar atendimento → "Estamos transferindo para um atendente."
Protocolo de atendimento → "Seu protocolo de atendimento: %protocolo%."
Notificação de contato → "Cliente entrou em contato e solicitou atendimento. Protocolo: %protocolo% Nome do Cliente: %nomeCliente%"
Fora do horário de atendimento → " Desculpe, estamos fora do horário de atendimento."
Página 3 (4 tipos visíveis):
21. Fora do turno do departamento → "👻 O departamento %nomeDepartamento% está indisponível no momento. O tempo de espera pode ser maior, pedimos que aguarde alguns instantes."
22. Fora do turno do atendente → "👻 O atendente %nomeAtendente% está indisponível no momento. O tempo de espera pode ser maior, pedimos que aguarde alguns instantes."
23. Fila de atendimento → "Você está na posição %posicao% da fila de atendimento."
24. Usuário indisponível com atendimento em andamento → "🔴 Atendente %nomeAtendente% está indisponível no momento. Sua mensagem será respondida em breve."
2.2. Tela de Formulário (Print 2)
Título: "Mensagem do sistema"
Campos:
Tipo*: Dropdown obrigatório (ex: "Boas-vindas")
Mensagem: Textarea grande com suporte a emojis e formatação WhatsApp (negrito com *, emojis como 👻, 🔴)
Botão de emoji (😊) ao lado direito do textarea
Checkbox "Ativo": Habilita/desabilita a mensagem (marcado por padrão)
Rodapé:
Botão "Voltar" (vermelho, esquerda)
Botão "Salvar" (vermelho com ícone de disquete, direita)
2.3. Navegação (Print 3)
Ícone de envelope com texto "Sistema" no menu lateral, indicando que este módulo é acessado como uma subseção do módulo de mensagens.
3. MAPEAMENTO COMPLETO DAS 24 MENSAGENS AUTOMÁTICAS
Baseado nos prints e na lógica de um ChatBot completo, os 24 tipos de mensagens automáticas são:
3.1. Mensagens de Início e Fim de Atendimento
Boas-vindas - Saudação inicial quando cliente inicia conversa
Encerrar - Confirmação de encerramento do atendimento
Saudação inicial - Primeira mensagem após boas-vindas (opcional)
Encerramento por inatividade - Quando cliente fica sem responder por tempo definido
3.2. Mensagens de Navegação e Validação
Opção inválida - Quando cliente digita opção não existente
Confirmação de opção - Confirma escolha do cliente no menu
Aguardando resposta - Quando sistema espera input do cliente
Mensagem de erro geral - Erros técnicos não mapeados
3.3. Mensagens de Transferência
Transferência para departamento - Cliente transferido entre departamentos
Transferência para atendente - Cliente transferido para atendente humano
Solicitar atendimento - Cliente solicitou atendimento humano
Retorno de atendimento - Atendente retorna após pausa
3.4. Mensagens de Protocolo e Notificação
Protocolo de atendimento - Gera e informa número de protocolo
Notificação de contato - Notifica atendente sobre novo cliente
Confirmação de agendamento - Confirma agendamento realizado
Cancelamento de agendamento - Confirma cancelamento
3.5. Mensagens de Fila e Espera
Fila de atendimento - Informa posição na fila
Tempo de espera excedido - Quando espera ultrapassa tempo estimado
Fora do horário de atendimento - Fora do horário comercial geral
Fora do turno do departamento - Departamento específico fora do turno
Fora do turno do atendente - Atendente específico fora do turno
Usuário indisponível com atendimento em andamento - Atendente ocupado
3.6. Mensagens de Pesquisa e Feedback
Pesquisa - Solicita avaliação do atendimento (NPS/CSAT)
Agradecimento final - Agradece após pesquisa respondida
4. ENTIDADE: SYSTEM_MESSAGE (MENSAGEM DO SISTEMA)
4.1. Atributos da Entidade

SystemMessage:
├── id: UUID (primary key, auto-gerado)
├── tenant_id: UUID (foreign key → Tenant, isolamento multi-tenant)
├── type: Enum (24 valores fixos, ver lista acima)
├── content: Text (conteúdo da mensagem, max 1024 chars)
├── is_active: Boolean (default True)
├── created_at: DateTime (auto, timezone-aware)
├── updated_at: DateTime (auto, onupdate)
└── created_by: UUID (foreign key → User, quem editou pela última vez)

4.2. Constraints e Regras
Unique Constraint: (tenant_id, type) - cada tenant tem exatamente uma mensagem de cada tipo
Não deletável: Mensagens do sistema não podem ser deletadas, apenas desativadas (soft delete via is_active = false)
Não criável via API: Os 24 tipos são criados automaticamente no seed inicial do tenant; a API permite apenas GET, PUT, PATCH
4.3. Variáveis Dinâmicas Suportadas
As mensagens podem conter variáveis que serão substituídas em tempo de execução pelo motor do ChatBot:
Variável
Descrição
Exemplo de Uso
%nomeCliente%
Nome do cliente
"Olá %nomeCliente%, bem-vindo!"
%nomeAtendente%
Nome do atendente
"Transferido para %nomeAtendente%"
%nomeDepartamento%
Nome do departamento
"Departamento %nomeDepartamento%"
%protocolo%
Número do protocolo
"Protocolo: %protocolo%"
%posicao%
Posição na fila
"Posição %posicao% da fila"
%tempoEspera%
Tempo estimado de espera
"Tempo estimado: %tempoEspera%"
%quantidadeMensagens%
Qtd de mensagens na fila
"%quantidadeMensagens% na fila"
%data%
Data atual formatada
"Data: %data%"
%hora%
Hora atual formatada
"Hora: %hora%"
%nomeEmpresa%
Nome da empresa (tenant)
"Obrigado por contactar %nomeEmpresa%"
%linkAvaliacao%
URL de pesquisa de satisfação
"Avalie: %linkAvaliacao%"
%numeroProtocolo%
Alias para %protocolo%
"Nº %numeroProtocolo%"
Formatação WhatsApp suportada:
*texto* → negrito
_texto_ → itálico
~texto~ → tachado
`texto` → monoespaçado
Emojis Unicode (, 🔴, ✅, etc.)
5. DESIGN DA API RESTFUL (PYTHON/FASTAPI)
5.1. Endpoints Principais
GET /api/v1/system-messages

Descrição: Lista todas as mensagens automáticas do sistema do tenant atual.
Query Parameters:
type: string (opcional) - filtro por tipo específico
is_active: boolean (opcional) - filtro por status
search: string (opcional) - busca textual no conteúdo
page: integer (default 1, min 1)
limit: integer (default 24, max 50)
sort_by: string (default 'type')
sort_order: enum 'asc' | 'desc' (default 'asc')
Headers:
Authorization: Bearer <JWT>
X-Tenant-ID: <uuid>
Response 200 OK:

{
  "data": [
    {
      "id": "uuid-1",
      "type": "BOAS_VINDAS",
      "type_label": "Boas-vindas",
      "content": " Seja bem-vindo!",
      "is_active": true,
      "created_at": "2026-07-02T14:30:00Z",
      "updated_at": "2026-07-02T14:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 24,
    "total": 24,
    "total_pages": 1
  },
  "display_info": "Listado 24 de 24 registro(s)"
}

GET /api/v1/system-messages/{message_id}
Descrição: Retorna detalhes de uma mensagem específica.
Path Parameters:
message_id: UUID
Response 200 OK: Objeto SystemMessage completo
Response 404 Not Found: Mensagem não existe ou não pertence ao tenant
PUT /api/v1/system-messages/{message_id}
Descrição: Atualiza completamente uma mensagem do sistema (substituição total).
Path Parameters:
message_id: UUID
Body Parameters (JSON):
{
  "type": "BOAS_VINDAS",
  "content": "👻 Seja bem-vindo ao nosso atendimento!",
  "is_active": true
}

Headers:
Authorization: Bearer <JWT>
X-Tenant-ID: <uuid>
Content-Type: application/json
Response 200 OK: Mensagem atualizada
Response 400 Bad Request: Conteúdo excede 1024 chars ou tipo inválido
Response 404 Not Found: Mensagem não existe
Response 409 Conflict: Tipo já existe para outro registro (não aplicável aqui pois é unique por tenant)
Idempotência: Sim (mesma requisição produz mesmo estado final)

PATCH /api/v1/system-messages/{message_id}
Descrição: Atualização parcial (ex: apenas ativar/desativar, ou apenas mudar conteúdo).
Path Parameters:
message_id: UUID
Body Parameters (JSON parcial):
{
  "is_active": false
}
{
  "content": "Nova mensagem atualizada"
}
Response 200 OK: Mensagem atualizada parcialmente
Response 404 Not Found: Mensagem não existe
Idempotência: Depende (setar valor fixo = sim, incrementar = não)

POST /api/v1/system-messages/initialize
Descrição: Inicializa as 24 mensagens padrão para um tenant (usado no onboarding).
Headers:
Authorization: Bearer <JWT>
X-Tenant-ID: <uuid>
Response 201 Created:
{
  "message": "24 mensagens do sistema inicializadas com sucesso",
  "created_count": 24
}
Response 409 Conflict: Tenant já possui mensagens inicializadas
Idempotência: Não (cria recursos)

GET /api/v1/system-messages/types

Descrição: Lista todos os tipos de mensagens disponíveis (para popular dropdowns).
Response 200 OK:

{
  "data": [
    { "value": "BOAS_VINDAS", "label": "Boas-vindas", "category": "inicio_fim" },
    { "value": "ENCERRAR", "label": "Encerrar", "category": "inicio_fim" },
    { "value": "OPCAO_INVALIDA", "label": "Opção inválida", "category": "navegacao" },
    ...
  ]
}

POST /api/v1/system-messages/{message_id}/preview

Descrição: Simula a substituição de variáveis para preview da mensagem final.
Path Parameters:
message_id: UUID
Body Parameters:

{
  "variables": {
    "nomeCliente": "João Silva",
    "nomeAtendente": "Maria Santos",
    "nomeDepartamento": "Vendas",
    "protocolo": "20260702143000",
    "posicao": 3
  }
}

Response 200 OK:

{
  "original": "Você foi transferido para o departamento %nomeDepartamento%.",
  "preview": "Você foi transferido para o departamento Vendas.",
  "variables_used": ["nomeDepartamento"],
  "variables_missing": []
}

5.2. Códigos de Status HTTP Utilizados
Código
Quando Usar
200 OK
GET, PUT, PATCH bem-sucedidos
201 Created
POST de inicialização bem-sucedido
204 No Content
(Não aplicável - não há DELETE)
400 Bad Request
Validação falhou (content > 1024, type inválido)
401 Unauthorized
Token JWT ausente ou inválido
403 Forbidden
Usuário sem permissão para editar mensagens do sistema
404 Not Found
Mensagem não existe ou não pertence ao tenant
409 Conflict
Tenant já inicializado
422 Unprocessable Entity
Variáveis inválidas no preview
500 Internal Server Error
Erro inesperado no servidor
6. ARQUITETURA BACKEND PYTHON (FASTAPI)
6.1. Estrutura de Arquivos
chatbotmarcx-backend/
── app/
    ├── modules/
    │   └── system_messages/
    │       ├── __init__.py
    │       ├── models.py          # SQLAlchemy model
    │       ├── schemas.py         # Pydantic schemas
    │       ├── repository.py      # Acesso a dados
    │       ├── service.py         # Regras de negócio
    │       ├── controller.py      # Endpoints (router)
    │       ├── constants.py       # 24 tipos fixos
    │       ── seed.py            # Dados iniciais
    └── main.py                    # Registro do router
    6.2. Model SQLAlchemy

    import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Boolean, DateTime, Enum, ForeignKey, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base

class SystemMessageType(str, Enum):
    BOAS_VINDAS = "BOAS_VINDAS"
    ENCERRAR = "ENCERRAR"
    SAUDACAO_INICIAL = "SAUDACAO_INICIAL"
    ENCERRAMENTO_INATIVIDADE = "ENCERRAMENTO_INATIVIDADE"
    OPCAO_INVALIDA = "OPCAO_INVALIDA"
    CONFIRMACAO_OPCAO = "CONFIRMACAO_OPCAO"
    AGUARDANDO_RESPOSTA = "AGUARDANDO_RESPOSTA"
    ERRO_GERAL = "ERRO_GERAL"
    TRANSFERENCIA_DEPARTAMENTO = "TRANSFERENCIA_DEPARTAMENTO"
    TRANSFERENCIA_ATENDENTE = "TRANSFERENCIA_ATENDENTE"
    SOLICITAR_ATENDIMENTO = "SOLICITAR_ATENDIMENTO"
    RETORNO_ATENDIMENTO = "RETORNO_ATENDIMENTO"
    PROTOCOLO_ATENDIMENTO = "PROTOCOLO_ATENDIMENTO"
    NOTIFICACAO_CONTATO = "NOTIFICACAO_CONTATO"
    CONFIRMACAO_AGENDAMENTO = "CONFIRMACAO_AGENDAMENTO"
    CANCELAMENTO_AGENDAMENTO = "CANCELAMENTO_AGENDAMENTO"
    FILA_ATENDIMENTO = "FILA_ATENDIMENTO"
    TEMPO_ESPERA_EXCEDIDO = "TEMPO_ESPERA_EXCEDIDO"
    FORA_HORARIO_ATENDIMENTO = "FORA_HORARIO_ATENDIMENTO"
    FORA_TURNO_DEPARTAMENTO = "FORA_TURNO_DEPARTAMENTO"
    FORA_TURNO_ATENDENTE = "FORA_TURNO_ATENDENTE"
    USUARIO_INDISPONIVEL = "USUARIO_INDISPONIVEL"
    PESQUISA = "PESQUISA"
    AGRADECIMENTO_FINAL = "AGRADECIMENTO_FINAL"

class SystemMessage(Base):
    __tablename__ = "system_messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    type = Column(Enum(SystemMessageType), nullable=False, index=True)
    content = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), server_default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    __table_args__ = (
        UniqueConstraint('tenant_id', 'type', name='uq_tenant_system_message_type'),
        Index('ix_system_messages_tenant_active', 'tenant_id', 'is_active'),
    )

    6.3. Constants (24 Tipos com Labels e Categorias)
   6.3. Constants (24 Tipos com Labels e Categorias)

   SYSTEM_MESSAGE_TYPES = {
    "BOAS_VINDAS": {
        "label": "Boas-vindas",
        "category": "inicio_fim",
        "default_content": "👻 Seja bem-vindo!",
        "variables": ["nomeCliente", "nomeEmpresa"]
    },
    "ENCERRAR": {
        "label": "Encerrar",
        "category": "inicio_fim",
        "default_content": "Atendimento encerrado.",
        "variables": []
    },
    "TRANSFERENCIA_DEPARTAMENTO": {
        "label": "Transferência para departamento",
        "category": "transferencia",
        "default_content": "Você foi transferido para o departamento %nomeDepartamento%. Caso deseje finalizar o atendimento digite: *encerrar atendimento* e confirme",
        "variables": ["nomeDepartamento"]
    },
    # ... (demais 21 tipos)
}
 6.4. Schema Pydantic

 from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from app.modules.system_messages.models import SystemMessageType

class SystemMessageCreate(BaseModel):
    type: SystemMessageType
    content: str = Field(..., max_length=1024, min_length=1)
    is_active: bool = True
    
    @field_validator('content')
    @classmethod
    def validate_content(cls, v):
        if not v.strip():
            raise ValueError('Conteúdo não pode ser vazio')
        return v.strip()

class SystemMessageUpdate(BaseModel):
    content: Optional[str] = Field(None, max_length=1024)
    is_active: Optional[bool] = None

class SystemMessageResponse(BaseModel):
    id: UUID
    type: SystemMessageType
    type_label: str
    content: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class SystemMessageTypeOption(BaseModel):
    value: str
    label: str
    category: str
    default_content: str
    variables: List[str]

class PreviewRequest(BaseModel):
    variables: dict = Field(..., description="Variáveis para substituição")

class PreviewResponse(BaseModel):
    original: str
    preview: str
    variables_used: List[str]
    variables_missing: List[str]

    6.6. Controller (Router FastAPI)

    from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Optional
from uuid import UUID
from app.modules.system_messages.schemas import (
    SystemMessageCreate, SystemMessageUpdate, SystemMessageResponse,
    SystemMessageTypeOption, PreviewRequest, PreviewResponse
)
from app.modules.system_messages.service import SystemMessageService
from app.modules.system_messages.constants import SYSTEM_MESSAGE_TYPES
from app.middleware.authentication import get_current_user
from app.middleware.tenant_isolation import get_tenant_id

router = APIRouter(prefix="/api/v1/system-messages", tags=["System Messages"])

@router.get("", response_model=dict)
async def list_system_messages(
    page: int = Query(1, ge=1),
    limit: int = Query(24, ge=1, le=50),
    type: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    tenant_id: UUID = Depends(get_tenant_id),
    current_user: dict = Depends(get_current_user),
    service: SystemMessageService = Depends()
):
    return await service.list_with_pagination(
        tenant_id=tenant_id, page=page, limit=limit,
        type=type, is_active=is_active, search=search
    )

@router.get("/types", response_model=List[SystemMessageTypeOption])
async def list_message_types():
    return [
        SystemMessageTypeOption(
            value=k,
            label=v["label"],
            category=v["category"],
            default_content=v["default_content"],
            variables=v["variables"]
        )
        for k, v in SYSTEM_MESSAGE_TYPES.items()
    ]

@router.get("/{message_id}", response_model=SystemMessageResponse)
async def get_system_message(
    message_id: UUID,
    tenant_id: UUID = Depends(get_tenant_id),
    current_user: dict = Depends(get_current_user),
    service: SystemMessageService = Depends()
):
    result = await service.db.execute(
        select(SystemMessage).where(
            SystemMessage.id == message_id,
            SystemMessage.tenant_id == tenant_id
        )
    )
    message = result.scalar_one_or_none()
    if not message:
        raise HTTPException(status_code=404, detail="Mensagem não encontrada")
    return message

@router.put("/{message_id}", response_model=SystemMessageResponse)
async def update_system_message(
    message_id: UUID,
    data: SystemMessageCreate,
    tenant_id: UUID = Depends(get_tenant_id),
    current_user: dict = Depends(get_current_user),
    service: SystemMessageService = Depends()
):
    return await service.update(message_id, tenant_id, SystemMessageUpdate(
        content=data.content, is_active=data.is_active
    ))

@router.patch("/{message_id}", response_model=SystemMessageResponse)
async def partial_update_system_message(
    message_id: UUID,
    data: SystemMessageUpdate,
    tenant_id: UUID = Depends(get_tenant_id),
    current_user: dict = Depends(get_current_user),
    service: SystemMessageService = Depends()
):
    return await service.update(message_id, tenant_id, data)

@router.post("/initialize", status_code=status.HTTP_201_CREATED)
async def initialize_tenant_messages(
    tenant_id: UUID = Depends(get_tenant_id),
    current_user: dict = Depends(get_current_user),
    service: SystemMessageService = Depends()
):
    return await service.initialize_tenant_messages(tenant_id, current_user["user_id"])

@router.post("/{message_id}/preview", response_model=PreviewResponse)
async def preview_system_message(
    message_id: UUID,
    data: PreviewRequest,
    tenant_id: UUID = Depends(get_tenant_id),
    current_user: dict = Depends(get_current_user),
    service: SystemMessageService = Depends()
):
    return await service.preview(message_id, tenant_id, data.variables)
    7. ARQUITETURA FRONTEND ANGULAR
7.1. Estrutura de Componentes

src/app/features/messages/
└── system-messages/
    ├── system-message-list/
    │   ├── system-message-list.component.ts
    │   ├── system-message-list.component.html
    │   └── system-message-list.component.scss
    ├── system-message-form/
    │   ├── system-message-form.component.ts
    │   ├── system-message-form.component.html
    │   └── system-message-form.component.scss
    ├── services/
    │   └── system-message.service.ts
    └── models/
        └── system-message.model.ts
        7.2. Model TypeScript

        export interface SystemMessage {
  id: string;
  type: SystemMessageType;
  type_label: string;
  content: string;
  is_active: boolean;
  created_at: Date;
  updated_at: Date;
}

export type SystemMessageType = 
  | 'BOAS_VINDAS' | 'ENCERRAR' | 'SAUDACAO_INICIAL'
  | 'ENCERRAMENTO_INATIVIDADE' | 'OPCAO_INVALIDA' | 'CONFIRMACAO_OPCAO'
  | 'AGUARDANDO_RESPOSTA' | 'ERRO_GERAL' | 'TRANSFERENCIA_DEPARTAMENTO'
  | 'TRANSFERENCIA_ATENDENTE' | 'SOLICITAR_ATENDIMENTO' | 'RETORNO_ATENDIMENTO'
  | 'PROTOCOLO_ATENDIMENTO' | 'NOTIFICACAO_CONTATO' | 'CONFIRMACAO_AGENDAMENTO'
  | 'CANCELAMENTO_AGENDAMENTO' | 'FILA_ATENDIMENTO' | 'TEMPO_ESPERA_EXCEDIDO'
  | 'FORA_HORARIO_ATENDIMENTO' | 'FORA_TURNO_DEPARTAMENTO' | 'FORA_TURNO_ATENDENTE'
  | 'USUARIO_INDISPONIVEL' | 'PESQUISA' | 'AGRADECIMENTO_FINAL';

export interface SystemMessageTypeOption {
  value: SystemMessageType;
  label: string;
  category: string;
  default_content: string;
  variables: string[];
}

export interface SystemMessageFilters {
  type?: SystemMessageType;
  is_active?: boolean;
  search?: string;
}

export interface PaginationResponse<T> {
  data: T[];
  pagination: { page: number; limit: number; total: number; total_pages: number; };
  display_info: string;
}
export interface SystemMessage {
  id: string;
  type: SystemMessageType;
  type_label: string;
  content: string;
  is_active: boolean;
  created_at: Date;
  updated_at: Date;
}

export type SystemMessageType = 
  | 'BOAS_VINDAS' | 'ENCERRAR' | 'SAUDACAO_INICIAL'
  | 'ENCERRAMENTO_INATIVIDADE' | 'OPCAO_INVALIDA' | 'CONFIRMACAO_OPCAO'
  | 'AGUARDANDO_RESPOSTA' | 'ERRO_GERAL' | 'TRANSFERENCIA_DEPARTAMENTO'
  | 'TRANSFERENCIA_ATENDENTE' | 'SOLICITAR_ATENDIMENTO' | 'RETORNO_ATENDIMENTO'
  | 'PROTOCOLO_ATENDIMENTO' | 'NOTIFICACAO_CONTATO' | 'CONFIRMACAO_AGENDAMENTO'
  | 'CANCELAMENTO_AGENDAMENTO' | 'FILA_ATENDIMENTO' | 'TEMPO_ESPERA_EXCEDIDO'
  | 'FORA_HORARIO_ATENDIMENTO' | 'FORA_TURNO_DEPARTAMENTO' | 'FORA_TURNO_ATENDENTE'
  | 'USUARIO_INDISPONIVEL' | 'PESQUISA' | 'AGRADECIMENTO_FINAL';

export interface SystemMessageTypeOption {
  value: SystemMessageType;
  label: string;
  category: string;
  default_content: string;
  variables: string[];
}

export interface SystemMessageFilters {
  type?: SystemMessageType;
  is_active?: boolean;
  search?: string;
}

export interface PaginationResponse<T> {
  data: T[];
  pagination: { page: number; limit: number; total: number; total_pages: number; };
  display_info: string;
}

7.3. Service Angular

import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { SystemMessage, SystemMessageFilters, SystemMessageTypeOption, PaginationResponse } from '../models/system-message.model';
import { environment } from '../../../environments/environment';

@Injectable({ providedIn: 'root' })
export class SystemMessageService {
  private http = inject(HttpClient);
  private apiUrl = `${environment.apiUrl}/api/v1/system-messages`;

  list(page: number = 1, limit: number = 24, filters?: SystemMessageFilters): Observable<PaginationResponse<SystemMessage>> {
    let params = new HttpParams().set('page', page.toString()).set('limit', limit.toString());
    if (filters) {
      if (filters.type) params = params.set('type', filters.type);
      if (filters.is_active !== undefined) params = params.set('is_active', filters.is_active.toString());
      if (filters.search) params = params.set('search', filters.search);
    }
    return this.http.get<PaginationResponse<SystemMessage>>(this.apiUrl, { params });
  }

  getById(id: string): Observable<SystemMessage> {
    return this.http.get<SystemMessage>(`${this.apiUrl}/${id}`);
  }

  update(id: string, data: Partial<SystemMessage>): Observable<SystemMessage> {
    return this.http.put<SystemMessage>(`${this.apiUrl}/${id}`, data);
  }

  patch(id: string, data: Partial<SystemMessage>): Observable<SystemMessage> {
    return this.http.patch<SystemMessage>(`${this.apiUrl}/${id}`, data);
  }

  getTypes(): Observable<SystemMessageTypeOption[]> {
    return this.http.get<SystemMessageTypeOption[]>(`${this.apiUrl}/types`);
  }

  initialize(): Observable<any> {
    return this.http.post(`${this.apiUrl}/initialize`, {});
  }

  preview(id: string, variables: Record<string, any>): Observable<any> {
    return this.http.post(`${this.apiUrl}/${id}/preview`, { variables });
  }
}

7.4. Componente de Listagem

import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { SystemMessageService } from '../services/system-message.service';
import { SystemMessage, SystemMessageFilters } from '../models/system-message.model';
import { Router } from '@angular/router';
import { debounceTime, distinctUntilChanged, Subject } from 'rxjs';

@Component({
  selector: 'app-system-message-list',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './system-message-list.component.html'
})
export class SystemMessageListComponent implements OnInit {
  private service = inject(SystemMessageService);
  private router = inject(Router);

  messages: SystemMessage[] = [];
  loading = false;
  pagination = { page: 1, limit: 24, total: 0, total_pages: 0 };
  displayInfo = '';
  filters: SystemMessageFilters = {};
  search = '';
  typeFilter = '';
  statusFilter = '';
  private searchSubject = new Subject<string>();

  ngOnInit() {
    this.loadMessages();
    this.searchSubject.pipe(debounceTime(300), distinctUntilChanged()).subscribe(value => {
      this.filters.search = value;
      this.pagination.page = 1;
      this.loadMessages();
    });
  }

  onSearchChange(value: string) { this.search = value; this.searchSubject.next(value); }
  
  onTypeFilterChange(value: string) {
    this.typeFilter = value;
    this.filters.type = value || undefined;
    this.pagination.page = 1;
    this.loadMessages();
  }

  onStatusFilterChange(value: string) {
    this.statusFilter = value;
    this.filters.is_active = value === '' ? undefined : value === 'true';
    this.pagination.page = 1;
    this.loadMessages();
  }

  loadMessages() {
    this.loading = true;
    this.service.list(this.pagination.page, this.pagination.limit, this.filters).subscribe({
      next: (response) => {
        this.messages = response.data;
        this.pagination = response.pagination;
        this.displayInfo = response.display_info;
        this.loading = false;
      },
      error: (err) => { console.error(err); this.loading = false; }
    });
  }

  onNew() { this.router.navigate(['/messages/system/new']); }
  onEdit(message: SystemMessage) { this.router.navigate(['/messages/system/edit', message.id]); }
  
  onPageChange(page: number) { this.pagination.page = page; this.loadMessages(); }
}

7.5. Template HTML da Listagem
<div class="system-message-list-container">
  <div class="filters-bar">
    <div class="filter-group">
      <label>Tipo:</label>
      <select [(ngModel)]="typeFilter" (ngModelChange)="onTypeFilterChange($event)">
        <option value="">Selecione</option>
        <option value="BOAS_VINDAS">Boas-vindas</option>
        <option value="ENCERRAR">Encerrar</option>
        <option value="OPCAO_INVALIDA">Opção inválida</option>
        <!-- ... demais tipos ... -->
      </select>
    </div>
    <div class="filter-group">
      <label>Status:</label>
      <select [(ngModel)]="statusFilter" (ngModelChange)="onStatusFilterChange($event)">
        <option value="true">Ativo</option>
        <option value="false">Inativo</option>
      </select>
    </div>
    <button class="btn btn-primary" (click)="onNew()">
      <span>+</span> Novo
    </button>
  </div>

  <h3>Mensagens automáticas do sistema</h3>

  <div class="table-container" *ngIf="!loading">
    <table class="table">
      <thead>
        <tr>
          <th>Tipo</th>
          <th>Mensagem</th>
          <th>Status</th>
          <th>Ações</th>
        </tr>
      </thead>
      <tbody>
        <tr *ngFor="let msg of messages">
          <td><strong>{{ msg.type_label }}</strong></td>
          <td class="message-content">{{ msg.content }}</td>
          <td>
            <span class="badge" [class.active]="msg.is_active" [class.inactive]="!msg.is_active">
              {{ msg.is_active ? '✓ ATIVO' : ' INATIVO' }}
            </span>
          </td>
          <td>
            <button class="btn-icon btn-edit" (click)="onEdit(msg)" title="Editar">✏️</button>
          </td>
        </tr>
        <tr *ngIf="messages.length === 0">
          <td colspan="4" class="no-data">Nenhuma mensagem encontrada</td>
        </tr>
      </tbody>
    </table>
  </div>

  <div class="pagination-footer">
    <span class="display-info">{{ displayInfo }}</span>
    <div class="pagination" *ngIf="pagination.total_pages > 1">
      <button [disabled]="pagination.page === 1" (click)="onPageChange(1)">«</button>
      <button [disabled]="pagination.page === 1" (click)="onPageChange(pagination.page - 1)">‹</button>
      <button *ngFor="let p of [].constructor(pagination.total_pages); let i = index" 
              [class.active]="i + 1 === pagination.page" 
              (click)="onPageChange(i + 1)">{{ i + 1 }}</button>
      <button [disabled]="pagination.page === pagination.total_pages" (click)="onPageChange(pagination.page + 1)">›</button>
      <button [disabled]="pagination.page === pagination.total_pages" (click)="onPageChange(pagination.total_pages)">»</button>
    </div>
  </div>
</div>

7.6. Componente de Formulário
import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { SystemMessageService } from '../services/system-message.service';
import { ActivatedRoute, Router } from '@angular/router';

@Component({
  selector: 'app-system-message-form',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './system-message-form.component.html'
})
export class SystemMessageFormComponent implements OnInit {
  private fb = inject(FormBuilder);
  private service = inject(SystemMessageService);
  private route = inject(ActivatedRoute);
  private router = inject(Router);

  form!: FormGroup;
  messageId: string | null = null;
  charCount = 0;
  maxChars = 1024;

  ngOnInit() {
    this.initForm();
    const id = this.route.snapshot.paramMap.get('id');
    if (id) {
      this.messageId = id;
      this.loadMessage(id);
    }
  }

  initForm() {
    this.form = this.fb.group({
      type: ['', [Validators.required]],
      content: ['', [Validators.required, Validators.maxLength(1024)]],
      is_active: [true]
    });
    this.form.get('content')?.valueChanges.subscribe(value => {
      this.charCount = value?.length || 0;
    });
  }

  loadMessage(id: string) {
    this.service.getById(id).subscribe({
      next: (msg) => {
        this.form.patchValue({
          type: msg.type,
          content: msg.content,
          is_active: msg.is_active
        });
        this.charCount = msg.content.length;
      },
      error: (err) => console.error(err)
    });
  }

  addEmoji(emoji: string) {
    const contentControl = this.form.get('content');
    if (contentControl) {
      const current = contentControl.value || '';
      contentControl.setValue(current + emoji);
    }
  }

  onSave() {
    if (this.form.invalid) { this.form.markAllAsTouched(); return; }
    const data = this.form.value;
    const request = this.messageId 
      ? this.service.update(this.messageId, data)
      : this.service.initialize(); // Para "Novo" - na verdade não se cria, apenas inicializa
    
    request.subscribe({
      next: () => this.router.navigate(['/messages/system']),
      error: (err) => console.error(err)
    });
  }

  onBack() { this.router.navigate(['/messages/system']); }
}

7.7. Template HTML do Formulário
<div class="system-message-form-container">
  <h2>Mensagem do sistema</h2>
  
  <form [formGroup]="form" (ngSubmit)="onSave()">
    <div class="form-group">
      <label>Tipo*:</label>
      <select formControlName="type">
        <option value="BOAS_VINDAS">Boas-vindas</option>
        <option value="ENCERRAR">Encerrar</option>
        <option value="OPCAO_INVALIDA">Opção inválida</option>
        <!-- ... demais tipos ... -->
      </select>
    </div>

    <div class="form-group">
      <label>Mensagem:</label>
      <div class="textarea-wrapper">
        <textarea formControlName="content" maxlength="1024" rows="6"></textarea>
        <button type="button" class="emoji-btn" (click)="addEmoji('😊')">😊</button>
      </div>
      <span class="char-counter" [class.danger]="charCount > 900">{{ charCount }}/{{ maxChars }}</span>
    </div>

    <div class="form-group checkbox-group">
      <label>
        <input type="checkbox" formControlName="is_active" />
        Ativo
      </label>
    </div>

    <div class="form-actions">
      <button type="button" class="btn btn-secondary" (click)="onBack()">Voltar</button>
      <button type="submit" class="btn btn-primary" [disabled]="form.invalid">
        <span>💾</span> Salvar
      </button>
    </div>
  </form>
</div>

8. CHECKLIST DE IMPLEMENTAÇÃO
Fase 1: Backend Python (Semanas 1-2)
Criar estrutura de pastas app/modules/system_messages/
Definir constants.py com os 24 tipos de mensagens (labels, categorias, conteúdos padrão, variáveis)
Criar Model SQLAlchemy SystemMessage com constraints
Criar Schemas Pydantic (Create, Update, Response, TypeOption, Preview)
Implementar repository.py com queries filtradas por tenant_id
Implementar service.py com lógica de negócio (list, update, initialize, preview)
Implementar controller.py com todos os endpoints RESTful
Criar migration Alembic para tabela system_messages
Criar endpoint de inicialização automática no onboarding de tenant
Implementar endpoint de preview com substituição de variáveis
Criar testes unitários com pytest (cobertura > 80%)
Documentar endpoints no Swagger/OpenAPI
Fase 2: Frontend Angular (Semanas 3-4)
Criar models TypeScript (system-message.model.ts)
Criar SystemMessageService com todos os métodos HTTP
Criar SystemMessageListComponent (listagem com filtros e paginação)
Criar SystemMessageFormComponent (formulário de edição)
Implementar contadores de caracteres dinâmicos
Implementar botão de emoji picker
Implementar filtros (Tipo, Status, Busca textual)
Implementar paginação completa com "Listado X de Y registro(s)"
Adicionar badges de status (ATIVO/INATIVO)
Integrar com menu lateral (ícone "Sistema" com envelope)
Adicionar validações de formulário (required, maxLength)
Implementar tratamento de erros via interceptor
Fase 3: Integração e Testes (Semana 5)
Testar fluxo completo: listar → editar → salvar → visualizar alterações
Testar filtros combinados (tipo + status + busca)
Testar paginação com grande volume de dados
Testar endpoint de preview com diversas variáveis
Testar isolamento multi-tenant (2 tenants não podem ver mensagens um do outro)
Testar inicialização automática no onboarding de novo tenant
Validar formatação WhatsApp (negrito, itálico, emojis)
Testes E2E com Cypress
Fase 4: Integração com Motor do ChatBot (Semana 6)
Criar serviço de resolução de variáveis no backend
Integrar endpoint de mensagens automáticas com o motor de fluxo do ChatBot
Implementar cache das mensagens em Redis para performance
Criar logs de uso de cada mensagem automática
Implementar webhook de notificação quando mensagem for enviada
9. REGRAS DE NEGÓCIO E VALIDAÇÕES
9.1. Validações de Campos
Tipo: Obrigatório, valor fixo entre os 24 tipos pré-definidos
Conteúdo: Obrigatório, mínimo 1 caractere, máximo 1024 caracteres, não pode ser apenas espaços
Status (is_active): Boolean, default true
Variáveis dinâmicas: Devem estar no formato %nomeVariavel% (entre百分号)
9.2. Regras de Isolamento Multi-Tenant
Todas as queries filtram obrigatoriamente por tenant_id
Cada tenant tem exatamente 24 mensagens (uma de cada tipo)
Mensagens não podem ser deletadas, apenas desativadas
Inicialização ocorre automaticamente no onboarding do tenant
9.3. Regras de Formatação WhatsApp
*texto* → negrito
_texto_ → itálico
~texto~ → tachado
`texto` → monoespaçado
Emojis Unicode são suportados nativamente
Quebras de linha são preservadas
9.4. Regras de UX/UI (Baseado nos Prints)
Listagem: Filtros de Tipo e Status no topo, botão "+ Novo" à direita
Tabela: Colunas Tipo, Mensagem, Status (badge verde/vermelho), Ações (apenas editar)
Paginação: Completa com primeira, anterior, números, próxima, última
Rodapé: "Listado X de Y registro(s)"
Formulário: Tipo obrigatório, textarea grande, botão de emoji, checkbox Ativo
Ações: Botões "Voltar" (esquerda) e "Salvar" (direita) em vermelho
9.5. Regras de Negócio do ChatBot
Mensagens automáticas são disparadas por eventos do sistema, não por escolha do cliente
Variáveis são substituídas em tempo de execução pelo motor do ChatBot
Mensagens inativas não são enviadas (sistema usa fallback ou ignora)
Prioridade: mensagens específicas (ex: "Fora do turno do departamento") têm prioridade sobre genéricas
10. INTEGRAÇÃO COM MÓDULO EXISTENTE
10.1. Navegação
O módulo de Mensagens Automáticas do Sistema deve ser acessado via menu lateral:

Mensagens
├── 💬 Mensagens Interativas (existente)
── ✉️ Sistema (NOVO - este módulo)
├── 📝 Memorandos
└── 📌 Post-its
const routes: Routes = [
  { path: 'messages', children: [
    { path: 'interactive', component: MessageListComponent },
    { path: 'interactive/new', component: MessageFormComponent },
    { path: 'interactive/edit/:id', component: MessageFormComponent },
    { path: 'system', component: SystemMessageListComponent },      // NOVO
    { path: 'system/new', component: SystemMessageFormComponent },  // NOVO
    { path: 'system/edit/:id', component: SystemMessageFormComponent } // NOVO
  ]}
];
10.3. Compartilhamento de Serviços
TenantService e AuthService são compartilhados entre os módulos
Interceptors HTTP (auth, tenant, error) são globais
ToastService para notificações é compartilhado
11. FORMATO DE SAÍDA ESPERADO
Ao executar esta skill, o desenvolvedor ou IA deve gerar:
Código completo do backend Python (models, schemas, repository, service, controller, constants, seed)
Código completo do frontend Angular (models, service, components, templates, styles)
Migration Alembic para criação da tabela system_messages
Script de seed com as 24 mensagens padrão em português
Testes unitários para service e controller (pytest + httpx)
Testes E2E para fluxos críticos (Cypress)
Documentação Swagger/OpenAPI atualizada com novos endpoints
Guia de integração com o motor do ChatBot para disparo automático das mensagens
Manual de variáveis dinâmicas para administradores do sistema
Plano de migração para tenants existentes (script de inicialização em massa)
12. CONSIDERAÇÕES FINAIS
Este módulo é crítico para a operação do ChatBot, pois define a experiência do cliente em momentos-chave do atendimento (boas-vindas, transferências, fila, encerramento). A implementação deve priorizar:
Confiabilidade: Mensagens devem sempre estar disponíveis (cache em Redis)
Flexibilidade: Administradores devem poder personalizar todas as mensagens
Performance: Substituição de variáveis deve ser rápida (< 50ms)
Observabilidade: Logs de qual mensagem foi enviada, para quem e quando
Multi-tenancy: Isolamento total de dados entre tenants
A stack Angular + Python (FastAPI) oferece a combinação ideal de produtividade no frontend e performance no backend para atender a estes requisitos.
