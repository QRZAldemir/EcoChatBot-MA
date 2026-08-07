# Skill — Autenticação

## Como funciona hoje

**Backend** (`backend/app/security.py` + `routers/auth.py`): login por
e-mail/senha (bcrypt), emissão de JWT assinado (`SECRET_KEY`/`JWT_ALGORITHM`/
`JWT_EXPIRE_MINUTES` no `.env`). O token carrega um `jti` (id único) além do
`sub` (id do usuário) — é o que permite revogar um token específico no
logout sem precisar de uma blocklist por usuário.

Rotas:

| Rota                | Método | Requer token? | O que faz |
|----------------------|--------|:---:|-----------|
| `/api/auth/login`    | POST   | não | Autentica, devolve `access_token` + dados do usuário |
| `/api/auth/me`       | GET    | sim | Devolve o usuário do token atual (usado pra validar a sessão) |
| `/api/auth/refresh`  | POST   | sim | Emite um novo token a partir de um ainda válido, sem novo login |
| `/api/auth/logout`   | POST   | sim | Revoga o `jti` do token atual (grava em `tokens_revogados`) |

`obter_usuario_atual` (a dependency que protege rotas) valida, nessa ordem:
assinatura do JWT → expiração (`exp`, conferido automaticamente pela lib
`jose`) → se o `jti` não está em `tokens_revogados` (logout) → se o usuário
ainda existe e está `ativo`.

**Frontend**: `auth.service.ts` guarda `access_token` + usuário no
`localStorage`; `isAuthenticated()` decodifica o payload do JWT e checa o
`exp` (não só se existe um token); `auth.guard.ts` usa `isAuthenticated()`
para bloquear `/admin/*`; `auth.interceptor.ts` anexa `Authorization: Bearer`
em toda requisição e, se o backend responder 401 (token expirado/revogado/
inválido), limpa a sessão local e redireciona para `/login` — exceto no
próprio `/auth/login`, onde 401 é "senha errada" e deve aparecer no
formulário, não disparar um redirect.

## Lacunas corrigidas em 2026-08-07

Antes desta revisão, **nenhuma rota do backend verificava o JWT** — o
`auth.guard.ts` do Angular impedia a *navegação* para `/admin/*` sem token,
mas qualquer requisição feita diretamente à API (curl, Postman, um token
expirado) era aceita sem checagem alguma. Também não havia como invalidar
um token antes do vencimento natural (logout só limpava o `localStorage`).

Corrigido:
- `obter_usuario_atual` (nova dependency) — assinatura + expiração + revogação.
- `/auth/me`, `/auth/refresh`, `/auth/logout` (com revogação real via
  `tokens_revogados`, migration `006_create_tokens_revogados.sql`).
- `isAuthenticated()` no frontend agora decodifica o `exp`, não só confere
  se existe uma string no `localStorage`.
- Interceptor reage a 401 limpando a sessão e redirecionando — antes, um
  token expirado deixava a tela num estado quebrado sem explicação.

## Routers protegidos (exigem JWT) vs públicos

`main.py` decide por `ROUTERS_CONFIG` (`protegido: bool` na tupla de cada
router, aplicado via `include_router(..., dependencies=[...])`).

**Protegidos** — confirmado em código que só o painel `/admin/*` os chama,
nunca o widget de chat público (`pages/chat/*`) nem `bot_service.py` (que
mexe no banco direto via SQLAlchemy, não faz HTTP pra si mesmo):

`usuarios`, `departamentos`, `contatos`, `email` (módulo E-mail),
`campanhas`, `arquivos`, `conexoes`, `atendimento`.

**Deixados públicos (decisão consciente, não esquecimento)**:

- `canais`, `menus`, `modelos-mensagem` — o widget de chat anônimo
  (`hub-menu`/`atendimento` em `pages/chat/*`) faz `GET` neles sem login
  (paciente escolhendo canal/menu). Só a escrita (`POST`/`PUT`/`DELETE`,
  usada pelas telas admin de Canais/Mensagens) deveria exigir token — isso
  exige proteger rota a rota dentro de cada router, não o router inteiro.
  **Ainda não implementado** — é a lacuna mais concreta que sobrou.
- `ia`, `mensagem`, `audio`, `webhook` — motor do bot/WhatsApp. `webhook` é
  chamado pela Evolution API (protegido por `WEBHOOK_SECRET`, não por JWT
  — quem chama não é um browser logado). Os outros três não têm chamada
  confirmada vindo do Angular; manter protegido exigiria mapear todo
  caminho por onde a Evolution API ou o bot passam por eles antes de travar
  o acesso.

## Como adicionar proteção a uma rota nova

- **Router 100% admin** (nenhum uso por `pages/chat/*` ou `bot_service.py`):
  marcar `protegido=True` na tupla correspondente em `ROUTERS_CONFIG`
  (`main.py`) — protege todas as rotas do router de uma vez.
- **Router misto** (parte pública, parte admin): manter `protegido=False`
  na tupla e adicionar `Depends(obter_usuario_atual)` só nas rotas de
  escrita, dentro do próprio arquivo do router (import de
  `app.security.obter_usuario_atual`).
