# Skill — Barra de Menu (Sidebar)

## Referência visual

`docs/Barra Menu.png` é a fonte da verdade para ícone, ordem e estilo da
sidebar. Qualquer alteração no menu deve ser comparada com essa imagem antes
de ser considerada concluída.

A imagem mostra uma sidebar **só com ícones** (sem seções, sem títulos de
grupo), tema claro, nesta ordem:

1. Início (casa)
2. Usuários (pessoa)
3. Contatos (cartão de identificação)
4. Setor / Departamento (prédio)
5. Chat (balão de conversa)
6. E-mail (envelope)
7. Histórico (seta circular)
8. Conexões (wifi)
9. Sinal (barras)
10. Calendário
11. Campanhas (avião de papel)
12. Arquivos (pasta)

## Implementação atual

Componente: `frontend/src/app/shared/components/layout/layout.component.ts`
(`.html` / `.css` no mesmo diretório).

- A sidebar é uma lista **plana** de `navItens` (sem agrupamento por seção —
  isso foi removido para bater com a referência).
- Tema: fundo branco (`--sb: #ffffff`), destaque azul no item ativo
  (`--blue: #5c8ad6`), borda sutil (`--border: #e5ddd8`) em vez do antigo
  tema escuro/vermelho.
- Cada item é `{ rota, icone, label }`; `icone` é uma classe Font Awesome
  (`fa-*`).

### Regra de inclusão

**Um item só entra no menu quando a página correspondente existe de fato.**
Itens presentes na imagem mas sem rota implementada ainda ficam de fora —
não adicionar ícone "morto" sem destino.

Estado atual de `navItens` — todos os itens da imagem com página própria já
foram implementados (2026-08-07):

| Ordem | Label     | Ícone            | Rota                  |
|-------|-----------|------------------|------------------------|
| 1     | Início    | fa-house         | /admin/dashboard       |
| 2     | Usuários  | fa-users         | /admin/usuarios        |
| 3     | Contatos  | fa-address-card  | /admin/contatos        |
| 4     | Setor     | fa-building      | /admin/departamentos   |
| 5     | Chat      | fa-comments      | /admin/atendimentos    |
| 6     | Mensagens | fa-comment-dots  | /admin/mensagens       |
| 7     | E-mail    | fa-envelope      | /admin/email           |
| 8     | Conexões  | fa-wifi          | /admin/conexoes        |
| 9     | Campanhas | fa-paper-plane   | /admin/campanhas       |
| 10    | Arquivos  | fa-folder        | /admin/arquivos        |

Escopo de cada módulo novo (CRUD completo, backend + frontend):

- **Contatos** — agenda de clientes WhatsApp (`contatos` table); base de
  destinatários para Campanhas.
- **E-mail** — central de envio avulso com histórico (`emails_enviados`
  table); usa SMTP se configurado (`SMTP_HOST` etc. no `.env`), senão
  registra como "simulado" (mesmo padrão de resiliência do
  `evolution_service`).
- **Campanhas** — disparo em massa via WhatsApp (`campanhas` +
  `campanha_contatos` tables), reaproveitando uma Conexão existente e o
  `evolution_service`.
- **Arquivos** — biblioteca de mídia do chat (`arquivos` table); upload
  grava em disco (`backend/uploads/arquivos/`, fora do Git) e metadados no
  banco.

`Histórico`, `Sinal` e `Calendário` aparecem na imagem mas seu significado
exato no produto ainda não foi definido (podem ser sub-ações de Conexões, e
não itens de topo — revisar com a imagem antes de criar página para eles).
Esses três continuam de fora do menu.

## Como adicionar um item novo

1. Criar a página (component standalone) em `frontend/src/app/pages/admin/<nome>/`.
2. Registrar a rota em `frontend/src/app/app.routes.ts` (lazy-load,
   seguindo o padrão dos itens existentes).
3. Adicionar `{ rota, icone, label }` em `navItens`
   (`layout.component.ts`), na posição correspondente à ordem da imagem
   de referência.
4. Conferir visualmente contra `docs/Barra Menu.png` (ordem, ícone, cor do
   item ativo).

## Histórico

- O menu era agrupado em seções ("Visão Geral", "Atendimento",
  "Configuração", "Gestão") com tema escuro/vermelho. Foi substituído pela
  lista plana de ícones em tema claro/azul para seguir `Barra Menu.png`.
- Módulo **Conexões** foi adicionado primeiro (frontend + backend
  completos: `conexoes.component.*`, `conexao.service.ts`,
  `routers/conexoes.py`, `services/conexao_service.py`,
  `migrations/004_create_conexoes.sql`).
- **Contatos, E-mail, Campanhas e Arquivos** foram implementados em
  seguida (migration `005_create_contatos_email_campanhas_arquivos.sql`),
  fechando a lista de itens do menu que tinham página própria pendente —
  ver tabela acima.
