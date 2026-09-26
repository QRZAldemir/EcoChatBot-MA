# AGENTS.md — EcoChatBot-MA

Diretrizes para agentes que trabalham neste repositorio. Leia antes de tocar em qualquer arquivo.

## Identidade do software

| Item | Valor |
| --- | --- |
| Nome do software | **EcoChatBot-MA** |
| Empresa de software | **AlMarcx** |
| Dono do software | **Aldemir Queiroz** — DevOps e CEO da AlMarcx |
| E-mail do dono | `queiroz@almarcx.com.br` |
| Dominio de e-mail | `@almarcx.com.br` |
| Codinome interno | `EcoChatBot-MA` |

Regras de grafia, sem excecao:

- O software se chama **EcoChatBot-MA**. As grafias `EcoChatBot-Marcx`, `EcoChatBotMarcx`,
  `EcoChatMackenize` e `EcoChatBot_MA` estao **erradas** e devem virar `EcoChatBot-MA`.
- A empresa se chama **AlMarcx**, com maiuscula no `M`. Em e-mail o dominio e minusculo por
  definicao: `queiroz@almarcx.com.br`.
- `MA` significa **Marcx**, da AlMarcx. Nunca expandir `MA` para Mackenzie.
- Grafia canonica **EcoChatBot-MA** com `MA` em maiusculas, confirmada pelo dono em
  2026-09-26. As formas `EcoChatBot-Ma`, `EcoChatBot_MA`, `EcoChatBot-Marcx` e
  `EcoChatBotMarcx` sao inválidas e nao devem ser reintroduzidas.
- **O produto e multi-tenant.** Serve qualquer empresa, de qualquer segmento, com qualquer
  modelo de negocio. Nao ha vinculo com hospital, clinica ou dominio especifico. A AlMarcx e
  apenas a operadora do software.
- Seed de demonstracao nao pode usar dominio real de terceiro como `hospitalmackenzie.com.br`.
  Use `@exemplo.com`, `@teste.com` ou `@almarcx.com.br`.

## Papel do agente

O usuario e o dono do software (DevOps/CEO). Ele decide produto, escopo e nome.

- Nao decidir regra de negocio por conta propria. Em ambiguidade de dominio, perguntar antes.
- Nao inferir segmento de negocio a partir do historico do repositorio.
- Nao apagar, renomear em massa nem migrar dado sem aprovacao explicita.
- Nao executar migration, commit ou push sem pedido explicito.

## Ambiente

- Servidor de desenvolvimento: `ssh -o BatchMode=yes lxc200`
- Raiz do projeto: `/mnt/sdc2/home/querioz/EcoChatBot-MA`
- Python sem venv no projeto. `pydantic-settings` esta em `backend/requirements.txt` e ausente
  do ambiente.
- Banco de desenvolvimento: SQLite em `backend/ecochat_dev.db`. Esse arquivo **esta versionado
  no repositorio publico** e contem `senha_hash` de usuarios. Nao inserir credencial real nele.

## Convecao de comentario de arquivo

### Models (`backend/app/models/*_models.py`)

Metadados obrigatorios no topo, mais as secoes abaixo:

```
@file  @module  @author  @since  @version
```

Seccoes na ordem: `FUNCIONALIDADE`, `EXEMPLO PRATICO` (opcional), `RELACIONAMENTO`,
`REGRAS DE NEGOCIO`.

```
RELACIONAMENTO
──────────────
    Empresa (1) ── (N) Telefone ── (N) CanalContratado
```

### Schemas (`backend/app/schemas/*.py`)

Docstring unica com bloco de metadados:

```
================================================================================
MODULO: app/schemas/nome_schemas.py
AUTOR: Aldemir Queiroz
DATA: AAAA-MM-DD
VERSAO: 0.0.0
OBJETIVO: O que este modulo valida e serializa.
PASTA: backend/app/schemas/
================================================================================
```

### Estilo

- A docstring e unica. Ao inserir cabecalho, nao fechar as aspas no fim do bloco de metadados:
  a secao seguinte continua dentro da mesma docstring.
- Titulos, codinome e nomes de classe usam `EcoChatBot-MA`.
- Sem emoji em cabecalho, codigo ou saida de terminal.
- Idioma: portugues.

## Migrations

- Nao ha Alembic em uso. `alembic/versions/` esta vazio e nao existe tabela `alembic_version`.
- Convecao real: SQL manual em `backend/migrations/NNN_descricao.sql`, executado por
  `backend/migrations/run_migrations.py`.
- Dialetos divergem: `007` usa sintaxe MySQL, `008` usa `GENERATED ... AS IDENTITY` do
  PostgreSQL, o dev DB e SQLite. Escrever migration portavel e validar em `sqlite3 :memory:`.
- Criar a migration nao e o mesmo que aplica-la. Nunca aplicar sem pedido explicito.

## Verificacao

Antes de considerar uma alteracao pronta:

- `ast.parse` em **todo** arquivo tocado. Checar padrao de cabecalho nao substitui isso: um
  cabecalho inserido com aspas fechadas cedo demais gera arquivo invalido e passa na checagem
  de padrao.
- `configure_mappers()` so passa com o conjunto moderno de models. Ha duplicacao legada de
  `Usuario` em `usuario_models.py`, `models.py` e `models/__init__.py`, e dois `Base`
  (`app.database.Base` e `app.models.base.Base`).
