SKILL: ANALISE ESTRUTURAL E PLANEJAMENTO DE ARQUITETURA ANGULAR E PYTHON PARA O MODULO DE MENSAGENS INTERATIVAS DO CHATBOTMARCX
CONTEXTO E OBJETIVO
Voce atuara como um Arquiteto de Software Senior especialista em Angular, Python, APIs RESTful e arquitetura multi-tenant. O EcoChatBotMarcx e uma plataforma SaaS generica, adaptavel a qualquer modelo de negocio. A stack tecnologica e Angular no frontend e Python (FastAPI) no backend. O foco desta skill e exclusivamente o modulo de Mensagens Interativas, baseado no template visual e funcional do ZigChat.
REFERENCIA VISUAL - TEMPLATE ZIGCHAT E HTML ATUAL
Analise o arquivo HTML fornecido (EcoChat v2.0) e os prints do ZigChat como referencia de interface. O sistema atual (EcoChat) possui os seguintes modulos:
MODULO DE TURNOS (Nao sera abordado nesta skill):
Turnos e equipes configuraveis pelo tenant
Funcoes operacionais configuraveis pelo tenant
Importacao de escalas ou agendas conforme o negocio
Importacao de Escalas (Excel e OCR)
MODULO DE MENSAGENS INTERATIVAS (Foco desta skill):
Baseado no HTML atual e no template ZigChat, o modulo deve ter:
Titulo: Mensagens Interativas
Descricao: Cadastre mensagens com botoes (ate 3 opcoes) vinculadas a um Departamento e Canal de Atendimento - o sistema usa esse vinculo para saber qual mensagem apresentar quando o cliente escolher aquele menu.
Formulario Nova mensagem interativa com:
Campos com * sao obrigatorios
Descricao* com contador 0/100
Cabecalho com contador 0/60
Corpo* com contador 0/1024
Rodape com contador 0/60
Departamento* (dropdown: Selecione um departamento...)
Canal de Atendimento* (dropdown: Selecione o departamento primeiro...)
Texto helper: Define em qual fluxo (prototipo) esta mensagem sera usada.
Secao Vincular a um usuario
Secao Opcoes (0/3) - Botoes com botao + Adicionar
Mensagem de estado vazio: Nenhuma opcao adicionada.
Botoes: Cancelar e Salvar (com icone de disquete)
Secao Mensagens cadastradas com contador (0 mensagens)
Baseado no ZigChat (referencia adicional):
Tela de listagem com filtros (Descricao e Tipo)
Botao + Novo em vermelho
Tabela com colunas: Descricao, Tipo, Dono da mensagem, Acoes (editar/excluir)
Exemplos: SAUDACOES, Orcamentos/Tesouraria, ANTES DE ENCERRAR ATENDIMENTO, ENCERRAR ATENDIMENTO, GUIA MATERNIDADE, AGENDAMENTO CIRURGICO GERAL
Paginacao: Exibindo 10 de 84 modelo(s)
Tela de edicao com secao Arquivo (Selecionar arquivo e Gravar audio)
Preview de imagem PNG anexada
Aviso: arquivos de audio nao acompanham mensagens de texto (a mensagem sera ignorada)
CORRECAO CRITICA DE ESCOPO - SEPARACAO TOTAL DE MODULOS
E fundamental compreender que o modulo de Mensagens Interativas e um sistema completamente isolado e independente. Ele NAO trata de escalas, NAO trata de gestao de turnos, NAO tem relacao com profissionais de saude ou hospitais especificos. O unico proposito deste modulo e permitir que administradores de qualquer tipo de negocio (clinicas, lojas, escolas, restaurantes, escritorios de contabilidade, etc.) possam criar templates de mensagens padronizadas do WhatsApp com texto, midia e botoes interativos. O vinculo com Departamentos e Canais de Atendimento define qual mensagem o ChatBot enviara quando o cliente interagir com um determinado menu no fluxo de atendimento. As escalas permanecem como um modulo interno completamente separado, sem nenhuma relacao com este modulo de mensagens.
FUNDAMENTACAO TEORICA APLICADA - GRAMATICA DE APIS
Toda a analise e planejamento devem seguir rigorosamente os principios da Gramatica de APIs:
Verbos HTTP e Idempotencia:
GET: Recuperar listas ou detalhes de recursos (idempotente - mesma requisicao produz mesmo resultado)
POST: Criar novos recursos (nao idempotente - cada chamada cria um novo recurso)
PUT: Substituir recurso completo (idempotente - mesma requisicao repetida produz mesmo estado final)
PATCH: Atualizar parcialmente (idempotencia depende do contexto - setar valor fixo e idempotente, incrementar nao e)
DELETE: Remover recursos (idempotente - deletar recurso inexistente continua sendo sucesso)
Tipos de Parametros:
Path Parameters: Identificadores fixos na URL para apontar recurso unico (ex: /message-templates/{id}) - usar para IDs obrigatorios
Query Parameters: Filtros opcionais apos o ? na URL (ex: ?page=1&limit=10&type=standard) - ideal para paginacao e ordenacao, nunca para dados sensiveis
Body Parameters: Dados estruturados no corpo da requisicao (JSON ou multipart/form-data) - para objetos complexos em POST/PUT/PATCH
Header Parameters: Metadados da requisicao (Authorization Bearer token, X-Tenant-ID, Content-Type, Accept) - para autenticacao e contexto tecnico
Codigos de Status HTTP:
200 OK: Sucesso em GET, PUT, PATCH
201 Created: Sucesso ao criar recurso via POST
204 No Content: Sucesso sem dados para retornar (DELETE)
400 Bad Request: Dados invalidos ou mal formados
401 Unauthorized: Falta de autenticacao (quem e voce?)
403 Forbidden: Autenticado mas sem permissao (sei quem e voce, mas nao pode)
404 Not Found: Recurso nao existe
409 Conflict: Conflito (ex: descricao ja existe)
500 Internal Server Error: Excecao inesperada no servidor
503 Service Unavailable: Servidor sobrecarregado ou em manutencao
Arquitetura em Camadas (MVC + Service Layer):
Controller: Ponto de entrada, valida requisicao e delega trabalho
Service Layer: Coracao do sistema, concentra regras de negocio e validacoes complexas
Repository Layer: Acesso exclusivo aos dados, intermediario com banco de dados
Model: Estrutura das entidades do banco
View: Representacao JSON devolvida ao cliente (no contexto de API)
Padrao BFF (Backend For Frontend):
Camada sob medida para cada interface (web desktop, mobile, integracoes third-party)
Otimiza volume de dados, performance e complexidade
Logica de filtro no BFF mantem frontend limpo
INSTRUCAO 1: AUDITORIA DO FRONTEND ATUAL E MAPEAMENTO DO TEMPLATE ZIGCHAT
Analise o arquivo HTML fornecido (EcoChat v2.0) e os prints do ZigChat. Identifique e documente:
A. Acoplamentos especificos de qualquer negocio que devem ser removidos ou parametrizados:
Referencias a uma empresa, marca ou unidade especifica no texto de exemplo
Nomes de pessoas, equipes, departamentos ou produtos reais na identidade visual
Nomes de fluxos especificos de um segmento ou cliente
Todos esses valores devem ser configuraveis por tenant, com valores padrao editaveis
B. Estrutura do formulario de Mensagem Modelo (baseado no ZigChat e HTML atual):
Descricao: campo obrigatorio, maximo 100 caracteres, contador de caracteres visivel (0/100), deve ser unico por tenant, automaticamente convertido para maiusculas
Cabecalho: campo opcional, maximo 60 caracteres, contador visivel (0/60)
Corpo: textarea grande, maximo 1024 caracteres, contador visivel (0/1024), suporta emojis (botao de emoji ao lado), obrigatorio
Rodape: campo opcional, maximo 60 caracteres, contador visivel (0/60)
Tipo: campo implicito (text, image, document, audio, interactive, standard) - determinado pelo conteudo
Departamento: dropdown obrigatorio, populado via API, com placeholder Selecione um departamento...
Canal de Atendimento: dropdown obrigatorio, populado via API, dependente do departamento selecionado, com placeholder Selecione o departamento primeiro...
Texto helper: Define em qual fluxo (prototipo) esta mensagem sera usada.
Vincular a usuario: campos Codigo e Usuario (opcionais, com busca/autocomplete)
Secao Arquivo (ZigChat):
Botao Selecionar arquivo para upload de imagem/documento
Botao Gravar audio para gravacao direta de audio
Preview do arquivo anexado com tipo (ex: Imagem PNG)
Botao de excluir arquivo (lixeira)
Botao de download arquivo
Aviso sobre audio nao acompanhar texto
Botoes interativos: ate 3 opcoes com label e action (visivel no HTML atual)
Botao Salvar com icone de disquete
Botao Cancelar
C. Estrutura da listagem (baseado no ZigChat):
Filtros: busca por descricao (campo texto), filtro por tipo (dropdown com opcao Todos)
Tabela com colunas: Descricao, Tipo, Dono da mensagem (usuario vinculado), Acoes (editar/excluir)
Paginacao: Exibindo X de Y modelo(s) com navegacao completa (primeira, anterior, numeros, proxima, ultima)
Botao + Novo para criacao
Total de registros visivel (ex: 84 modelos)
D. Dependencias de localStorage a migrar:
Todas as mensagens atualmente em localStorage devem migrar para API Python
Departamentos e canais devem vir de endpoints dedicados
Upload de midia deve ir para servico de armazenamento (S3/MinIO)
Busca de usuarios deve vir de endpoint de usuarios
INSTRUCAO 2: DESIGN DA API RESTFUL EM PYTHON
Projete os endpoints usando FastAPI (recomendado por performance e OpenAPI automatico) ou Django REST Framework.
A. Recursos de MessageTemplate (Modelo de Mensagem):
GET /api/v1/message-templates
Query Parameters:
page: integer (default 1, minimo 1) - numero da pagina
limit: integer (default 10, maximo 100) - itens por pagina
search: string (opcional) - busca textual em descricao e corpo
type: string (opcional) - filtro por tipo (text, image, document, audio, interactive, standard)
departmentId: UUID (opcional) - filtro por departamento
channelId: UUID (opcional) - filtro por canal
isActive: boolean (opcional) - filtro por status ativo
sortBy: string (default createdAt) - campo para ordenacao
sortOrder: enum asc ou desc (default desc) - ordem
Headers:
Authorization: Bearer {JWT}
X-Tenant-ID: {tenant_id}
Response 200 OK:
{
"data": [array de MessageTemplateResponse],
"pagination": {
"page": 1,
"limit": 10,
"total": 84,
"totalPages": 9
},
"displayInfo": "Exibindo 10 de 84 modelo(s)"
}
POST /api/v1/message-templates
Body Parameters (JSON ou multipart/form-data):
{
"descricao": "SAUDACOES",
"header": "Ola, tudo bem?",
"body": "Atendimento [NOME_EMPRESA].\nComo posso ajudar?",
"footer": "Horario: 8h as 18h",
"type": "interactive",
"departmentId": "uuid-department",
"channelId": "uuid-channel",
"linkedUserId": "uuid-user (opcional)",
"linkedUserCode": "codigo-usuario (opcional)",
"buttons": [
{"label": "Agendar Consulta", "action": "AGENDAR"},
{"label": "Falar com Atendente", "action": "ATENDENTE"}
]
}
Files (multipart/form-data, opcional):
media: arquivo (image/png, image/jpeg, application/pdf, audio/ogg, audio/mpeg)
Headers:
Authorization: Bearer {JWT}
X-Tenant-ID: {tenant_id}
Response 201 Created:
{
"id": "uuid-gerado",
"descricao": "SAUDACOES",
"type": "interactive",
"mediaUrl": "https://s3...",
"mediaType": "image/png",
"createdAt": "2026-07-02T14:30:00Z"
}
Validacoes no Service:
descricao obrigatoria, max 100 chars, unica por tenant
body obrigatorio, max 1024 chars
header opcional, max 60 chars
footer opcional, max 60 chars
departmentId e channelId obrigatorios e devem existir no tenant
maximo 3 botoes, cada label max 20 chars
se tiver midia, validar tipo e tamanho (imagem max 5MB, documento max 10MB, audio max 5MB e 1 minuto)
audio nao acompanha texto (se tipo audio, body e ignorado)
PUT /api/v1/message-templates/{id}
Path Parameters: id (UUID do template)
Body Parameters: Mesma estrutura completa do POST (substituicao total)
Headers: Authorization, X-Tenant-ID
Response 200 OK: Template atualizado completo
Response 404 Not Found: Template nao encontrado ou nao pertence ao tenant
Response 409 Conflict: Descricao ja existe
Idempotencia: Sim (mesma requisicao repetida produz mesmo estado final)
PATCH /api/v1/message-templates/{id}
Path Parameters: id (UUID do template)
Body Parameters: Apenas campos a atualizar (JSON parcial)
Exemplo: {"body": "Novo texto atualizado"} ou {"buttons": [...]}
Headers: Authorization, X-Tenant-ID
Response 200 OK: Template atualizado parcialmente
Response 404 Not Found: Template nao encontrado
Idempotencia: Depende (setar valor fixo = sim, incrementar = nao)
DELETE /api/v1/message-templates/{id}
Path Parameters: id (UUID do template)
Headers: Authorization, X-Tenant-ID
Response 204 No Content: Sucesso (sem corpo)
Response 404 Not Found: Template nao encontrado
Idempotencia: Sim (deletar recurso inexistente continua sendo sucesso)
Implementacao: Soft delete (setar isActive = false) para permitir recuperacao
GET /api/v1/message-templates/{id}
Path Parameters: id (UUID do template)
Headers: Authorization, X-Tenant-ID
Response 200 OK:
{
"id": "uuid",
"descricao": "SAUDACOES",
"header": "Ola, tudo bem?",
"body": "Atendimento...",
"footer": "Horario...",
"type": "interactive",
"department": {"id": "uuid", "name": "Atendimento", "code": "ATENDIMENTO"},
"channel": {"id": "uuid", "name": "WhatsApp Principal", "platform": "whatsapp"},
"linkedUser": {"id": "uuid", "code": "001", "name": "Joao Silva"},
"buttons": [{"label": "Agendar", "action": "AGENDAR"}],
"mediaUrl": "https://s3...",
"mediaType": "image/png",
"isActive": true,
"createdAt": "...",
"updatedAt": "..."
}
Response 404 Not Found: Template nao encontrado ou nao pertence ao tenant
B. Recursos de Department (Departamento):
GET /api/v1/departments
Query Parameters: isActive, search
Headers: Authorization, X-Tenant-ID
Response 200 OK: Lista de departamentos do tenant
POST /api/v1/departments
Body: {"name": "Atendimento", "code": "ATENDIMENTO", "description": "Departamento de atendimento ao cliente"}
Response 201 Created
C. Recursos de Channel (Canal de Atendimento):
GET /api/v1/channels
Query Parameters: platform, isActive, departmentId
Headers: Authorization, X-Tenant-ID
Response 200 OK: Lista de canais do tenant
POST /api/v1/channels
Body: {"name": "WhatsApp Principal", "platform": "whatsapp", "phoneNumber": "+5511999999999"}
Response 201 Created
D. Recursos de User (Usuario) - para vinculacao:
GET /api/v1/users
Query Parameters: search, departmentId
Headers: Authorization, X-Tenant-ID
Response 200 OK: Lista de usuarios do tenant
INSTRUCAO 3: ARQUITETURA BACKEND PYTHON
A. Stack Tecnologica Recomendada:
Framework: FastAPI (recomendado) ou Django REST Framework
ORM: SQLAlchemy 2.0 (FastAPI) ou Django ORM
Validacao: Pydantic v2 (FastAPI) ou Django Serializers
Banco de Dados: PostgreSQL 15+
Autenticacao: JWT com python-jose ou PyJWT, senhas com bcrypt
Upload de Arquivos: AWS S3, MinIO ou armazenamento local com estrutura por tenant
Background Tasks: Celery + Redis (para processamento assincrono de midia e integracao WhatsApp)
Migracoes: Alembic (SQLAlchemy) ou Django Migrations
Testes: pytest + httpx (FastAPI) ou pytest-django
Documentacao: OpenAPI/Swagger automatico do FastAPI
B. Estrutura de Pastas Sugerida (FastAPI):
chatbotmarcx-backend/
app/
init.py
main.py (ponto de entrada, configuracao FastAPI, CORS, middlewares)
config.py (variaveis de ambiente via pydantic-settings)
database.py (conexao PostgreSQL, sessao SQLAlchemy async)
models/
init.py
base.py (classe base com id, timestamps)
tenant.py
user.py
department.py
channel.py
message_template.py
schemas/
init.py
message_template.py (Pydantic models para request/response)
department.py
channel.py
user.py
pagination.py (schema generico de paginacao)
repositories/
init.py
base_repository.py (CRUD generico com filtros de tenant)
message_template_repository.py
department_repository.py
channel_repository.py
user_repository.py
services/
init.py
message_template_service.py (regras de negocio)
department_service.py
channel_service.py
user_service.py
media_service.py (upload/download S3, validacao de tipo/tamanho)
controllers/ (ou routers no FastAPI)
init.py
message_template_controller.py
department_controller.py
channel_controller.py
user_controller.py
middleware/
init.py
authentication.py (validacao JWT, extrai usuario)
tenant_isolation.py (extrai e valida X-Tenant-ID)
utils/
init.py
exceptions.py (custom exceptions: NotFoundException, ConflictException)
validators.py (validacoes de negocio: limites de caracteres, botoes)
helpers.py (funcoes auxiliares)
tasks/
init.py
media_processing.py (Celery tasks para processamento assincrono)
alembic/ (migrations)
tests/
requirements.txt
.env.example
docker-compose.yml
C. Model SQLAlchemy - message_template.py:
class MessageTemplate(Base):
tablename = "message_templates"
id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
descricao = Column(String(100), nullable=False)
header = Column(String(60), nullable=True)
body = Column(Text, nullable=False)
footer = Column(String(60), nullable=True)
type = Column(Enum('text', 'image', 'document', 'audio', 'interactive', 'standard', name='message_type'), nullable=False, default='text')
department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id"), nullable=False, index=True)
channel_id = Column(UUID(as_uuid=True), ForeignKey("channels.id"), nullable=False, index=True)
linked_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
linked_user_code = Column(String(20), nullable=True)
media_url = Column(String(500), nullable=True)
media_type = Column(String(50), nullable=True)
media_size = Column(Integer, nullable=True)
buttons = Column(JSON, nullable=True)
is_active = Column(Boolean, default=True, index=True)
created_at = Column(DateTime(timezone=True), server_default=func.now())
updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
tenant = relationship("Tenant", back_populates="message_templates")
department = relationship("Department", back_populates="message_templates")
channel = relationship("Channel", back_populates="message_templates")
linked_user = relationship("User", back_populates="linked_message_templates")

__table_args__ = (
    UniqueConstraint('tenant_id', 'descricao', name='uq_tenant_descricao'),
    Index('ix_message_templates_tenant_active', 'tenant_id', 'is_active'),
    Index('ix_message_templates_department', 'tenant_id', 'department_id'),
)
D. Schema Pydantic - message_template.py:
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from uuid import UUID
from datetime import datetime
class ButtonSchema(BaseModel):
label: str = Field(..., max_length=20, description="Texto do botao (max 20 chars)")
action: str = Field(..., max_length=50, description="Identificador da acao")
class MessageTemplateCreate(BaseModel):
descricao: str = Field(..., max_length=100, description="Descricao obrigatoria (max 100 chars)")
header: Optional[str] = Field(None, max_length=60, description="Cabecalho opcional (max 60 chars)")
body: str = Field(..., max_length=1024, description="Corpo obrigatorio (max 1024 chars)")
footer: Optional[str] = Field(None, max_length=60, description="Rodape opcional (max 60 chars)")
type: str = Field(..., pattern="^(text|image|document|audio|interactive|standard)$")
department_id: UUID
channel_id: UUID
linked_user_id: Optional[UUID] = None
linked_user_code: Optional[str] = Field(None, max_length=20)
buttons: Optional[List[ButtonSchema]] = Field(None, max_length=3)

@field_validator('descricao')
@classmethod
def descricao_uppercase(cls, v):
    return v.upper().strip()

@field_validator('buttons')
@classmethod
def validate_buttons(cls, v):
    if v and len(v) > 3:
        raise ValueError('Maximo 3 botoes permitidos')
    return v
    class MessageTemplateResponse(BaseModel):
id: UUID
descricao: str
header: Optional[str]
body: str
footer: Optional[str]
type: str
department: dict
channel: dict
linked_user: Optional[dict]
linked_user_code: Optional[str]
buttons: Optional[List[ButtonSchema]]
media_url: Optional[str]
media_type: Optional[str]
is_active: bool
created_at: datetime
updated_at: datetime

class Config:
    from_attributes = True

   class MessageTemplateListResponse(BaseModel):
data: List[MessageTemplateResponse]
pagination: dict
display_info: str
E. Controller/Router - message_template_controller.py:
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status, Form
from typing import List, Optional
from uuid import UUID
from app.schemas.message_template import MessageTemplateCreate, MessageTemplateResponse, MessageTemplateListResponse
from app.services.message_template_service import MessageTemplateService
from app.middleware.authentication import get_current_user
from app.middleware.tenant_isolation import get_tenant_id
router = APIRouter(prefix="/api/v1/message-templates", tags=["Message Templates"])
@router.get("", response_model=MessageTemplateListResponse)
async def list_message_templates(
page: int = Query(1, ge=1), limit: int = Query(10, ge=1, le=100),
search: Optional[str] = Query(None), type: Optional[str] = Query(None),
department_id: Optional[UUID] = Query(None), channel_id: Optional[UUID] = Query(None),
is_active: Optional[bool] = Query(None), sort_by: str = Query("created_at"),
sort_order: str = Query("desc", pattern="^(asc|desc)$"),
tenant_id: UUID = Depends(get_tenant_id), current_user: dict = Depends(get_current_user),
service: MessageTemplateService = Depends()
):
result = await service.list_with_pagination(tenant_id=tenant_id, page=page, limit=limit, search=search, type=type, department_id=department_id, channel_id=channel_id, is_active=is_active, sort_by=sort_by, sort_order=sort_order)
return result
@router.post("", response_model=MessageTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_message_template(
descricao: str = Form(..., max_length=100), body: str = Form(..., max_length=1024),
header: Optional[str] = Form(None, max_length=60), footer: Optional[str] = Form(None, max_length=60),
type: str = Form(...), department_id: UUID = Form(...), channel_id: UUID = Form(...),
linked_user_id: Optional[UUID] = Form(None), linked_user_code: Optional[str] = Form(None, max_length=20),
buttons: Optional[str] = Form(None), media: Optional[UploadFile] = File(None),
tenant_id: UUID = Depends(get_tenant_id), current_user: dict = Depends(get_current_user),
service: MessageTemplateService = Depends()
):
parsed_buttons = None
if buttons:
import json
parsed_buttons = json.loads(buttons)
return await service.create(tenant_id=tenant_id, data={"descricao": descricao, "body": body, "header": header, "footer": footer, "type": type, "department_id": department_id, "channel_id": channel_id, "linked_user_id": linked_user_id, "linked_user_code": linked_user_code, "buttons": parsed_buttons}, media=media)
@router.put("/{template_id}", response_model=MessageTemplateResponse)
async def update_message_template(template_id: UUID, template: MessageTemplateCreate, tenant_id: UUID = Depends(get_tenant_id), current_user: dict = Depends(get_current_user), service: MessageTemplateService = Depends()):
return await service.update(template_id, tenant_id, template)
@router.patch("/{template_id}", response_model=MessageTemplateResponse)
async def partial_update_message_template(template_id: UUID, updates: dict, tenant_id: UUID = Depends(get_tenant_id), current_user: dict = Depends(get_current_user), service: MessageTemplateService = Depends()):
return await service.partial_update(template_id, tenant_id, updates)
@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_message_template(template_id: UUID, tenant_id: UUID = Depends(get_tenant_id), current_user: dict = Depends(get_current_user), service: MessageTemplateService = Depends()):
await service.delete(template_id, tenant_id)
@router.get("/{template_id}", response_model=MessageTemplateResponse)
async def get_message_template(template_id: UUID, tenant_id: UUID = Depends(get_tenant_id), current_user: dict = Depends(get_current_user), service: MessageTemplateService = Depends()):
return await service.get_by_id(template_id, tenant_id)
F. Service - message_template_service.py:
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, UploadFile, status
from uuid import UUID
from app.repositories.message_template_repository import MessageTemplateRepository
from app.services.media_service import MediaService
from app.utils.validators import validate_message_template_limits, validate_media_file
class MessageTemplateService:
def init(self, db: AsyncSession, media_service: MediaService):
self.db = db
self.repo = MessageTemplateRepository(db)
self.media_service = media_service
 async def list_with_pagination(self, tenant_id: UUID, page: int, limit: int, **filters):
    templates, total = await self.repo.find_with_filters(tenant_id=tenant_id, page=page, limit=limit, **filters)
    total_pages = (total + limit - 1) // limit
    display_start = (page - 1) * limit + 1
    display_end = min(page * limit, total)
    display_info = f"Exibindo {display_start} de {total} modelo(s)" if total > 0 else "Nenhum modelo encontrado"
    return {"data": templates, "pagination": {"page": page, "limit": limit, "total": total, "total_pages": total_pages}, "display_info": display_info}

async def create(self, tenant_id: UUID, data: dict, media: UploadFile = None):
    existing = await self.repo.find_by_descricao(tenant_id, data["descricao"])
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Descricao '{data['descricao']}' ja existe para este tenant")
    validate_message_template_limits(data)
    if data.get("buttons") and len(data["buttons"]) > 3:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Maximo 3 botoes permitidos")
    media_url = None
    media_type = None
    media_size = None
    if media:
        validate_media_file(media)
        media_url, media_type, media_size = await self.media_service.upload(media, tenant_id)
    if media and not data.get("type"):
        if media_type.startswith("image/"): data["type"] = "image"
        elif media_type.startswith("audio/"): data["type"] = "audio"
        elif media_type == "application/pdf": data["type"] = "document"
    template = await self.repo.create({**data, "tenant_id": tenant_id, "media_url": media_url, "media_type": media_type, "media_size": media_size})
    return template

async def update(self, template_id: UUID, tenant_id: UUID, data: dict):
    template = await self.repo.find_by_id(template_id)
    if not template or template.tenant_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template nao encontrado")
    if data.descricao != template.descricao:
        existing = await self.repo.find_by_descricao(tenant_id, data.descricao)
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Descricao ja existe")
    validate_message_template_limits(data.dict())
    return await self.repo.update(template_id, data.dict())

async def partial_update(self, template_id: UUID, tenant_id: UUID, updates: dict):
    template = await self.repo.find_by_id(template_id)
    if not template or template.tenant_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template nao encontrado")
    if "descricao" in updates and updates["descricao"] != template.descricao:
        existing = await self.repo.find_by_descricao(tenant_id, updates["descricao"])
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Descricao ja existe")
    if "body" in updates and len(updates["body"]) > 1024:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Body excede 1024 caracteres")
    if "buttons" in updates and len(updates["buttons"]) > 3:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Maximo 3 botoes permitidos")
    return await self.repo.update(template_id, updates, partial=True)

async def delete(self, template_id: UUID, tenant_id: UUID):
    template = await self.repo.find_by_id(template_id)
    if not template or template.tenant_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template nao encontrado")
    await self.repo.update(template_id, {"is_active": False})

async def get_by_id(self, template_id: UUID, tenant_id: UUID):
    template = await self.repo.find_by_id_with_relations(template_id)
    if not template or template.tenant_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template nao encontrado")
    return template

    async def list_with_pagination(self, tenant_id: UUID, page: int, limit: int, **filters):
    templates, total = await self.repo.find_with_filters(tenant_id=tenant_id, page=page, limit=limit, **filters)
    total_pages = (total + limit - 1) // limit
    display_start = (page - 1) * limit + 1
    display_end = min(page * limit, total)
    display_info = f"Exibindo {display_start} de {total} modelo(s)" if total > 0 else "Nenhum modelo encontrado"
    return {"data": templates, "pagination": {"page": page, "limit": limit, "total": total, "total_pages": total_pages}, "display_info": display_info}

async def create(self, tenant_id: UUID, data: dict, media: UploadFile = None):
    existing = await self.repo.find_by_descricao(tenant_id, data["descricao"])
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Descricao '{data['descricao']}' ja existe para este tenant")
    validate_message_template_limits(data)
    if data.get("buttons") and len(data["buttons"]) > 3:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Maximo 3 botoes permitidos")
    media_url = None
    media_type = None
    media_size = None
    if media:
        validate_media_file(media)
        media_url, media_type, media_size = await self.media_service.upload(media, tenant_id)
    if media and not data.get("type"):
        if media_type.startswith("image/"): data["type"] = "image"
        elif media_type.startswith("audio/"): data["type"] = "audio"
        elif media_type == "application/pdf": data["type"] = "document"
    template = await self.repo.create({**data, "tenant_id": tenant_id, "media_url": media_url, "media_type": media_type, "media_size": media_size})
    return template

async def update(self, template_id: UUID, tenant_id: UUID, data: dict):
    template = await self.repo.find_by_id(template_id)
    if not template or template.tenant_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template nao encontrado")
    if data.descricao != template.descricao:
        existing = await self.repo.find_by_descricao(tenant_id, data.descricao)
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Descricao ja existe")
    validate_message_template_limits(data.dict())
    return await self.repo.update(template_id, data.dict())

async def partial_update(self, template_id: UUID, tenant_id: UUID, updates: dict):
    template = await self.repo.find_by_id(template_id)
    if not template or template.tenant_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template nao encontrado")
    if "descricao" in updates and updates["descricao"] != template.descricao:
        existing = await self.repo.find_by_descricao(tenant_id, updates["descricao"])
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Descricao ja existe")
    if "body" in updates and len(updates["body"]) > 1024:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Body excede 1024 caracteres")
    if "buttons" in updates and len(updates["buttons"]) > 3:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Maximo 3 botoes permitidos")
    return await self.repo.update(template_id, updates, partial=True)

async def delete(self, template_id: UUID, tenant_id: UUID):
    template = await self.repo.find_by_id(template_id)
    if not template or template.tenant_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template nao encontrado")
    await self.repo.update(template_id, {"is_active": False})

async def get_by_id(self, template_id: UUID, tenant_id: UUID):
    template = await self.repo.find_by_id_with_relations(template_id)
    if not template or template.tenant_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template nao encontrado")
    return template

    async def list_with_pagination(self, tenant_id: UUID, page: int, limit: int, **filters):
    templates, total = await self.repo.find_with_filters(tenant_id=tenant_id, page=page, limit=limit, **filters)
    total_pages = (total + limit - 1) // limit
    display_start = (page - 1) * limit + 1
    display_end = min(page * limit, total)
    display_info = f"Exibindo {display_start} de {total} modelo(s)" if total > 0 else "Nenhum modelo encontrado"
    return {"data": templates, "pagination": {"page": page, "limit": limit, "total": total, "total_pages": total_pages}, "display_info": display_info}

async def create(self, tenant_id: UUID, data: dict, media: UploadFile = None):
    existing = await self.repo.find_by_descricao(tenant_id, data["descricao"])
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Descricao '{data['descricao']}' ja existe para este tenant")
    validate_message_template_limits(data)
    if data.get("buttons") and len(data["buttons"]) > 3:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Maximo 3 botoes permitidos")
    media_url = None
    media_type = None
    media_size = None
    if media:
        validate_media_file(media)
        media_url, media_type, media_size = await self.media_service.upload(media, tenant_id)
    if media and not data.get("type"):
        if media_type.startswith("image/"): data["type"] = "image"
        elif media_type.startswith("audio/"): data["type"] = "audio"
        elif media_type == "application/pdf": data["type"] = "document"
    template = await self.repo.create({**data, "tenant_id": tenant_id, "media_url": media_url, "media_type": media_type, "media_size": media_size})
    return template

async def update(self, template_id: UUID, tenant_id: UUID, data: dict):
    template = await self.repo.find_by_id(template_id)
    if not template or template.tenant_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template nao encontrado")
    if data.descricao != template.descricao:
        existing = await self.repo.find_by_descricao(tenant_id, data.descricao)
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Descricao ja existe")
    validate_message_template_limits(data.dict())
    return await self.repo.update(template_id, data.dict())

async def partial_update(self, template_id: UUID, tenant_id: UUID, updates: dict):
    template = await self.repo.find_by_id(template_id)
    if not template or template.tenant_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template nao encontrado")
    if "descricao" in updates and updates["descricao"] != template.descricao:
        existing = await self.repo.find_by_descricao(tenant_id, updates["descricao"])
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Descricao ja existe")
    if "body" in updates and len(updates["body"]) > 1024:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Body excede 1024 caracteres")
    if "buttons" in updates and len(updates["buttons"]) > 3:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Maximo 3 botoes permitidos")
    return await self.repo.update(template_id, updates, partial=True)

async def delete(self, template_id: UUID, tenant_id: UUID):
    template = await self.repo.find_by_id(template_id)
    if not template or template.tenant_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template nao encontrado")
    await self.repo.update(template_id, {"is_active": False})

async def get_by_id(self, template_id: UUID, tenant_id: UUID):
    template = await self.repo.find_by_id_with_relations(template_id)
    if not template or template.tenant_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template nao encontrado")
    return template

    async def upload(self, file: UploadFile, tenant_id: UUID) -> tuple:
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Tipo de arquivo nao permitido: {file.content_type}")
    content = await file.read()
    size = len(content)
    if file.content_type in ALLOWED_IMAGE_TYPES and size > MAX_IMAGE_SIZE:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Imagem excede tamanho maximo de 5MB")
    elif file.content_type in ALLOWED_DOCUMENT_TYPES and size > MAX_DOCUMENT_SIZE:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Documento excede tamanho maximo de 10MB")
    elif file.content_type in ALLOWED_AUDIO_TYPES and size > MAX_AUDIO_SIZE:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Audio excede tamanho maximo de 5MB")
    import uuid
    file_extension = file.filename.split('.')[-1] if file.filename else 'bin'
    s3_key = f"tenants/{tenant_id}/media/{uuid.uuid4()}.{file_extension}"
    self.s3_client.put_object(Bucket=self.bucket, Key=s3_key, Body=content, ContentType=file.content_type)
    url = f"https://{self.bucket}.s3.{settings.AWS_REGION}.amazonaws.com/{s3_key}"
    return url, file.content_type, size
   INSTRUCAO 4: DESIGN DO FRONTEND ANGULAR
A. Stack Tecnologica Recomendada:
Angular 17+ com standalone components
TypeScript 5+
RxJS 7+ para programacao reativa
Angular Material ou PrimeNG para componentes UI
TailwindCSS para estilizacao customizada (opcional)
Angular Reactive Forms para formularios complexos com validacoes
HttpClient para chamadas API
B. Estrutura de Pastas Sugerida:
chatbotmarcx-frontend/
src/
app/
app.component.ts
app.config.ts
app.routes.ts
core/
interceptors/
auth.interceptor.ts
error.interceptor.ts
guards/
auth.guard.ts
services/
auth.service.ts
tenant.service.ts
toast.service.ts
models/
message-template.model.ts
department.model.ts
channel.model.ts
user.model.ts
pagination.model.ts
features/
messages/
message.routes.ts
components/
message-list/
message-list.component.ts
message-list.component.html
message-list.component.scss
message-form/
message-form.component.ts
message-form.component.html
message-form.component.scss
button-editor/
button-editor.component.ts
button-editor.component.html
media-upload/
media-upload.component.ts
media-upload.component.html
services/
message-template.service.ts
department.service.ts
channel.service.ts
user.service.ts
shared/
components/
pagination/
file-upload/
emoji-picker/
loading/
pipes/
truncate.pipe.ts
environments/
environment.ts
environment.prod.ts
assets/
angular.json
package.json
tsconfig.json
C. Modelos TypeScript - message-template.model.ts:
export interface MessageTemplate {
id: string;
descricao: string;
header?: string;
body: string;
footer?: string;
type: 'text' | 'image' | 'document' | 'audio' | 'interactive' | 'standard';
departmentId: string;
department?: Department;
channelId: string;
channel?: Channel;
linkedUserId?: string;
linkedUserCode?: string;
linkedUser?: User;
mediaUrl?: string;
mediaType?: string;
mediaSize?: number;
buttons?: MessageButton[];
isActive: boolean;
createdAt: Date;
updatedAt: Date;
}
export interface MessageButton {
label: string;
action: string;
}
export interface MessageTemplateCreate {
descricao: string;
header?: string;
body: string;
footer?: string;
type: string;
departmentId: string;
channelId: string;
linkedUserId?: string;
linkedUserCode?: string;
buttons?: MessageButton[];
}
export interface PaginationResponse<T> {
data: T[];
pagination: { page: number; limit: number; total: number; totalPages: number; };
displayInfo: string;
}
export interface MessageTemplateFilters {
search?: string;
type?: string;
departmentId?: string;
channelId?: string;
isActive?: boolean;
sortBy?: string;
sortOrder?: 'asc' | 'desc';
}
D. Service Angular - message-template.service.ts:
import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { MessageTemplate, MessageTemplateCreate, MessageTemplateFilters, PaginationResponse } from '../models/message-template.model';
import { environment } from '../../../environments/environment';
@Injectable({ providedIn: 'root' })
export class MessageTemplateService {
private http = inject(HttpClient);
private apiUrl = ${environment.apiUrl}/api/v1/message-templates;
list(page: number = 1, limit: number = 10, filters?: MessageTemplateFilters): Observable<PaginationResponse<MessageTemplate>> {
let params = new HttpParams().set('page', page.toString()).set('limit', limit.toString());
if (filters) {
Object.keys(filters).forEach(key => {
const value = (filters as any)[key];
if (value !== undefined && value !== null && value !== '') {
params = params.set(key, value.toString());
}
});
}
return this.http.get<PaginationResponse<MessageTemplate>>(this.apiUrl, { params });
}
getById(id: string): Observable<MessageTemplate> {
return this.http.get<MessageTemplate>(${this.apiUrl}/${id});
}
create(template: MessageTemplateCreate, media?: File): Observable<MessageTemplate> {
if (media) {
const formData = new FormData();
formData.append('descricao', template.descricao);
formData.append('body', template.body);
if (template.header) formData.append('header', template.header);
if (template.footer) formData.append('footer', template.footer);
formData.append('type', template.type);
formData.append('department_id', template.departmentId);
formData.append('channel_id', template.channelId);
if (template.linkedUserId) formData.append('linked_user_id', template.linkedUserId);
if (template.linkedUserCode) formData.append('linked_user_code', template.linkedUserCode);
if (template.buttons) formData.append('buttons', JSON.stringify(template.buttons));
formData.append('media', media);
return this.http.post<MessageTemplate>(this.apiUrl, formData);
}
return this.http.post<MessageTemplate>(this.apiUrl, template);
}
update(id: string, template: MessageTemplateCreate): Observable<MessageTemplate> {
return this.http.put<MessageTemplate>(${this.apiUrl}/${id}, template);
}
patch(id: string, updates: Partial<MessageTemplateCreate>): Observable<MessageTemplate> {
return this.http.patch<MessageTemplate>(${this.apiUrl}/${id}, updates);
}
delete(id: string): Observable<void> {
return this.http.delete<void>(${this.apiUrl}/${id});
}
}
E. Componente de Listagem - message-list.component.ts:
import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MessageTemplateService } from '../services/message-template.service';
import { MessageTemplate, MessageTemplateFilters } from '../models/message-template.model';
import { Router } from '@angular/router';
import { debounceTime, distinctUntilChanged, Subject } from 'rxjs';
@Component({
selector: 'app-message-list',
standalone: true,
imports: [CommonModule, FormsModule],
templateUrl: './message-list.component.html',
styleUrls: ['./message-list.component.scss']
})
export class MessageListComponent implements OnInit {
private messageService = inject(MessageTemplateService);
private router = inject(Router);
templates: MessageTemplate[] = [];
loading = false;
pagination = { page: 1, limit: 10, total: 0, totalPages: 0 };
displayInfo = '';
filters: MessageTemplateFilters = {};
search = '';
typeFilter = '';
private searchSubject = new Subject<string>();
ngOnInit() {
this.loadTemplates();
this.searchSubject.pipe(debounceTime(300), distinctUntilChanged()).subscribe(value => {
this.filters.search = value;
this.pagination.page = 1;
this.loadTemplates();
});
}
onSearchChange(value: string) { this.search = value; this.searchSubject.next(value); }
onTypeFilterChange(value: string) { this.typeFilter = value; this.filters.type = value || undefined; this.pagination.page = 1; this.loadTemplates(); }
loadTemplates() {
this.loading = true;
this.messageService.list(this.pagination.page, this.pagination.limit, this.filters).subscribe({
next: (response) => { this.templates = response.data; this.pagination = response.pagination; this.displayInfo = response.displayInfo; this.loading = false; },
error: (error) => { console.error('Erro ao carregar templates', error); this.loading = false; }
});
}
onCreate() { this.router.navigate(['/messages/new']); }
onEdit(template: MessageTemplate) { this.router.navigate(['/messages/edit', template.id]); }
onDelete(template: MessageTemplate) {
if (confirm(Deseja excluir a mensagem "${template.descricao}"?)) {
this.messageService.delete(template.id).subscribe({
next: () => { this.loadTemplates(); },
error: (error) => { console.error('Erro ao excluir', error); }
});
}
}
onPageChange(page: number) { this.pagination.page = page; this.loadTemplates(); }
}
F. Template HTML - message-list.component.html:
<div class="message-list-container">
<div class="header">
<h1>Modelos de Mensagem</h1>
<button class="btn btn-primary" (click)="onCreate()"><span>+</span> Novo</button>
</div>
<div class="filters">
<div class="filter-group">
<label>Descricao:</label>
<input type="text" placeholder="Buscar..." [(ngModel)]="search" (ngModelChange)="onSearchChange($event)" />
</div>
<div class="filter-group">
<label>Tipo:</label>
<select [(ngModel)]="typeFilter" (ngModelChange)="onTypeFilterChange($event)">
<option value="">Todos</option>
<option value="text">Texto</option>
<option value="image">Imagem</option>
<option value="document">Documento</option>
<option value="audio">Audio</option>
<option value="interactive">Interativo</option>
<option value="standard">Padrao</option>
</select>
</div>
</div>
<div class="table-container" *ngIf="!loading">
<table class="table">
<thead>
<tr>
<th>Descricao</th>
<th>Tipo</th>
<th>Dono da mensagem</th>
<th>Acoes</th>
</tr>
</thead>
<tbody>
<tr *ngFor="let template of templates">
<td>{{ template.descricao }}</td>
<td>{{ template.type === 'interactive' ? 'Interativo' : template.type === 'standard' ? 'Padrao' : template.type }}</td>
<td>{{ template.linkedUser?.name || '-' }}</td>
<td class="actions">
<button class="btn-icon btn-edit" (click)="onEdit(template)" title="Editar">✏️</button>
<button class="btn-icon btn-delete" (click)="onDelete(template)" title="Excluir">🗑️</button>
</td>
</tr>
<tr *ngIf="templates.length === 0">
<td colspan="4" class="no-data">Nenhuma mensagem cadastrada</td>
</tr>
</tbody>
</table>
</div>
<div class="pagination-info" *ngIf="displayInfo">{{ displayInfo }}</div>
<div class="pagination" *ngIf="pagination.totalPages > 1">
<button [disabled]="pagination.page === 1" (click)="onPageChange(1)">«</button>
<button [disabled]="pagination.page === 1" (click)="onPageChange(pagination.page - 1)">‹</button>
<button *ngFor="let p of [].constructor(pagination.totalPages); let i = index" [class.active]="i + 1 === pagination.page" (click)="onPageChange(i + 1)">{{ i + 1 }}</button>
<button [disabled]="pagination.page === pagination.totalPages" (click)="onPageChange(pagination.page + 1)">›</button>
<button [disabled]="pagination.page === pagination.totalPages" (click)="onPageChange(pagination.totalPages)">»</button>
</div>
</div>

G. Componente de Formulario - message-form.component.ts:
import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { MessageTemplateService } from '../services/message-template.service';
import { DepartmentService } from '../services/department.service';
import { ChannelService } from '../services/channel.service';
import { ActivatedRoute, Router } from '@angular/router';
@Component({
selector: 'app-message-form',
standalone: true,
imports: [CommonModule, ReactiveFormsModule],
templateUrl: './message-form.component.html',
styleUrls: ['./message-form.component.scss']
})
export class MessageFormComponent implements OnInit {
private fb = inject(FormBuilder);
private messageService = inject(MessageTemplateService);
private departmentService = inject(DepartmentService);
private channelService = inject(ChannelService);
private route = inject(ActivatedRoute);
private router = inject(Router);
form!: FormGroup;
departments: any[] = [];
channels: any[] = [];
isEditing = false;
templateId: string | null = null;
selectedMedia: File | null = null;
mediaPreview: string | null = null;
buttons: {label: string, action: string}[] = [];
ngOnInit() {
this.initForm();
this.loadDepartments();
const id = this.route.snapshot.paramMap.get('id');
if (id) { this.isEditing = true; this.templateId = id; this.loadTemplate(id); }
}
initForm() {
this.form = this.fb.group({
descricao: ['', [Validators.required, Validators.maxLength(100)]],
header: ['', [Validators.maxLength(60)]],
body: ['', [Validators.required, Validators.maxLength(1024)]],
footer: ['', [Validators.maxLength(60)]],
type: ['text', [Validators.required]],
departmentId: ['', [Validators.required]],
channelId: ['', [Validators.required]],
linkedUserCode: [''],
linkedUserId: ['']
});
}
loadDepartments() { this.departmentService.list().subscribe({ next: (data) => this.departments = data, error: (err) => console.error('Erro ao carregar departamentos', err) }); }
onDepartmentChange(departmentId: string) {
this.form.patchValue({ channelId: '' });
this.channels = [];
if (departmentId) { this.channelService.list({ departmentId }).subscribe({ next: (data) => this.channels = data }); }
}
addMedia(file: File) {
this.selectedMedia = file;
if (file.type.startsWith('image/')) {
const reader = new FileReader();
reader.onload = () => this.mediaPreview = reader.result as string;
reader.readAsDataURL(file);
}
}
removeMedia() { this.selectedMedia = null; this.mediaPreview = null; }
addAudioRecording(audioBlob: Blob) {
const audioFile = new File([audioBlob], 'audio.ogg', { type: 'audio/ogg' });
this.selectedMedia = audioFile;
this.form.patchValue({ type: 'audio' });
}
addEmoji(emoji: string) {
const bodyControl = this.form.get('body');
if (bodyControl) { const current = bodyControl.value || ''; bodyControl.setValue(current + emoji); }
}
addButton() { if (this.buttons.length < 3) { this.buttons.push({ label: '', action: '' }); } }
removeButton(index: number) { this.buttons.splice(index, 1); }
onSave() {
if (this.form.invalid) { this.form.markAllAsTouched(); return; }
const formData = this.form.value;
formData.buttons = this.buttons.filter(b => b.label && b.action);
const request = this.isEditing ? this.messageService.update(this.templateId!, formData) : this.messageService.create(formData, this.selectedMedia || undefined);
request.subscribe({ next: () => { this.router.navigate(['/messages']); }, error: (err) => { console.error('Erro ao salvar', err); } });
}
onCancel() { this.router.navigate(['/messages']); }
}
H. Template HTML - message-form.component.html:
<div class="message-form-container">
<h2>{{ isEditing ? 'Editar Mensagem Modelo' : 'Nova Mensagem Interativa' }}</h2>
<p class="subtitle">Campos com * sao obrigatorios.</p>
<form [formGroup]="form" (ngSubmit)="onSave()">
<div class="form-group">
<label>Descricao *</label>
<input type="text" formControlName="descricao" maxlength="100" />
<span class="char-counter">{{ form.get('descricao')?.value?.length || 0 }}/100</span>
</div>
<div class="form-group">
<label>Mensagem *</label>
<div class="textarea-wrapper">
<textarea formControlName="body" maxlength="1024" rows="6"></textarea>
<button type="button" class="emoji-btn" (click)="addEmoji('😊')">😊</button>
</div>
<span class="char-counter">{{ form.get('body')?.value?.length || 0 }}/1024</span>
</div>
<div class="form-group">
<label>Cabecalho</label>
<input type="text" formControlName="header" maxlength="60" />
<span class="char-counter">{{ form.get('header')?.value?.length || 0 }}/60</span>
</div>
<div class="form-group">
<label>Rodape</label>
<input type="text" formControlName="footer" maxlength="60" />
<span class="char-counter">{{ form.get('footer')?.value?.length || 0 }}/60</span>
</div>
<div class="form-row">
<div class="form-group">
<label>Departamento *</label>
<select formControlName="departmentId" (change)="onDepartmentChange($any($event.target).value)">
<option value="">Selecione um departamento...</option>
<option *ngFor="let dept of departments" [value]="dept.id">{{ dept.name }}</option>
</select>
</div>
<div class="form-group">
<label>Canal de Atendimento *</label>
<select formControlName="channelId" [disabled]="!form.get('departmentId')?.value">
<option value="">Selecione o departamento primeiro...</option>
<option *ngFor="let ch of channels" [value]="ch.id">{{ ch.name }}</option>
</select>
</div>
</div>
<p class="helper-text">Define em qual fluxo (prototipo) esta mensagem sera usada.</p>
<div class="section-divider"></div>
<h3>Vincular a um usuario</h3>
<div class="form-row">
<div class="form-group small"><label>Cod.:</label><input type="text" formControlName="linkedUserCode" /></div>
<div class="form-group large"><label>Usuario:</label><input type="text" placeholder="Vincular mensagem ao usuario..." /></div>
</div>
<div class="section-divider"></div>
<h3>Arquivo</h3>
<p>Selecione um arquivo ou grave um audio para ser enviado:</p>
<div class="media-actions">
<button type="button" class="btn btn-secondary" (click)="fileInput.click()"><span>+</span> Selecionar arquivo</button>
<button type="button" class="btn btn-secondary" (click)="startAudioRecording()"><span>🎤</span> Gravar audio</button>
<input #fileInput type="file" accept="image/*,application/pdf,audio/*" (change)="onFileSelected($event)" hidden />
</div>
<div class="media-preview" *ngIf="selectedMedia || mediaPreview">
<div class="media-info"><span class="media-type">Imagem {{ selectedMedia?.name?.split('.').pop()?.toUpperCase() }}</span></div>
<img *ngIf="mediaPreview" [src]="mediaPreview" alt="Preview" class="media-image" />
<div class="media-actions-right">
<button type="button" class="btn-icon btn-delete" (click)="removeMedia()" title="Excluir">️</button>
<button type="button" class="btn-icon btn-download" title="Download">⬇️</button>
</div>
</div>
<p class="warning-text" *ngIf="form.get('type')?.value === 'audio'">Atencao: arquivos de audio nao acompanham mensagens de texto (a mensagem sera ignorada).</p>
<div class="section-divider"></div>
<h3>Opcoes ({{ buttons.length }}/3) - Botoes</h3>
<app-button-editor [buttons]="buttons" (buttonsChange)="buttons = $event"></app-button-editor>
<div class="form-actions">
<button type="button" class="btn btn-cancel" (click)="onCancel()">Cancelar</button>
<button type="submit" class="btn btn-save" [disabled]="form.invalid"><span>💾</span> Salvar</button>
</div>
</form>
</div>

I. Interceptor HTTP - auth.interceptor.ts:
import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { TenantService } from '../../core/services/tenant.service';
import { AuthService } from '../../core/services/auth.service';
export const authInterceptor: HttpInterceptorFn = (req, next) => {
const tenantService = inject(TenantService);
const authService = inject(AuthService);
const tenantId = tenantService.getTenantId();
const token = authService.getToken();
let clonedReq = req;
if (token) { clonedReq = clonedReq.clone({ setHeaders: { 'Authorization': Bearer ${token} } }); }
if (tenantId) { clonedReq = clonedReq.clone({ setHeaders: { 'X-Tenant-ID': tenantId } }); }
return next(clonedReq);
};
J. Interceptor de Erro - error.interceptor.ts:
import { HttpInterceptorFn, HttpErrorResponse } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { ToastService } from '../../core/services/toast.service';
import { catchError, throwError } from 'rxjs';
export const errorInterceptor: HttpInterceptorFn = (req, next) => {
const router = inject(Router);
const toastService = inject(ToastService);
return next(req).pipe(
catchError((error: HttpErrorResponse) => {
let message = 'Erro desconhecido';
switch (error.status) {
case 400: message = error.error?.detail || 'Dados invalidos'; break;
case 401: message = 'Sessao expirada. Faca login novamente.'; router.navigate(['/login']); break;
case 403: message = 'Voce nao tem permissao para esta acao'; break;
case 404: message = 'Recurso nao encontrado'; break;
case 409: message = error.error?.detail || 'Conflito de dados'; break;
case 500: message = 'Erro interno do servidor'; break;
default: message = Erro ${error.status};
}
toastService.showError(message);
return throwError(() => error);
})
);
};
INSTRUCAO 5: CHECKLIST DE IMPLEMENTACAO
A. Backend Python (FastAPI):
Fase 1 - Setup (Semana 1):
[ ] Configurar ambiente virtual Python 3.11+
[ ] Instalar FastAPI, uvicorn, sqlalchemy 2.0, pydantic v2, python-jose, bcrypt
[ ] Configurar PostgreSQL 15+ e criar banco de dados chatbotmarcx
[ ] Configurar Alembic para migrations
[ ] Criar models: Tenant, User, Department, Channel, MessageTemplate
[ ] Implementar migrations iniciais
[ ] Configurar .env com variaveis de ambiente (DATABASE_URL, SECRET_KEY, AWS_*)
[ ] Configurar CORS no main.py para permitir frontend Angular
Fase 2 - Autenticacao e Multi-Tenancy (Semana 2):
[ ] Implementar JWT authentication (login, refresh token)
[ ] Criar middleware tenant_isolation.py (extrai X-Tenant-ID)
[ ] Criar middleware authentication.py (valida JWT)
[ ] Implementar sistema de usuarios com roles (admin, attendant, manager)
[ ] Criar endpoints de login/register
[ ] Implementar base_repository.py com filtro automatico de tenant_id
Fase 3 - API de MessageTemplates (Semana 3-4):
[ ] Implementar MessageTemplateRepository (CRUD completo com filtros)
[ ] Implementar MessageTemplateService (regras de negocio, validacoes)
[ ] Implementar MessageTemplateController (endpoints RESTful)
[ ] Implementar MediaService (upload S3 com isolamento por tenant)
[ ] Adicionar validacoes Pydantic (limites de caracteres, botoes, tipos de arquivo)
[ ] Implementar paginacao com display_info (Exibindo X de Y modelo(s))
[ ] Implementar soft delete (is_active = false)
[ ] Criar endpoints de Department e Channel
[ ] Criar endpoint de User para vinculacao
[ ] Criar testes unitarios com pytest (cobertura > 80%)
Fase 4 - Documentacao e Testes (Semana 5):
[ ] Configurar Swagger/OpenAPI automatico (disponivel em /docs)
[ ] Criar testes de integracao com httpx
[ ] Configurar CI/CD (GitHub Actions)
[ ] Documentar endpoints no README
[ ] Criar script de seed com dados de exemplo
B. Frontend Angular:
Fase 1 - Setup (Semana 1):
[ ] Criar projeto Angular 17+ com standalone components
[ ] Configurar TailwindCSS ou Angular Material
[ ] Configurar HttpClient e interceptors (auth, error)
[ ] Criar models TypeScript (MessageTemplate, Department, Channel, User, Pagination)
[ ] Configurar routing com lazy loading do modulo de mensagens
[ ] Configurar Reactive Forms
Fase 2 - Servicos e Autenticacao (Semana 2):
[ ] Implementar AuthService (login, JWT storage em sessionStorage)
[ ] Implementar TenantService (gestao de tenant atual)
[ ] Criar interceptors HTTP (auth.interceptor, error.interceptor)
[ ] Implementar guards de rota (auth.guard)
[ ] Criar ToastService para notificacoes
Fase 3 - Componentes de Mensagens (Semana 3-4):
[ ] Criar MessageListComponent (tabela, filtros, paginacao completa com display info)
[ ] Criar MessageFormComponent (formulario reativo com validacoes)
[ ] Implementar contadores de caracteres (0/100, 0/1024, 0/60)
[ ] Criar componente de emoji picker (botao ao lado do textarea)
[ ] Criar componente de upload de arquivo com preview
[ ] Criar componente de gravacao de audio (MediaRecorder API)
[ ] Implementar editor de botoes dinamicos (add/remove, max 3)
[ ] Criar componente de vinculacao de usuario (busca/autocomplete)
[ ] Integrar com backend via servicos
[ ] Implementar cascata departamento -> canal (canal depende do departamento)
Fase 4 - Refinamento (Semana 5):
[ ] Adicionar loading states (spinners) em todas as operacoes assincronas
[ ] Implementar error handling global via interceptor
[ ] Melhorar responsividade mobile (tabela vira cards em telas pequenas)
[ ] Adicionar confirmacoes antes de excluir
[ ] Implementar ordenacao de colunas na tabela
[ ] Testes E2E com Cypress para fluxo completo (criar, editar, excluir)
C. Integracao e Deploy (Semana 6):
[ ] Configurar Docker para backend (Dockerfile Python)
[ ] Configurar Docker para frontend (Dockerfile Node/Angular)
[ ] Configurar docker-compose para desenvolvimento (app + db + redis)
[ ] Testar fluxo completo (CRUD de mensagens com upload de midia)
[ ] Validar multi-tenancy (criar 2 tenants, verificar isolamento de dados)
[ ] Testar paginacao e filtros com grande volume de dados
[ ] Deploy em ambiente de staging
[ ] Testes de carga com k6 ou Artillery
INSTRUCAO 6: REGRAS DE NEGOCIO E VALIDACOES
A. Validacoes de MessageTemplate:
Descricao: Obrigatoria, Maximo 100 caracteres, Unica por tenant (nao pode repetir dentro do mesmo tenant), Automaticamente convertida para maiusculas e trim, Apenas letras, numeros, espacos e underscore
Cabecalho (Header): Opcional, Maximo 60 caracteres, Usado em templates de imagem/documento (aparece acima do corpo)
Corpo (Body): Obrigatorio, Maximo 1024 caracteres, Suporta emojis e quebras de linha, Nao pode estar vazio ou apenas espacos, Variaveis dinamicas permitidas: [NOME_CLIENTE], [NOME_EMPRESA], [DATA], [HORA]
Rodape (Footer): Opcional, Maximo 60 caracteres, Geralmente usado para informacoes adicionais (horario, endereco)
Tipo: Obrigatorio, Valores: 'text', 'image', 'document', 'audio', 'interactive', 'standard'
Botoes (apenas para type='interactive'): Opcional, Maximo 3 botoes, Cada botao tem label (max 20 chars) e action (identificador unico)
Midia (Arquivo): Opcional, Tipos aceitos: Imagem (png/jpeg/jpg max 5MB), Documento (pdf max 10MB), Audio (ogg/mpeg/wav max 5MB e 1 min), Upload para S3 com estrutura: tenants/{tenant_id}/media/{uuid}.{ext}, Regra critica: arquivos de audio NAO acompanham mensagens de texto (body e ignorado quando type='audio')
Departamento e Canal: Obrigatorios, Devem existir e pertencer ao mesmo tenant, Canal depende do departamento (cascata)
Vinculacao de Usuario: Opcional, Campos: Codigo (string curta) e Usuario (busca por nome/email), Se informado, mensagem so pode ser usada/editada por este usuario
B. Regras de Isolamento Multi-Tenant:
Todas as queries devem filtrar por tenant_id (via middleware)
Usuario so pode ver/editar/excluir dados do seu tenant
Descricao de template deve ser unica dentro do tenant (nao global)
Upload de midia deve ser isolado por tenant (pasta separada no S3)
Logs e auditoria devem incluir tenant_id e user_id
Tenant inativo nao pode acessar a API (validar no middleware)
C. Regras de WhatsApp Business API (para futura integracao):
Templates aprovados pela Meta tem limites especificos (Body max 1024, Header max 60, Footer max 60, Botoes max 3)
Mensagens interativas permitem ate 3 botoes de resposta rapida, ou lista de opcoes (max 10 itens), ou calendario
Politicas de envio: Janela de 24 horas para mensagens iniciadas pelo usuario, Templates aprovados pela Meta para mensagens proativas, Rate limits por numero de telefone, Opt-out obrigatorio
Variaveis em templates: Formato {{1}}, {{2}}, {{3}} para templates aprovados. No ChatBotMarcx, usar [NOME_CLIENTE] e converter no envio
D. Regras de UX/UI (baseadas no ZigChat e HTML atual):
Listagem: Mostrar Exibindo X de Y modelo(s) no rodape, Paginacao completa, Filtros de descricao e tipo, Colunas: Descricao, Tipo, Dono da mensagem, Acoes
Formulario: Campos obrigatorios com asterisco (*), Contadores de caracteres visiveis, Botao de emoji ao lado do textarea, Secao de arquivo com dois botoes, Preview de imagem, Aviso sobre audio, Secao de vinculacao de usuario, Editor de botoes com limite de 3, Botao Salvar e Cancelar
Validacoes visuais: Campo obrigatorio vazio (borda vermelha), Limite de caracteres excedido (contador vermelho), Tipo de arquivo invalido (mensagem de erro), Descricao duplicada (erro 409)
FORMATO DE SAIDA ESPERADO
Voce deve responder com um relatorio tecnico detalhado em texto puro contendo:
Analise completa do HTML atual identificando todos os acoplamentos com um cliente especifico que precisam ser removidos ou parametrizados
Mapeamento completo das entidades MessageTemplate, Department, Channel, User com todos os atributos, tipos de dados, constraints, relacionamentos e indices
Especificacao completa dos endpoints RESTful seguindo a gramatica de APIs (Verbo HTTP, Path/Query/Body/Header Parameters, Status codes, Idempotencia, Exemplos)
Modelagem de dados SQLAlchemy completa (colunas, tipos, foreign keys, constraints, indices, soft delete)
Schemas Pydantic completos para request e response (validacoes, validators customizados, exemplos)
Implementacao completa de Controller, Service e Repository em Python (tratamento de erros, isolamento de tenant, validacoes, upload de midia)
Estrutura completa de componentes Angular (MessageListComponent, MessageFormComponent, ButtonEditorComponent, MediaUploadComponent, Servicos, Interceptors)
Plano de implementacao faseado com checklist detalhado semana a semana
Regras de negocio completas (validacoes de campos, isolamento multi-tenant, regras de WhatsApp Business API, regras de UX/UI)
Estrategia de migracao do localStorage atual para API backend (extracao, transformacao, carga, validacao)
Consideracoes sobre integracao futura com WhatsApp Business API (conversao de variaveis, aprovacao de templates, janela de 24 horas, rate limits)
O relatorio deve ser tecnico, pratico e pronto para guiar o desenvolvimento real do modulo de Mensagens Interativas do ChatBotMarcx, garantindo que seja uma plataforma generica, multi-tenant e escalavel, completamente independente de escalas, baseada no template visual e funcional do ZigChat e no HTML atual do EcoChat v2.0, usando Angular no frontend e Python (FastAPI) no backend, seguindo rigorosamente os principios da Gramatica de APIs. 