# EcoChat Marcx — Arquitetura do Sistema

## Visão Geral

Sistema de atendimento inteligente para o Hospital Marcx, com suporte a múltiplos canais, departamentos e integração com IA (DeepSeek).

---

## Estrutura de Dados Principal

```
Usuário
 ├── nivel: atendente | supervisor | gerente | administrador
 ├── departamento → Departamento (ex: Call-Center, Recepção, Ouvidoria)
 └── canal → Canal (ex: Portaria, Atendimento-Cliente)
                └── arquivoMenu → "7portaria-marcx.html"
```

### Exemplos reais cadastrados:
| Usuário   | Nível      | Departamento | Canal                   | Arquivo Menu                          |
|-----------|------------|--------------|-------------------------|---------------------------------------|
| Aldemir   | Atendente  | Call-Center  | Exames-Diagnostico      | 3examesdiagnostico-marcx.html     |
| Ana       | Atendente  | Call-Center  | Atendimento-Cliente     | 1atendimento-marcx.html           |
| João      | Atendente  | Recepção     | Portaria                | 7portaria-marcx.html              |
| Francisca | Atendente  | Ouvidoria    | Ouvidoria               | 8ouvidoria-marcx.html             |
| Daniele   | Atendente  | Call-Center  | Agendamento-Ambulatorial| 2agendamento-marcx.html           |

---

## Estrutura de Pastas

```
EcoChatMackenize/
├── frontend/                      # Angular 17 (standalone components)
│   └── src/app/
│       ├── core/
│       │   ├── models/            # Interfaces TypeScript escritas à mão
│       │   ├── services/          # Services de comunicação com a API (HttpClient)
│       │   │   ├── usuario.service.ts, departamento.service.ts, canal.service.ts
│       │   │   ├── atendimento.service.ts, menu.service.ts, modelo-mensagem.service.ts
│       │   │   ├── auth.service.ts e deepseek.service.ts
│       │   ├── guards/ / interceptors/ / pipes/ / utils/
│       │   └── api/                # GERADO — cliente OpenAPI (ver "Contrato Angular ↔ FastAPI" abaixo)
│       │       └── NÃO editar à mão; recriado via `npm run generate:api`
│       ├── pages/
│       │   ├── login/             # Tela de login
│       │   └── admin/
│       │       ├── dashboard/, usuarios/, departamentos/, canais/, niveis/
│       │       ├── atendimentos/, mensagens/, relatorio/, escalas/
│       │   └── chat/
│       │       ├── hub-menu/      # Menu principal (cliente CLICA, não digita)
│       │       └── atendimento/   # Chat por canal
│       └── app.routes.ts          # Roteamento lazy-load
│
├── backend/                        # Python 3.12 + FastAPI
│   ├── requirements.txt            # Dependências (fastapi, sqlalchemy, pydantic...)
│   ├── export_openapi.py           # Exporta o schema OpenAPI para codegen do Angular
│   ├── init_db.py / seed_data.py   # Criação de schema + dados iniciais
│   ├── run_migrations.py           # Executor das migrações SQL em migrations/
│   ├── migrations/                 # Migrações SQL versionadas (001_..., 002_...)
│   └── app/
│       ├── main.py                 # Instância FastAPI, CORS, registro de routers
│       ├── database.py             # Engine/Session do SQLAlchemy
│       ├── models/                 # Entidades ORM (entities.py: Usuario, Departamento, Canal...)
│       ├── schemas/                # DTOs Pydantic (request/response)
│       ├── services/                # Regras de negócio
│       │   ├── usuario_service.py, departamento_service.py, canal_service.py
│       │   ├── atendimento_service.py, menu_service.py, modelo_mensagem_service.py
│       │   ├── bot_service.py       # Lógica do fluxo conversacional do bot
│       │   ├── deepseek_service.py  # Integração com IA DeepSeek
│       │   ├── evolution_service.py # Integração com WhatsApp (Evolution API)
│       │   └── audio_service.py     # Texto → fala (gTTS)
│       └── routers/                 # Endpoints REST (um por domínio)
│           ├── auth.py, usuarios.py, departamentos.py, canais.py
│           ├── ia.py, mensagem.py, menus.py, modelos_mensagem.py
│           ├── atendimento.py, webhook.py, audio.py
│
├── prototipos/                    # HTMLs originais (referência visual)
└── docs/                          # Documentação
```

---

## Fluxo do Cliente (Chat)

```
1. Cliente acessa /chat/menu
2. HubMenuComponent carrega canais ativos via GET /api/canais
3. Cliente CLICA em uma opção (ex: 📞 Atendimento-Cliente)
4. Sistema navega para /chat/atendimento?canal=1
5. AtendimentoComponent carrega perguntas do canal
6. Cliente CLICA nas perguntas (não digita)
7. POST /api/ia/opcao → DeepSeekService → resposta IA
```

---

## APIs Implementadas

O FastAPI gera a documentação interativa automaticamente a partir dos routers e
dos schemas Pydantic — a lista completa e sempre atualizada dos endpoints está
em **http://localhost:8000/docs** (Swagger UI) e **/redoc** (ReDoc), não é
necessário mantê-la manualmente aqui. Alguns exemplos:

| Endpoint                     | Método | Descrição                       |
|------------------------------|--------|---------------------------------|
| /api/usuarios                | GET    | Listar com filtros              |
| /api/usuarios                | POST   | Criar usuário                   |
| /api/usuarios/{id}           | PUT    | Atualizar usuário               |
| /api/usuarios/{id}           | DELETE | Excluir usuário                 |
| /api/departamentos           | GET    | Listar departamentos            |
| /api/canais                  | GET    | Listar canais                   |
| /api/ia/opcao                | POST   | IA responde opção do menu       |
| /api/atendimento             | GET    | Fila e histórico de atendimentos|
| /api/webhook                 | POST   | Recebe eventos do WhatsApp (Evolution API) |

---

## Contrato Angular ↔ FastAPI (documentação sempre sincronizada)

O FastAPI já expõe o schema OpenAPI automaticamente a partir do código
(routers + schemas Pydantic) — não é necessário nenhum gerador externo do
lado do backend (diferente do mundo Java, onde ferramentas como
springdoc-openapi ou SmallRye OpenAPI cumprem esse papel).

Do lado do Angular, esse mesmo schema é usado para **gerar automaticamente**
os services e models TypeScript, eliminando a digitação manual e o risco de o
frontend divergir do contrato real da API:

```bash
cd frontend
npm run generate:api
```

Isso executa, em sequência:
1. `backend/export_openapi.py` — importa a app FastAPI e grava `backend/openapi.json`
2. `openapi-typescript-codegen` — gera `frontend/src/app/core/api/` (services + models Angular)

O conteúdo de `frontend/src/app/core/api/` é gerado e ignorado pelo Git —
sempre recriado a partir do backend atual, nunca editado à mão.

---

## Como Iniciar o Ambiente de Desenvolvimento

### Pré-requisitos
```bash
# Node.js 20+ e Angular CLI
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs
npm install -g @angular/cli

# Python 3.12+
sudo apt install -y python3 python3-pip python3-venv

# PostgreSQL
sudo apt install -y postgresql
sudo -u postgres createdb ecochat_marcx
sudo -u postgres psql -c "CREATE USER ecochat WITH PASSWORD 'ecochat123';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE ecochat_marcx TO ecochat;"
```

### Iniciar Backend (FastAPI)
```bash
cd backend
python3 -m venv venv
source venv/bin/activate       # Linux/Mac
pip install -r requirements.txt
cp .env.example .env           # Configurar DATABASE_URL, DEEPSEEK_API_KEY, etc.
python3 init_db.py             # Cria o schema e popula dados iniciais
uvicorn app.main:app --reload --port 8000
# API:            http://localhost:8000
# Swagger UI:     http://localhost:8000/docs
# ReDoc:          http://localhost:8000/redoc
```

### Iniciar Frontend (Angular)
```bash
cd frontend
npm install
npm run generate:api   # Gera o cliente TypeScript a partir do schema OpenAPI do backend
ng serve
# Disponível em http://localhost:4200
```

---

## Próximas Etapas (Roadmap)

- [ ] Etapa 1: Configurar ambiente (Node + Python + PostgreSQL)
- [ ] Etapa 2: Completar CRUD de Usuários/Departamentos/Canais no Angular
- [ ] Etapa 3: Implementar REST Client DeepSeek no FastAPI
- [ ] Etapa 4: Interface de chat com clique nas opções (hub-menu)
- [ ] Etapa 5: Autenticação JWT (login por usuário/senha)
- [ ] Etapa 6: Dashboard e relatórios
- [ ] Etapa 7: Integração futura com Chatwoot (webhook)
- [ ] Etapa 8: Personalização para outros modelos de negócio (multi-tenant)
