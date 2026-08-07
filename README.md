# EcoChatBot Marcx
### Protótipo — Hospital Presbiteriano Marcx · Dourados/MS

---

## O que é o EcoChatBot

O **EcoChatBot** é um sistema de atendimento digital configurável, desenvolvido inicialmente como protótipo para o **Hospital Presbiteriano Marcx**.

A ideia central é simples: o paciente/cliente interage via **WhatsApp clicando em botões** — nunca digitando — e é automaticamente direcionado para o atendente certo conforme o canal escolhido. O atendente vê a conversa no painel **EcoChat** com todo o contexto já coletado.

O sistema foi projetado para ser **configurável e reutilizável** em outros modelos de negócio no futuro.

---

## Conceito Principal

```
PACIENTE (WhatsApp)
    │
    │  recebe botões de menu
    │  ex: 📞 Atendimento | 📅 Agendamento | 🚪 Portaria
    │
    │  CLICA em uma opção
    ▼
WhatsApp Business API
    │
    │  dispara webhook
    ▼
EcoChatBot Backend (Python FastAPI)
    │
    │  identifica o Canal pelo botão clicado
    │  ex: "Portaria" → canal vinculado ao arquivo 7portaria-marcx.html
    │
    │  busca atendente disponível daquele canal
    │  ex: João → Departamento: Recepção → Canal: Portaria
    ▼
EcoChat Painel (Angular)
    │
    │  abre atendimento para João
    │  exibe o fluxo do canal (perguntas/respostas do HTML)
    ▼
ATENDENTE responde
```

---

## Exemplos de Usuários Cadastrados

| Usuário   | Nível     | Departamento | Canal                    | Arquivo de Menu                       |
|-----------|-----------|--------------|--------------------------|---------------------------------------|
| Aldemir   | Atendente | Call-Center  | Exames-Diagnostico       | `3examesdiagnostico-marcx.html`   |
| Ana       | Atendente | Call-Center  | Atendimento-Cliente      | `1atendimento-marcx.html`         |
| João      | Atendente | Recepção     | Portaria                 | `7portaria-marcx.html`            |
| Francisca | Atendente | Ouvidoria    | Ouvidoria                | `8ouvidoria-marcx.html`           |
| Daniele   | Atendente | Call-Center  | Agendamento-Ambulatorial | `2agendamento-marcx.html`         |

**Regra:** Um usuário pertence a um **Departamento** e atende um **Canal**. O canal define qual fluxo de perguntas/respostas o paciente verá.

---

## Estado Atual — Protótipo

Este projeto está em fase de **protótipo visual e estrutural**. Os arquivos HTML representam como cada canal de atendimento será apresentado ao paciente. O código Angular e Python FastAPI está estruturado e pronto para ser executado quando o ambiente for instalado.

### O que já existe

| Camada     | Status      | Descrição                                              |
|------------|-------------|--------------------------------------------------------|
| Protótipos | ✅ Completo | HTMLs funcionais de todos os canais                   |
| Angular    | ✅ Estruturado | Componentes, rotas, modelos e serviços criados       |
| FastAPI    | ✅ Estruturado | API REST completa com SQLAlchemy, DeepSeek integrado |
| Banco      | ⏳ Pendente | PostgreSQL — aguarda instalação do ambiente           |
| WhatsApp   | ⏳ Pendente | Aguarda conta Meta Business verificada               |
| DeepSeek   | ⏳ Pendente | Aguarda chave de API configurada                      |

---

## Estrutura de Arquivos

```
EcoChatMackenize/
│
├── prototipos/                         ← HTMLs originais (referência visual)
│   ├── hub_Menu.html                   Menu principal apresentado ao paciente
│   ├── 1atendimento-marcx.html     Canal: Atendimento ao Cliente
│   ├── 2agendamento-marcx.html     Canal: Agendamento Ambulatorial
│   ├── 3examesdiagnostico-marcx.html Canal: Exames e Diagnósticos
│   ├── 7portaria-marcx.html        Canal: Portaria e Recepção
│   ├── 8ouvidoria-marcx.html       Canal: Ouvidoria
│   ├── EcoChatMarcxVs.html         Painel do atendente (protótipo completo)
│   ├── dashboard_eco.html              Dashboard de análise
│   ├── cadastro-usuarios.html          Tela de cadastro (protótipo)
│   └── Painel_Escalas_Marcx.html   Gestão de escalas médicas
│
├── frontend/                           ← Angular 17 (interface web)
│   └── src/
│       ├── main.ts                     Ponto de entrada da aplicação
│       ├── index.html                  HTML raiz
│       └── app/
│           ├── app.component.ts        Componente raiz
│           ├── app.routes.ts           Rotas da aplicação
│           ├── core/
│           │   ├── models/             Interfaces TypeScript
│           │   │   ├── usuario.model.ts
│           │   │   ├── departamento.model.ts
│           │   │   ├── canal.model.ts          ← canal tem arquivoMenu (= questionário)
│           │   │   └── nivel-usuario.model.ts
│           │   └── services/           Comunicação com a API backend
│           │       ├── usuario.service.ts
│           │       ├── departamento.service.ts
│           │       ├── canal.service.ts
│           │       └── deepseek.service.ts
│           ├── pages/
│           │   ├── admin/              Área administrativa
│           │   │   ├── dashboard/      Tela inicial com atalhos
│           │   │   ├── usuarios/       CRUD de usuários (agrupado por departamento)
│           │   │   ├── departamentos/  CRUD de departamentos
│           │   │   ├── canais/         CRUD de canais + vínculo com arquivo HTML
│           │   │   ├── niveis/         Níveis de acesso e permissões
│           │   │   ├── escalas/        Painel de escalas (carrega HTML em iframe)
│           │   │   └── relatorio/      Relatórios de atendimento
│           │   └── chat/               Área do cliente/paciente
│           │       ├── hub-menu/       Menu de opções (paciente CLICA, não digita)
│           │       └── atendimento/    Carrega o HTML do canal em iframe
│           └── shared/
│               └── components/layout/ Sidebar + topbar do painel admin
│
├── backend/                             ← Python 3.12 + FastAPI
│   ├── requirements.txt                 Dependências Python
│   ├── .env                             Variáveis de ambiente
│   ├── init_db.py / seed_data.py        Inicialização e dados de seed do banco
│   ├── run_migrations.py                Executor das migrações SQL
│   ├── export_openapi.py                Exporta o schema OpenAPI (usado pelo codegen do Angular)
│   ├── migrations/                      Migrações SQL versionadas
│   └── app/
│       ├── main.py                      Ponto de entrada da API FastAPI (docs em /docs e /redoc)
│       ├── database.py                  Configuração SQLAlchemy
│       ├── models/                      Modelos ORM (entities.py)
│       ├── schemas/                     Schemas Pydantic (validação e DTOs)
│       ├── services/                    Regras de negócio
│       │   ├── usuario_service.py, departamento_service.py, canal_service.py
│       │   ├── atendimento_service.py, menu_service.py, modelo_mensagem_service.py
│       │   ├── bot_service.py           Lógica do fluxo conversacional do bot
│       │   ├── deepseek_service.py      Integração com IA DeepSeek
│       │   ├── evolution_service.py     Integração com WhatsApp (Evolution API)
│       │   └── audio_service.py         Texto → fala (gTTS)
│       └── routers/                     Endpoints REST (um por domínio)
│           ├── auth.py, usuarios.py, departamentos.py, canais.py
│           ├── ia.py, mensagem.py, menus.py, modelos_mensagem.py
│           └── atendimento.py, webhook.py, audio.py

└── docs/
    └── arquitetura.md                  Documentação técnica detalhada
```

---

## Canais de Atendimento

Cada canal é uma entidade cadastrada no sistema que aponta para um arquivo HTML de menu:

| Canal                    | Arquivo HTML                          | Fluxo Principal                                      |
|--------------------------|---------------------------------------|------------------------------------------------------|
| Atendimento-Cliente      | `1atendimento-marcx.html`         | Guia de pacientes, 2ª via de documentos, contato    |
| Agendamento-Ambulatorial | `2agendamento-marcx.html`         | Marcar, confirmar, remarcar, cancelar consultas     |
| Exames-Diagnostico       | `3examesdiagnostico-marcx.html`   | Agendar exames, resultados, orçamentos, preparo     |
| Portaria                 | `7portaria-marcx.html`            | Visitas, estacionamento, achados/perdidos, PS       |
| Ouvidoria                | `8ouvidoria-marcx.html`           | Reclamação, elogio, sugestão, denúncia, prontuário |

O **nome do canal** determina qual botão aparece no WhatsApp para o paciente.
O **arquivo HTML** define o roteiro completo de perguntas e respostas daquele canal.

---

## Fluxo de Desenvolvimento — Próximas Etapas

```
ETAPA 1 — Ambiente (quando decidir rodar)
  │  sudo apt install python3 python3-pip python3-venv nodejs npm postgresql
  │  pip3 install virtualenv

ETAPA 2 — Banco de dados
  │  createdb ecochat_marcx
  │  cd backend && python3 -m venv venv
  │  source venv/bin/activate  # Linux/Mac
  │  pip install -r requirements.txt
  │  cp .env.example .env  # Configurar variáveis
  │  python3 init_db.py  # Inicializa banco com dados seed

ETAPA 3 — Backend FastAPI
  │  cd backend
  │  uvicorn app.main:app --reload --port 8000
  │  Acesso API: http://localhost:8000
  │  Docs Swagger: http://localhost:8000/docs

ETAPA 4 — Frontend Angular
  │  cd frontend && npm install
  │  npm run generate:api   # gera o cliente TS a partir do OpenAPI do backend
  │  ng serve
  │  Acesso: http://localhost:4200

ETAPA 5 — WhatsApp Business API
  │  Criar conta em developers.facebook.com
  │  Configurar webhook: https://seu-servidor/api/whatsapp/webhook
  │  Definir WHATSAPP_PHONE_ID, WHATSAPP_TOKEN, WHATSAPP_VERIFY_TOKEN no .env

ETAPA 6 — DeepSeek IA
  │  Obter chave em platform.deepseek.com
  │  Configurar DEEPSEEK_API_KEY no arquivo .env

ETAPA 7 — Futuro (multi-negócio)
     Tornar o sistema multi-tenant (cada cliente tem seus canais/departamentos)
     Integração com Chatwoot (webhook bidirecional)
     Builder visual de questionários por canal
```

---

## Tecnologias Utilizadas

| Camada     | Tecnologia            | Versão   | Motivo                                      |
|------------|-----------------------|----------|---------------------------------------------|
| Frontend   | Angular               | 17       | Componentes standalone, lazy loading        |
| Linguagem  | TypeScript            | 5.4      | Tipagem forte nos modelos                   |
| Estilo     | CSS puro + DM Sans    | —        | Mesmo padrão visual dos protótipos HTML     |
| Backend    | **FastAPI**           | 0.109+   | **Alta performance, async, Python moderno** |
| Linguagem  | **Python**            | 3.10+    | **Fácil manutenção, ecossistema rico**      |
| ORM        | **SQLAlchemy**        | 2.0+     | **ORM poderoso e flexível**                 |
| Validação  | **Pydantic**          | 2.5+     | **Validação automática de dados**           |
| Servidor   | **Uvicorn**           | 0.27+    | **ASGI server rápido**                      |
| Banco      | PostgreSQL            | 15+      | Relacional, confiável, LGPD-friendly        |
| IA         | DeepSeek Chat API     | —        | Custo menor que GPT, boa qualidade em PT-BR |
| Mensageria | WhatsApp Business API | v19.0    | Canal já usado pelos pacientes              |

---

## Variáveis de Ambiente Necessárias

Crie um arquivo `.env` na pasta `backend/` com as seguintes variáveis:

```bash
# Database
DATABASE_URL=postgresql://ecochat:ecochat123@localhost:5432/ecochat_marcx

# DeepSeek AI
DEEPSEEK_API_KEY=sk-sua-chave-aqui
DEEPSEEK_MODEL=deepseek-chat

# WhatsApp Business API (configurar quando integrar)
WHATSAPP_PHONE_ID=seu_phone_id
WHATSAPP_TOKEN=seu_token_whatsapp
WHATSAPP_VERIFY_TOKEN=seu_verify_token

# JWT (para autenticação futura)
SECRET_KEY=sua-chave-secreta-mude-em-producao
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

Ou copie o exemplo:
```bash
cd backend
cp .env.example .env
# Edite o arquivo .env com suas configurações
```

---

## Sobre o Projeto

- **Cliente:** Hospital Presbiteriano Marcx — Dourados/MS
- **Propósito atual:** Protótipo funcional para demonstração
- **Visão futura:** Ecossistema de chat configurável para qualquer modelo de negócio
- **Diferenciais:** Paciente clica nos botões (não digita), atendente recebe contexto completo, IA responde automaticamente quando necessário

---

## Dashboard Analítico — `dashboard_eco.html`

O dashboard importa planilhas exportadas do **EcoChat/ZigChat** e gera análises visuais interativas, além de um **Relatório Analítico** em HTML pronto para impressão ou envio.

### Planilhas suportadas

| Arquivo | Conteúdo |
|---|---|
| `REL_ATENDIMENTO.xlsx` | Histórico completo de atendimentos (Protocolo, Criação, Finalização, Atendente/Usuário, etc.) |
| `RELATORIO_CAPTACAO.xlsx` | Avaliações NPS dos clientes (Nota, Departamento, Data) |
| `Auditoria.xlsx` | Log de ações dos usuários no sistema |

### Regras de Negócio — Campo `Finalização`

O campo `Finalização` da planilha `REL_ATENDIMENTO` possui dois estados:

| Valor no campo | Significado |
|---|---|
| `"Não finalizado"` | Atendimento **aberto** (em andamento) |
| Data (ex: `21/04/2026 14:32`) | Atendimento **finalizado** com sucesso |

### Lógica dos Cards de Status

| Card | Regra de cálculo |
|---|---|
| **Total** | Todos os registros no período/filtro selecionado |
| **Aguardando Atendimento** | `Finalização = "Não finalizado"` **e** `Atendente/Usuário` **vazio** — nenhum atendente designado ainda |
| **Em Atendimento** | `Finalização = "Não finalizado"` **e** `Atendente/Usuário` **preenchido** — atendente designado, mas cliente aguarda (atendente pode estar ocupado com outro) |
| **Finalizados** | `Finalização` contém uma data válida |

> **Regra**: `Total = Aguardando Atendimento + Em Atendimento + Finalizados`

### Expediente de Atendimento

- **Horário:** 07:00 às 18:00
- **Dias:** Segunda a Domingo (todos os dias)

### Alertas de Operação Identificados

O dashboard detecta automaticamente 4 situações de alerta:

| Alerta | Critério de detecção |
|---|---|
| 🌙 **Fora do Expediente** | `hora(Criação) < 7` ou `hora(Criação) >= 18` — bot pode não rotear fora do horário |
| 🤖 **Sem Roteamento do Bot** | Aberto + sem atendente + sem departamento — cliente provavelmente só disse "oi" e o bot não identificou a intenção |
| ⏳ **Abertos há +24h** | `Finalização = "Não finalizado"` e criado há mais de 24 horas |
| 📋 **Sem Departamento** | Campo `Atendente/Usuário` vazio — ticket sem destino definido |

### Por que o bot não entrega alguns atendimentos?

**Causa 1 — Fora do expediente**
Tickets criados antes das 07h ou após as 18h. O fluxo do bot não está configurado para esse horário e o ticket fica aberto sem roteamento.

**Causa 2 — Interação mínima (cliente só diz "oi")**
O bot não consegue identificar a intenção do cliente e não roteia para nenhum departamento. Esses tickets ficam com `Atendente/Usuário` vazio e sem departamento, acumulando na fila sem resolução.

### Relatório Analítico Gerado

Ao clicar em **"Gerar Relatório Analítico"**, o sistema:

1. Abre um **modal de filtros** com prévia comparativa (Dia Atual × Dia Anterior)
2. Detecta automaticamente o período com dados e pré-preenche as datas
3. Gera sugestões de análise com base na variação dos indicadores
4. Exporta um arquivo `.html` com:
   - Tabela de atendimentos por departamento com taxa de finalização colorida (🟢 ≥70% / 🟡 ≥40% / 🔴 <40%)
   - Blocos de alertas operacionais
   - Análise de avaliações NPS (se importado)
   - Registros de auditoria (se importado)
   - Dados de telefonia/bilhetagem (se importado)

### Filtros de Data — Formato Brasileiro

Todos os campos de data do dashboard utilizam o formato **DD/MM/AAAA** com máscara automática ao digitar.
