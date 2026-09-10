SKILL: ANALISE ESTRUTURAL E PLANEJAMENTO DE ARQUITETURA ANGULAR E PYTHON PARA O PROJETO CHATBOTMARCX
CONTEXTO E OBJETIVO
Voce atuara como um Arquiteto de Software Senior especialista em Angular, Python, APIs RESTful e arquitetura multi-tenant. O projeto ChatBotMarcx esta sendo desenvolvido com stack Angular no frontend e Python no backend. O foco desta analise e exclusivamente o modulo de Mensagens Interativas, que serve para criar, configurar e gerenciar templates de mensagens do WhatsApp a serem enviadas aos clientes finais. Este modulo e completamente independente e nao possui nenhuma relacao com escalas ou gestao de turnos.
REFERENCIA VISUAL E FUNCIONAL
Analise o arquivo HTML fornecido e a estrutura da interface de cadastro de mensagens baseada no modelo do ZigChat. O sistema possui:
Tela de listagem com colunas: Descricao, Tipo, Dono da mensagem, Acoes (editar/excluir), com filtragem e paginacao.
Tela de cadastro/edicao com: Campo Descricao (obrigatorio), Campo Mensagem (textarea), Secao Arquivo (upload de arquivo ou gravacao de audio), Visualizacao de midia anexada, e Secao Vincular a um usuario.
Sistema de botões interativos (ate 3 opcoes) vinculados a Departamentos e Canais de Atendimento.
CORRECAO CRITICA DE ESCOPO - SEPARACAO TOTAL DE MODULOS
E fundamental compreender e reforcar que o modulo de Mensagens Interativas e um sistema completamente isolado. Ele NAO trata de escalas, NAO trata de gestao de turnos, NAO tem relacao com profissionais de saude ou hospitais. O unico proposito deste modulo e permitir que administradores de qualquer tipo de negocio (clinicas, lojas, escolas, restaurantes, etc.) possam criar templates de mensagens padronizadas do WhatsApp. Quando um cliente interage com o ChatBot e seleciona uma opcao de menu, o sistema consulta este modulo para saber qual mensagem template deve ser enviada.
FUNDAMENTACAO TEORICA APLICADA - GRAMATICA DE APIS
Toda a analise e planejamento devem seguir rigorosamente os principios da Gramatica de APIs:
Verbos HTTP e Idempotencia:
GET: Recuperar listas ou detalhes (idempotente)
POST: Criar novos recursos (nao idempotente)
PUT: Substituir recurso completo (idempotente)
PATCH: Atualizar parcialmente (depende do contexto)
DELETE: Remover recursos (idempotente)
Tipos de Parametros:
Path Parameters: IDs na URL para identificar recursos especificos
Query Parameters: Filtros opcionais para listagens (pagina, limite, ordenacao, busca)
Body Parameters: JSON ou multipart/form-data para criar/atualizar recursos
Header Parameters: Metadados como autenticacao, tenant-id, content-type
Codigos de Status HTTP:
200 OK: Sucesso em GET, PUT, PATCH
201 Created: Sucesso ao criar recurso (POST)
204 No Content: Sucesso sem dados para retornar (DELETE)
400 Bad Request: Dados invalidos ou mal formados
401 Unauthorized: Falta de autenticacao
403 Forbidden: Autenticado mas sem permissao
404 Not Found: Recurso nao existe
500 Internal Server Error: Erro no servidor
Arquitetura em Camadas:
Controller: Ponto de entrada, valida request e delega
Service: Regras de negocio e validacoes complexas
Repository: Acesso a dados e banco de dados
Model: Estrutura das entidades
INSTRUCAO 1: AUDITORIA E MAPEAMENTO DE ENTIDADES
Analise os prints e o HTML fornecido. Identifique e documente as seguintes entidades:
Entidade MessageTemplate (Modelo de Mensagem):
id: UUID (identificador unico)
tenantId: UUID (isolamento multi-tenant)
descricao: string (max 100 chars, obrigatorio, unico por tenant)
header: string (max 60 chars, opcional)
body: string (max 1024 chars, obrigatorio)
footer: string (max 60 chars, opcional)
type: enum ('text', 'image', 'document', 'audio', 'interactive')
departmentId: UUID (FK para Department, obrigatorio)
channelId: UUID (FK para Channel, obrigatorio)
linkedUserId: UUID (FK para User, opcional)
mediaUrl: string (URL do arquivo de midia, opcional)
mediaType: enum ('image/png', 'image/jpeg', 'audio/ogg', 'application/pdf')
buttons: array de objetos (max 3 botoes, cada um com label e action)
isActive: boolean (habilita/desabilita mensagem)
createdAt: datetime
updatedAt: datetime
Entidade Department (Departamento):
id: UUID, tenantId: UUID, name: string, code: string, description: string, isActive: boolean
Entidade Channel (Canal de Atendimento):
id: UUID, tenantId: UUID, name: string, platform: enum, phoneNumber: string, isActive: boolean
Entidade User (Usuario):
id: UUID, tenantId: UUID, name: string, email: string, role: enum, departmentId: UUID
INSTRUCAO 2: DESIGN DA API RESTFUL EM PYTHON
Projete os endpoints usando FastAPI (recomendado) ou Django REST Framework.
A. Recursos de MessageTemplate:
GET /api/v1/message-templates
Query Parameters: page, limit, search, departmentId, channelId, type, isActive, sortBy, sortOrder
Headers: Authorization (Bearer JWT), X-Tenant-ID
Response 200: JSON com array de dados e objeto de paginacao
POST /api/v1/message-templates
Body Parameters: JSON com descricao, header, body, footer, departmentId, channelId, linkedUserId, type, buttons
Files (opcional): media (multipart/form-data)
Headers: Authorization, X-Tenant-ID
Response 201: Objeto criado
Validacoes no Service: descricao unica por tenant, body max 1024 chars, max 3 botoes, departmentId e channelId devem existir.
PUT /api/v1/message-templates/{id}
Path Parameters: id (UUID)
Body Parameters: Mesma estrutura do POST (substituicao completa)
Response 200: Template atualizado completo
Idempotencia: Sim
PATCH /api/v1/message-templates/{id}
Path Parameters: id (UUID)
Body Parameters: Apenas campos a atualizar (JSON parcial)
Response 200: Template atualizado parcialmente
DELETE /api/v1/message-templates/{id}
Path Parameters: id (UUID)
Response 204: No Content
Idempotencia: Sim (implementar soft delete setando isActive = false)
B. Recursos de Department e Channel:
GET /api/v1/departments (Query: isActive, search)
POST /api/v1/departments
GET /api/v1/channels (Query: platform, isActive)
INSTRUCAO 3: ARQUITETURA BACKEND PYTHON
A. Stack Tecnologica Recomendada:
Framework: FastAPI
ORM: SQLAlchemy
Validacao: Pydantic
Banco de Dados: PostgreSQL
Autenticacao: JWT (python-jose)
Upload de Arquivos: AWS S3 ou MinIO
Background Tasks: Celery + Redis
B. Estrutura de Pastas Sugerida (FastAPI):
app/main.py (ponto de entrada)
app/config.py (variaveis de ambiente)
app/database.py (conexao PostgreSQL)
app/models/ (SQLAlchemy models: tenant, user, department, channel, message_template)
app/schemas/ (Pydantic models para request/response)
app/repositories/ (CRUD generico e especifico)
app/services/ (Regras de negocio, media_service)
app/controllers/ (Endpoints RESTful)
app/middleware/ (authentication, tenant_isolation)
app/utils/ (exceptions, validators)
C. Middleware de Tenant Isolation:
Extrair e validar o tenant_id do header X-Tenant-ID ou do token JWT. Garantir que todas as queries no Repository filtrem automaticamente por tenant_id para evitar vazamento de dados entre clientes.
INSTRUCAO 4: DESIGN DO FRONTEND ANGULAR
A. Stack Tecnologica Recomendada:
Angular 17+ (standalone components)
TypeScript 5+
RxJS 7+
Angular Material ou PrimeNG
Angular Reactive Forms
HttpClient
B. Estrutura de Pastas Sugerida:
src/app/core/interceptors/ (auth.interceptor, error.interceptor)
src/app/core/services/ (auth.service, tenant.service)
src/app/core/models/ (message-template.model, department.model)
src/app/features/messages/components/ (message-list, message-form, button-editor)
src/app/features/messages/services/ (message-template.service)
src/app/shared/components/ (pagination, file-upload)
C. Service Angular (message-template.service.ts):
Implementar metodos list, getById, create, update, patch, delete.
O metodo create deve lidar com FormData caso haja upload de midia, ou JSON puro caso contrario.
D. Interceptor HTTP (auth.interceptor.ts):
Interceptar todas as requisicoes HttpClient para injetar automaticamente o header Authorization (Bearer token) e o header X-Tenant-ID.
INSTRUCAO 5: CHECKLIST DE IMPLEMENTACAO
A. Backend Python:
Fase 1: Setup (ambiente virtual, FastAPI, SQLAlchemy, PostgreSQL, Alembic).
Fase 2: Autenticacao e Multi-Tenancy (JWT, middleware de tenant, sistema de usuarios).
Fase 3: API de MessageTemplates (Repository, Service, Controller, upload de midia, validacoes Pydantic).
Fase 4: Documentacao e Testes (Swagger/OpenAPI, testes unitarios com pytest).
B. Frontend Angular:
Fase 1: Setup (projeto Angular, Tailwind/Material, HttpClient, routing).
Fase 2: Servicos e Autenticacao (AuthService, TenantService, interceptors).
Fase 3: Componentes de Mensagens (MessageListComponent com tabela e paginacao, MessageFormComponent com Reactive Forms e validacoes de limite de caracteres, editor de botoes dinamicos).
Fase 4: Refinamento (loading states, error handling, responsividade).
INSTRUCAO 6: REGRAS DE NEGOCIO E VALIDACOES
Validacoes de MessageTemplate:
Descricao: Obrigatorio, max 100 chars, unico por tenant, apenas letras maiusculas/numeros/underscore.
Header: Opcional, max 60 chars.
Body: Obrigatorio, max 1024 chars, suporta emojis e quebras de linha.
Footer: Opcional, max 60 chars.
Buttons: Opcional, max 3 botoes (label max 20 chars, action identificador unico).
Media: Opcional, tipos aceitos imagem/doc/audio, limites de tamanho (max 5MB a 10MB).
Regras de Isolamento Multi-Tenant:
Todas as queries devem filtrar por tenant_id.
Usuario so pode ver/editar dados do seu tenant.
Descricao de template deve ser unica dentro do tenant.
Regras de WhatsApp Business API:
Respeitar os limites de caracteres da Meta para templates aprovados.
Mensagens interativas permitem ate 3 botoes ou lista de opcoes.
FORMATO DE SAIDA ESPERADO
Voce deve responder com um relatorio tecnico detalhado em texto puro, sem formatacao markdown, contendo:
Analise do estado atual do HTML e identificacao do que precisa ser migrado.
Mapeamento completo das entidades com atributos, tipos e relacionamentos.
Especificacao completa dos endpoints RESTful (verbos, parametros, status codes, idempotencia).
Modelagem de dados SQLAlchemy completa.
Schemas Pydantic para request/response.
Exemplos de implementacao de Controller, Service e Repository em Python.
Estrutura de componentes Angular e interceptors.
Plano de implementacao faseado com checklist.
Regras de negocio e consideracoes sobre WhatsApp Business API.