EcoChatBot-MA/                                    ← raiz
│
├── README.md                                     📘 Documentação principal
├── AGENTS.md                                     🆕 Guia de agentes IA / convenções
├── .gitignore                                    🚫 Exclusões Git
├── docker-compose.yml                            🐳 Containers (atualizado hoje)
├── package.json                                  📦 Metadados Node (atualizado hoje)
├── package-lock.json                             🔒 Lock de dependências
│
├── roteiros/                                     📄 HTML dos fluxos de atendimento
│   ├── hub_Menu.html                             🏠 Menu principal
│   ├── atendimento.html                          🎧 Atendimento geral
│   ├── agendamento.html                          📅 Agendamento
│   ├── informacoes.html                          ℹ️ Informações
│   ├── financeiro.html                           💰 Financeiro
│   └── suporte.html                              🛠️ Suporte
│
├── frontend/                                     🅰️ Angular 17 — atualizado hoje
│   └── src/
│       ├── main.ts
│       ├── index.html
│       └── app/
│           ├── app.component.ts
│           ├── app.routes.ts
│           │
│           ├── core/
│           │   ├── auth/                         🔐 Autenticação
│           │   │   └── token.resolver.ts
│           │   ├── models/                       📦 Modelos TS
│           │   │   ├── usuario.model.ts
│           │   │   ├── departamento.model.ts
│           │   │   ├── canal.model.ts
│           │   │   └── nivel-usuario.model.ts
│           │   └── services/
│           │       ├── usuario.service.ts
│           │       ├── departamento.service.ts
│           │       ├── canal.service.ts
│           │       └── ia.service.ts
│           │
│           ├── pages/
│           │   ├── admin/
│           │   │   ├── dashboard/
│           │   │   ├── usuarios/
│           │   │   ├── departamentos/
│           │   │   ├── canais/
│           │   │   ├── niveis/
│           │   │   ├── horarios/
│           │   │   └── relatorios/
│           │   └── atendimento/
│           │       ├── menu/
│           │       └── conversa/
│           │
│           └── shared/
│               └── components/layout/
│
├── backend/                                      🐍 FastAPI — atualizado hoje
│   ├── requirements.txt
│   ├── .env.example
│   ├── init_db.py
│   ├── seed_data.py
│   ├── run_migrations.py
│   ├── export_openapi.py
│   ├── migrations/
│   │
│   └── app/
│       ├── main.py                               🚀 Entrypoint FastAPI
│       ├── database.py                           🗄️ SQLAlchemy async
│       │
│       ├── models/                               🗄️ Camada ORM (consolidada)
│       │   ├── __init__.py                       🎯 Exporta todos
│       │   ├── base.py                           🧱 DeclarativeBase
│       │   ├── enums.py                          🔢 Enumerações
│       │   ├── mixins.py                         ♻️ Timestamps/SoftDelete/Tenant
│       │   ├── cliente_models.py                 🏢 Cliente (tenant raiz)
│       │   ├── empresa_models.py                 🏢 Empresa·Usuario·Instancia
│       │   ├── contato_models.py                 📇 Contatos
│       │   ├── departamento_models.py            🏛️ Departamentos
│       │   ├── canal_contratado_models.py        📡 Canais contratados
│       │   ├── conexao_models.py                 🔗 Conexões
│       │   ├── menu_models.py                    🍔 Menu·MenuItem
│       │   ├── roteiro_models.py                 🗺️ Roteiro
│       │   ├── atendimento_models.py             🎧 Atendimentos
│       │   ├── atendimento_context_models.py     📝 Contexto
│       │   ├── chamada_pabx_models.py            📞 PABX
│       │   ├── modelo_mensagem_models.py         💬 Templates
│       │   ├── campanha_models.py                📢 Campanhas
│       │   ├── pedido_models.py                  🛒 Pedidos
│       │   ├── email_models.py                   📧 E-mail
│       │   └── token_revogado_models.py          🚫 Blacklist JWT
│       │
│       ├── schemas/                              📋 Pydantic DTOs
│       ├── services/                             ⚙️ Regras de negócio
│       │   ├── usuario_service.py
│       │   ├── departamento_service.py
│       │   ├── canal_service.py
│       │   ├── atendimento_service.py
│       │   ├── roteiro_service.py
│       │   ├── bot_service.py
│       │   ├── ia_service.py
│       │   ├── whatsapp_service.py
│       │   └── audio_service.py
│       │
│       └── routers/                              🛣️ Endpoints HTTP
│           ├── auth.py
│           ├── usuarios.py
│           ├── departamentos.py
│           ├── canais.py
│           ├── atendimento.py
│           ├── webhook.py
│           ├── ia.py
│           ├── mensagens.py
│           ├── roteiros.py
│           └── audio.py
│
├── docs/                                         📚 Documentação (atualizada hoje)
│   ├── arquitetura.md
│   ├── guia-configuracao.md
│   └── modelos-de-negocio.md
│
├── scripts/                                      🛠️ Scripts (atualizado hoje)
│   └── arvore.md
│
└── painel-analitico/                             📊 Painel analítico
    └── dashboard.html
