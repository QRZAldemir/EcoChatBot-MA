# Análise Final — Pendências do Projeto EcoChatBot-MA

**Data:** 21/08/2026 (21082026)
**Autor:** Verdent (assistente de desenvolvimento)
**Objetivo:** Registrar o ponto atual do projeto e as pendências para retomada no próximo dia.

---

## 1. Contexto do documento

Este arquivo serve como **ponto de retomada**. Ele cruza o que o `README.md` documenta
com o **estado real do código-fonte**, separando o que já está implementado do que ainda
precisa ser feito. Use como guia para continuar o trabalho sem perder a lógica e as etapas.

---

## 2. O que JÁ está implementado (confirmado no código)

### Backend (FastAPI)
- **API estruturada** — `backend/app/main.py`, `backend/app/routers/` (auth, usuarios,
  departamentos, canais, atendimentos, mensagens, conexoes, tenant, etc.).
- **Modelos, schemas e serviços** — `app/models/`, `app/schemas/`, `app/services/`
  (usuario_service, canal_service, atendimento_service, email_service, conexao_service...).
- **Bot WhatsApp / Evolution API** — `app/services/bot_handlers/` com `bot_machine.py`,
  `evolution_client.py`, `atendimento.py`, `agendamento.py`, `pedidos_handler.py`,
  `handler_factory.py`. O fluxo menu → roteiro → atendente já existe.
- **Migrations SQL** — `backend/migrations/` com 6 scripts:
  - `001_rename_canal_to_tipo_canal.sql`
  - `002_backfill_departamento_e_status_fila.sql`
  - `003_create_modelos_mensagem.sql`
  - `004_create_conexoes.sql`
  - `005_create_contatos_email_campanhas_arquivos.sql`
  - `006_create_tokens_revogados.sql`
- **Segurança JWT** — `app/security.py` (criar_token, obter_usuario_atual, tokens revogados).
- **Camada de repositórios** — `app/repositories/tenant_repository.py` (UsuarioRepository
  com isolamento por `cliente_id`).
- **Multi-tenant (base iniciada)** — `app/routers/tenant/` (atendimentos.py, usuarios.py),
  `app/dependencies.py`, model `Cliente`, `TenantService`, `cliente_id` em `Usuario`.

### Frontend (Angular 17)
- Painel admin com sidebar: dashboard, usuários, contatos, departamentos, canais,
  atendimentos, mensagens, email, conexões, campanhas, arquivos, níveis, escalas, relatório.
- Chat: hub-menu + atendimento por canal.
- Login, `auth.guard.ts`, `auth.interceptor.ts`, services e models.

### Módulos de negócio
- **Contatos**, **E-mail**, **Campanhas**, **Arquivos**, **Conexões** — backend + frontend
  + migrations 004/005 (já implementados, apesar de o README não os detalhar).

---

## 3. PENDÊNCIAS — o que ainda precisa ser implementado

### 3.1. Infraestrutura / Ambiente (README seção 4 — "Pendente")
| # | Pendência | Detalhe | Prioridade |
|---|---|---|---|
| 1 | **PostgreSQL em produção** | Instalar/configurar o banco real e rodar as migrations. Hoje roda em SQLite para dev. | Alta |
| 2 | **WhatsApp com credenciais reais** | Código pronto (`evolution_client.py`, webhook); falta preencher `.env` com credenciais da Meta ou Evolution API. | Alta |
| 3 | **IA com chave real** | `ia_service.py`/`deepseek.service.ts` prontos; falta `IA_API_KEY`/modelo no `.env`. | Média |

### 3.2. Multi-Tenant — completar a evolução (README seção 11)
| # | Pendência | Detalhe | Prioridade |
|---|---|---|---|
| 4 | **Migração do banco p/ tenant** | Criar fisicamente a tabela `clientes` e a coluna `usuarios.cliente_id`/`status` no banco real (sem migrations criadas para isso ainda). | Alta |
| 5 | **Isolar todos os routers por tenant** | Hoje só `tenant/atendimentos.py` e `tenant/usuarios.py` usam `get_current_cliente`. Avaliar os demais (departamentos, canais, contatos, campanhas, arquivos, email). | Média |
| 6 | **Onboarding / construtor de cliente** | Tela/fluxo para criar e configurar novos clientes (tenants). | Média |

### 3.3. Novas funcionalidades (README seção 11 — "Próximas Etapas")
| # | Pendência | Detalhe | Prioridade |
|---|---|---|---|
| 7 | **Construtor Visual de Roteiros** | Criar fluxos de atendimento sem editar HTML. | Média |
| 8 | **Integrações prontas** | Pagamento, agendas, ERPs, e-commerce. | Baixa |
| 9 | **IA autônoma / autoaprendizado** | IA que aprende com o histórico e responde autonomamente. | Baixa |

### 3.4. Correções / melhorias identificadas em análises anteriores
| # | Pendência | Detalhe | Prioridade |
|---|---|---|---|
| 10 | **Erros de sintaxe em `bot_handlers/`** | `agendamento.py:204` (await fora de async), `atendimento.py:840` (parêntese não fechado), `pedidos_handler.py:784` (bloco except incompleto). | Alta |
| 11 | **Rotas duplicadas no frontend** | `app.routes.ts` tem `atendimentos` e `mensagens` duplicadas (títulos "Marcx"/"Mackenzie"). Limpar. | Baixa |
| 12 | **Política de senha forte** | Schemas agora exigem senha ≥ 8 com maiúscula/número/especial. Alinhar telas de cadastro/reset e seed. | Média |
| 13 | **README desatualizado** | Seção 5 (estrutura) e estado atual não refletem módulos novos, tenant e repositórios. Atualizar. | Baixa |

---

## 4. Pontos de atenção / riscos
- **Dependência de ambiente**: o import completo de `app.main` exige `gtts` (não instalado
  no ambiente) — não relacionado às mudanças, mas bloqueia o boot completo.
- **Migrations pendentes de tenant**: sem a migração do banco, as colunas novas
  (`clientes`, `cliente_id`, `status`) não existem fisicamente em produção.
- **Mudança de comportamento**: a nova política de senha forte pode quebrar telas/seed que
  usam senhas simples — alinhar antes de liberar.

---

## 5. Próximos passos sugeridos (amanhã)
1. **Prioridade alta**: corrigir os 3 erros de sintaxe em `bot_handlers/` (item 10).
2. **Prioridade alta**: criar a migration de tenant (tabela `clientes` + colunas) (item 4).
3. **Prioridade média**: alinhar frontend/seed à política de senha forte (item 12).
4. **Prioridade baixa**: atualizar README (item 13) e limpar rotas duplicadas (item 11).

---

*Arquivo gerado para retomada do trabalho no próximo dia.*
