EcoChatBot-MA/
│
├── .env                                🔒 Variáveis (não commitar)
├── .env.example                        📋 Template
├── .gitignore                          🚫
├── README.md                           📖
├── package.json                        📦 Orquestrador
├── docker-compose.yml                  🐳 APENAS AQUI (mongo + redis + postgres)
│
├── docs/
│   ├── ESTRUTURA.md
│   ├── ARQUITETURA.md
│   ├── API.md
│   ├── BANCO-DE-DADOS.md
│   ├── ACESSIBILIDADE.md
│   └── CANAIS.md
│
├── scripts/
│   ├── setup.sh
│   ├── dev.sh
│   └── backup.sh
│
├── backend/
│   ├── package.json                    📦 Node helpers
│   ├── requirements.txt                🐍 Python prod
│   ├── requirements-dev.txt            🐍 Python dev
│   ├── main.py                         🚀 FastAPI entry
│   ├── export_openapi.py               📤 OpenAPI
│   ├── alembic.ini                     🐘 Migrations
│   │
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/
│   │
│   ├── app/
│   │   ├── __init__.py
│   │   ├── database.py                 🐘 PostgreSQL           Implementado 25/09/2026 Ultima Versão
│   │   ├── mongodb.py                  🍃 MongoDB              Implementado 25/09/2026 Ultima Versão
│   │   ├── redis_client.py             ⚡ Redis                Implementado 25/09/2026 Ultima Versão
│   │   ├── deps.py                     🔗 Dependencies         Implementado 25/09/2026 Ultima Versão
│   │   ├── exceptions.py               🚨 Base + canal + repo  Implementado 24/05/2026 Ultima Versão
│   │   ├── security.py                 🔐 JWT + RBAC❌ FALTA   Implementado 24/05/2026 Ultima Versão
│   │   ├── config.py                   Implementado 24/05/2026 Ultima Versão
│   │   │
│   │   ├── exceptions/
│   │   │   ├── __init__.py                 🎯 Implementado 25/09/2026 Ultima Versão
│   │   │   └── atendimento_exceptions.py   🎯 Implementado 25/09/2026 Ultima Versao
│   │   │   └── auth_exceptions.py          🎯 Implementado 25/09/2026 Ultima Versao.
│   │   │   └── base_exceptions.py          🎯 Implementado 25/09/2026 Ultima Versao
│   │   │   └── canal_exceptions.py         🎯 Implementado 16/09/2026 Ultima Versao
│   │   │   └── ia_exceptions.py            🎯 Implementado 25/09/2026 Ultima Versao
│   │   │   └── integracao_exceptions.py    🎯 Implementado 25/09/2026 Ultima Versao
│   │   │   └── tenant_exceptions.py        🎯 Implementado 25/09/2026 Ultima Versao
│   │   │   └── usuario_exceptions.py       🎯 Implementado 25/09/2026 Ultima Versao
│   │   │   └── webhook_exceptions.py       🎯 Implementado 25/09/2026 Ultima Versao
│   │   │
│   │   ├── models/
│   │   │   ├── __init__.py             🎯 APENAS imports  esta implementado❌ FALTA
│   │   │   ├── cliente_models.py       🏢 Cliente (tenant) Não implmentado❌ FALTA
│   │   │   ├── usuario_models.py       👤 Usuario + NivelUsuario não implmentado❌ FALTA
│   │   │   ├── departamento_models.py  🏛️ Departamento falta implementar o script❌ FALTA
│   │   │   ├── canal_models.py         📡 Canal implementado OK
│   │   │   ├── atendimento_models.py   🎧 Atendimento implementado OK
│   │   │   ├── atendimento_context_models.py  📝 Context Implementado OK
│   │   │   ├── menu_models.py          🍔 Menu + MenuOpcao ❌ FALTANão Implementado 
│   │   │   ├── models.py               ❌ FALTAfalta implementar models.py  esse arquivo esta implementado e trata-se de  Define as tabelas e relacionamentos do banco de dados utilizando o ORM  SQLAlchemy. Este arquivo atua como a "fonte da verdade" para a estrutura  de dados da aplicação, garantindo integridade referencial através de     Foreign Keys e facilitando as consultas via objetos Python.nao conssegui entender para que serve refaça e com base da analise sugerir um nome
│   │   │   ├── modelo_mensagem_models.py  📝 Template falta implementar❌ FALTA
│   │   │   ├── conexao_models.py       🔌 WABA  Falta implementar.❌ FALTA
│   │   │   ├── contato_models.py       📇 Contato falta implementar❌ FALTA
│   │   │   ├── email_models.py         📧 Email falta implementar.❌ FALTA
│   │   │   ├── campanha_models.py      📢 Campanha falta implementar❌ FALTA
│   │   │   ├── arquivo_models.py       📎 Arquivo fala implementar❌ FALTA
│   │   │   ├── pedido_models.py        🛒 Pedido falta implementar❌ FALTA
│   │   │   ├── token_revogado_models.py 🚫 JWT Blacklist  aqui falta implementar.❌ FALTA
│   │   │   ├── empresa_models.py       🏢 Empresa (SaaS) aqui uma atenção falta implementar e nesse objeto que vai diferencia os clientes seus usuarios e modelo de negocio falta implementar
│   │   │   ├── instancia_chatbot_models.py  🤖 Evolution API aqui tambem falta atualizar.. ❌ FALTA
│   │   │   └── chamada_pabx_models.py  ☎️ CDR PABX falta implementar ❌ FALTA
│   │   │
│   │   ├── schemas/
│   │   │   ├── __init__.py            🎯implementado mas revisar
│   │   │   ├── auth_schemas.py        🎯implementado
│   │   │   ├── atendimento_schemas.py 🎯implementado mas revisar
│   │   │   ├── canal_schemas.py       🎯implementado mas revisar
│   │   │   ├── usuario_schemas.py     🎯implementado mas revisar
│   │   │   └── ...
│   │   │
│   │   ├── repositories/
│   │   │   ├── __init__.py
│   │   │   ├── base_repository.py
│   │   │   ├── usuario_repository.py         🎯implementado mas revisar  
│   │   │   ├── canal_repository.py           ❌ FALTA
│   │   │   ├── atendimento_repository.py     ❌ FALTA
│   │   │   ├── departamento_repository.py    ❌ FALTA
│   │   │   └── chamada_repository.py         🎯implementado mas revisar
│   │   │
│   │   ├── services/
│   │   │   ├── __init__.py                 🎯implementado mas revisar
│   │   │   ├── auth_service.py             🔐 JWT 🎯implementado mas revisar Centraliza toda a lógica de segurança, autenticação e manipulação de tokens     JWT (JSON Web Tokens)
│   │   │   ├── usuario_service.py          ❌ FALTA
│   │   │   ├── departamento_service.py     🎯implementado.Mas revisar
│   │   │   ├── canal_service.py            🎯implementado.Mas revisar   
│   │   │   ├── atendimento_service.py      🎯implementado.Mas revisar
│   │   │   ├── menu_service.py             🎯implementado.Mas revisar
│   │   │   ├── modelo_mensagem_service.py  🎯implementado.Mas revisar 
│   │   │   ├── contato_service.py          🎯implementado.Mas revisar
│   │   │   ├── campanha_service.py         🎯implementado.Mas revisar
│   │   │   ├── email_service.py            🎯implementado.Mas revisar
│   │   │   ├── audio_service.py            🎯implementado.Mas revisar
│   │   │   ├── evolution_service.py        🎯implementado.Mas revisar
│   │   │   ├── conexao_service.py          🎯implementado.Mas revisar     
│   │   │   ├── tenant_service.py           🎯implementado.Mas revisar 
│   │   │   ├── deepseek_service.py         ❌ FALTA
│   │   │   ├── pabx_service.py             🎯implementado.Mas revisar
│   │   │   ├── aps_service.py              🎯implementado.Mas revisar
│   │   │   ├── webhook_service.py          🎯implementado.Mas revisar mas nao tinha nessa arvore
│   │   │   ├── bot_service.py              🎯implementado.Mas revisar mas nao tinha nessa arvore
│   │   │   ├── arquivo_service.py          🎯implementado.Mas revisar mas nao tinha nessa arvore
│   │   │   │
│   │   │   └── bot_handlers/
│   │   │       ├── __init__.py         🎯implementado mas revisar
│   │   │       ├── core.py             (absorve base_handler.py)🎯implementado mas revisar
│   │   │       ├── validators.py       🎯implementado
│   │   │       ├── utils.py            🎯implementado
│   │   │       ├── privacy.py            🎯implementado
│   │   │       ├── evolution_client.py 🎯implementado
│   │   │       ├── atendimento_handler.py  🎯implementado
│   │   │       ├── agendamento_handler.py   🎯implementado
│   │   │       ├── pedidos_handler.py    🎯implementado
│   │   │       ├── dynamic_flow.py   🎯implementado
│   │   │       ├── tenant_handler.py 🎯implementado
│   │   │       ├── handler_factory.py  🎯implementado
│   │   │       └── bot_machine.py    🎯implementado
│   │   │
│   │   ├── routers/
│   │   │   ├── __init__.py    🎯implementado mas revisar
│   │   │   ├── auth_routers.py  🎯implementado mas revisar
│   │   │   ├── usuario_routers.py  🎯implementado mas revisar
│   │   │   ├── departamentos_routers.py 🎯implementado mas revisar
│   │   │   ├── canais_routers.py 🎯implementado mas revisar
│   │   │   ├── atendimento_routers.py  🎯implementado mas revisar
│   │   │   ├── menus_routers.py    🎯implementado mas revisar
│   │   │   ├── modelos_mensagem_routers.py  🎯implementado mas revisar
│   │   │   ├── contatos_routers.py   🎯implementado mas revisar
│   │   │   ├── campanhas_routers.py  🎯implementado mas revisar
│   │   │   ├── emails_routers.py     🎯implementado mas revisar
│   │   │   ├── conexoes_routers.py    🎯implementado mas revisar
│   │   │   ├── empresas_routers.py   🎯implementado mas revisar
│   │   │   ├── dashboard_routers.py  🎯implementado mas revisar
│   │   │   ├── ias_routers.py  🎯implementado mas revisar
│   │   │   ├── mensagens_routers.py 🎯implementado mas revisar
│   │   │   ├── audio_routers.py   🎯implementado mas revisar
│   │   │   ├── webhook_routers.py  🎯implementado mas revisar
│   │   │   └── tenant/
│   │   │       ├── __init__.py 🎯implementado mas revisar
│   │   │       ├── atendimentos.py 🎯implementado mas revisar
│   │   │       └── usuario.py🎯implementado mas revisar
│   │   │
│   │   ├── jobs/                       ⏰ Celery (backup MongoDB→PG)   ❌ FALTA  gerar script implementar
│   │   │   ├── __init__.py  ❌ FALTA  gerar script implementar
│   │   │   ├── backup.py  ❌ FALTA  gerar script implementar
│   │   │   └── celery_app.py   ❌ FALTA  gerar script implementar
│   │   │
│   │   ├── integrations/ 🔌 Canais   
│   │   │   ├── __init__.py           🎯implementado
│   │   │   ├── base.py               🎯implementado mas revisar
│   │   │   ├── whatsapp_integration.py  🎯implementado
│   │   │   ├── telegram_integration.py 🎯implementado
│   │   │   ├── discord_integration.py 🎯implementado
│   │   │   ├── instagram_integration.py 🎯implementado
│   │   │   ├── facebook_integration.py 🎯implementado
│   │   │   ├── microsip_integration.py 🎯implementado
│   │   │   ├── ocr_integration.py 🎯implementado
│   │   │   └── tts_integration.py 🎯implementado
│   │   │
│   │   └── tests/
│   │       ├── __init__.py❌ FALTA
│   │       ├── conftest.py❌ FALTA
│   │       ├── test_atendimento_router.py❌ FALTA
│   │       ├── test_atendimento_service.py❌ FALTA
│   │       ├── test_base_repository.py  ❌ FALTA     
│   │       ├── test_indicadores.py❌ FALTA
│   │       └── test_repositories_subclasses.py ❌ FALTA
│   │
│   └── scripts/
│       ├── ping-mongo.js❌ FALTA  gerar script implementar
│       ├── ping-redis.js❌ FALTA  gerar script implementar
│       └── ping-postgres.js ❌ FALTA  gerar script implementar
│
└── frontend/
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