EcoChatBot-MA/
│
├── .env                                🔒 Variáveis (não commitar)
├── .env.example                        📋 Template
├── .gitignore                          🚫 Ignorar arquivos
├── README.md                           📖 Documentação Principal
├── package.json                        📦 Orquestrador (Root)
├── docker-compose.yml                  🐳 Orquestração (mongo + redis + postgres)
│
├── docs/                               📚 Documentação Detalhada
│   ├── ESTRUTURA.md
│   ├── ARQUITETURA.md
│   ├── API.md
│   ├── BANCO-DE-DADOS.md
│   ├── ACESSIBILIDADE.md
│   └── CANAIS.md
│
├── scripts/                            🛠️ Scripts Globais
│   ├── setup.sh
│   ├── dev.sh
│   └── backup.sh
│
├── backend/                            🐍 Backend (Python/FastAPI)
│   ├── package.json                    📦 Node helpers (se houver)
│   ├── requirements.txt                📦 Dependências de Produção
│   ├── requirements-dev.txt            📦 Dependências de Dev/Teste
│   ├── main.py                         🚀 Entry Point FastAPI
│   ├── export_openapi.py               📤 Exportador OpenAPI
│   ├── alembic.ini                     🐘 Config Alembic
│   │
│   ├── alembic/                        🐘 Migrações de Banco
│   │   ├── env.py
│   │   └── versions/
│   │
│   └── app/                            📦 Pacote Principal da Aplicação
│       ├── __init__.py
│       ├── config.py                   ⚙️ Configurações (Pydantic Settings)
│       ├── database.py                 🐘 Engine, Session e Base (SQLAlchemy)
│       ├── mongodb.py                  🍃 Conexão MongoDB
│       ├── redis_client.py             ⚡ Conexão Redis
│       ├── deps.py                     🔗 Injeção de Dependências FastAPI
│       ├── security.py                 🔐 JWT + Hashing + RBAC
│       │
│       ├── exceptions/                 🚨 Tratamento de Erros (Consolidado)
│       │   ├── __init__.py
│       │   ├── base_exceptions.py
│       │   ├── auth_exceptions.py
│       │   ├── canal_exceptions.py
│       │   ├── ia_exceptions.py
│       │   ├── integracao_exceptions.py
│       │   ├── tenant_exceptions.py
│       │   ├── usuario_exceptions.py
│       │   ├── webhook_exceptions.py
│       │   └── atendimento_exceptions.py
│       │
│       ├── models/                     🗄️ Camada de Domínio (ORM)
│       │   ├── __init__.py             🎯 Exporta modelos
│       │   ├── enums.py                🆕 Enumerações (Status, Perfis, Tipos)
│       │   ├── mixins.py               🆕 Classes base (Timestamps, SoftDelete)
│       │   │
│       │   ├── empresa_models.py       🏢 Empresa, Usuario, InstanciaChatbot
│       │   ├── cliente_models.py       🏢 Cliente (Tenant)
│       │   ├── contato_models.py       📇 Contatos
│       │   ├── departamento_models.py  🏛️ Departamentos
│       │   │
│       │   ├── atendimento_models.py   🎧 Atendimentos
│       │   ├── atendimento_context_models.py 📝 Contexto/Variáveis do Bot
│       │   ├── chamada_pabx_models.py  📞 Registro de Chamadas
│       │   ├── canal_models.py         📡 Canais (WhatsApp, Telegram, etc)
│       │   ├── conexao_models.py       🔗 Status de Conexões
│       │   │
│       │   ├── instancia_chatbot_models.py 🤖 Configurações de Bot
│       │   ├── menu_models.py          🍔 Menus e Fluxos
│       │   ├── modelo_mensagem_models.py 📝 Templates de Mensagem
│       │   │
│       │   ├── campanha_models.py      📢 Campanhas de Marketing
│       │   ├── pedido_models.py        🛒 Pedidos/E-commerce
│       │   ├── email_models.py         📧 Templates e Logs de E-mail
│       │   └── token_revogado_models.py 🚫 Blacklist de JWT
│       │
│       ├── schemas/                    📐 Validação (Pydantic)
│       │   ├── __init__.py             ⚠️ Revisar
│       │   ├── auth_schemas.py         ✅ Implementado
│       │   ├── atendimento_schemas.py  ⚠️ Revisar
│       │   ├── canal_schemas.py        ⚠️ Revisar
│       │   ├── usuario_schemas.py      ⚠️ Revisar
│       │   └── ...                     ❌ Faltam schemas para Contato, Campanha, etc.
│       │
│       ├── repositories/               💾 Acesso a Dados (DAL)
│       │   ├── __init__.py
│       │   ├── base_repository.py      ✅ Implementado
│       │   ├── usuario_repository.py   ⚠️ Revisar
│       │   ├── chamada_repository.py   ⚠️ Revisar
│       │   ├── canal_repository.py     ❌ FALTA
│       │   ├── atendimento_repository.py ❌ FALTA
│       │   ├── departamento_repository.py ❌ FALTA
│       │   └── ...                     ❌ Faltam repos para as outras entidades
│       │
│       ├── services/                   💼 Regras de Negócio
│       │   ├── __init__.py             ⚠️ Revisar
│       │   ├── auth_service.py         ⚠️ Revisar
│       │   ├── departamento_service.py ⚠️ Revisar
│       │   ├── canal_service.py        ⚠️ Revisar
│       │   ├── atendimento_service.py  ⚠️ Revisar
│       │   ├── menu_service.py         ⚠️ Revisar
│       │   ├── contato_service.py      ⚠️ Revisar
│       │   ├── campanha_service.py     ⚠️ Revisar
│       │   ├── email_service.py        ⚠️ Revisar
│       │   ├── audio_service.py        ⚠️ Revisar
│       │   ├── evolution_service.py    ⚠️ Revisar
│       │   ├── conexao_service.py      ⚠️ Revisar
│       │   ├── tenant_service.py       ⚠️ Revisar
│       │   ├── pabx_service.py         ⚠️ Revisar
│       │   ├── aps_service.py          ⚠️ Revisar
│       │   ├── webhook_service.py      ⚠️ Revisar
│       │   ├── bot_service.py          ⚠️ Revisar
│       │   ├── arquivo_service.py      ⚠️ Revisar
│       │   ├── modelo_mensagem_service.py ⚠️ Revisar
│       │   ├── usuario_service.py      ❌ FALTA
│       │   ├── deepseek_service.py     ❌ FALTA
│       │   │
│       │   └── bot_handlers/           🤖 Lógica de Fluxo do Bot
│       │       ├── __init__.py         ⚠️ Revisar
│       │       ├── core.py             ⚠️ Revisar (absorve base_handler.py)
│       │       ├── validators.py       ✅ Implementado
│       │       ├── utils.py            ✅ Implementado
│       │       ├── privacy.py          ✅ Implementado
│       │       ├── evolution_client.py ✅ Implementado
│       │       ├── atendimento_handler.py ✅ Implementado
│       │       ├── agendamento_handler.py ✅ Implementado
│       │       ├── pedidos_handler.py  ✅ Implementado
│       │       ├── dynamic_flow.py     ✅ Implementado
│       │       ├── tenant_handler.py   ✅ Implementado
│       │       ├── handler_factory.py  ✅ Implementado
│       │       └── bot_machine.py      ✅ Implementado
│       │
│       ├── routers/                    🌐 Endpoints (API)
│       │   ├── __init__.py             ⚠️ Revisar
│       │   ├── auth_router.py          ⚠️ Revisar (Padronizado p/ singular)
│       │   ├── usuario_router.py       ⚠️ Revisar
│       │   ├── departamento_router.py  ⚠️ Revisar
│       │   ├── canal_router.py         ⚠️ Revisar
│       │   ├── atendimento_router.py   ⚠️ Revisar
│       │   ├── menu_router.py          ⚠️ Revisar
│       │   ├── contato_router.py       ⚠️ Revisar
│       │   ├── campanha_router.py      ⚠️ Revisar
│       │   ├── email_router.py         ⚠️ Revisar
│       │   ├── conexao_router.py       ⚠️ Revisar
│       │   ├── empresa_router.py       ⚠️ Revisar
│       │   ├── dashboard_router.py     ⚠️ Revisar
│       │   ├── ia_router.py            ⚠️ Revisar
│       │   ├── mensagem_router.py      ⚠️ Revisar
│       │   ├── audio_router.py         ⚠️ Revisar
│       │   ├── webhook_router.py       ⚠️ Revisar
│       │   │
│       │   └── tenant/                 🏢 Rotas específicas por Tenant
│       │       ├── __init__.py         ⚠️ Revisar
│       │       ├── atendimentos.py     ⚠️ Revisar
│       │       └── usuario.py          ⚠️ Revisar
│       │
│       ├── jobs/                       ⏰ Tarefas Assíncronas (Celery)
│       │   ├── __init__.py             ❌ FALTA
│       │   ├── celery_app.py           ❌ FALTA
│       │   └── backup.py               ❌ FALTA (Backup MongoDB→PG)
│       │
│       ├── integrations/               🔌 APIs Externas e Canais
│       │   ├── __init__.py             ✅ Implementado
│       │   ├── base.py                 ⚠️ Revisar
│       │   ├── whatsapp_integration.py ✅ Implementado
│       │   ├── telegram_integration.py ✅ Implementado
│       │   ├── discord_integration.py  ✅ Implementado
│       │   ├── instagram_integration.py ✅ Implementado
│       │   ├── facebook_integration.py ✅ Implementado
│       │   ├── microsip_integration.py ✅ Implementado
│       │   ├── ocr_integration.py      ✅ Implementado
│       │   └── tts_integration.py      ✅ Implementado
│       │
│       └── tests/                      🧪 Testes Automatizados
│           ├── __init__.py             ❌ FALTA
│           ├── conftest.py             ❌ FALTA (Fixtures)
│           ├── test_atendimento_router.py ❌ FALTA
│           ├── test_atendimento_service.py ❌ FALTA
│           ├── test_base_repository.py ❌ FALTA
│           ├── test_indicadores.py     ❌ FALTA
│           └── test_repositories_subclasses.py ❌ FALTA
│
└── frontend/                           🅰️ Frontend (Angular)
    ├── package.json
    ├── angular.json
    ├── tsconfig.json
    ├── tsconfig.app.json
    ├── tsconfig.spec.json
    │
    └── src/
        ├── app/
        │   ├── core/
        │   │   ├── api/
        │   │   │   ├── core/
        │   │   │   ├── models/
        │   │   │   ├── services/
        │   │   │   ├── api-error.interceptor.ts
        │   │   │   ├── token.resolver.ts
        │   │   │   ├── api.extensions.module.ts
        │   │   │   └── index.api.ts
        │   │   │
        │   │   ├── auth/
        │   │   │   ├── guards/
        │   │   │   ├── models/
        │   │   │   ├── sessions.facade.ts
        │   │   │   ├── token.storage.ts
        │   │   │   ├── niveis.auth.ts
        │   │   │   └── index.auth.ts
        │   │   │
        │   │   ├── services/
        │   │   │   ├── ocr.service.ts
        │   │   │   ├── tts.service.ts
        │   │   │   └── toast.service.ts
        │   │   │
        │   │   └── utils/
        │   │
        │   ├── features/
        │   │   ├── auth/
        │   │   ├── admin/
        │   │   └── configuracoes/
        │   │
        │   ├── shared/
        │   │   ├── components/
        │   │   ├── directives/
        │   │   ├── pipes/
        │   │   └── models/
        │   │
        │   ├── app.component.ts
        │   ├── app.config.ts
        │   └── app.routes.ts
        │
        ├── assets/
        └── environments/