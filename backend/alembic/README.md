# Camada Alembic — controle de versão do schema

## O que é isto

O Postgres não guarda o que a aplicação *quer* que o banco seja; guarda o que
*é*. Os models (`app/models/`) dizem a forma desejada. O Alembic é a
ferramenta que leva uma até a outra de forma rastreável.

Sem esta camada, o schema muda por dois caminhos ruins:

| Caminho | O que faz | Por que quebra |
|---|---|---|
| `Base.metadata.create_all` | cria tabela que falta | **nunca altera nem remove** tabela existente. A app sobe sem erro e o banco diverge em silêncio dos models. |
| SQL manual, arquivo a arquivo | funciona | não existe registro do que já foi aplicado. Rodar 2× reaplica, rodar fora de ordem corrompe. |

O Alembic resolve os dois: guarda o estado numa tabela `alembic_version` e
aplica só o que falta.

## Estrutura

```
alembic.ini                  config (URL fica VAZIA de propósito: vem do .env)
alembic/env.py               liga o Alembic na app: URL, metadata, modo async
alembic/script.py.mako       template das revisions futuras
alembic/versions/            as revisions, uma por arquivo
└── *_baseline_*.py          revision inicial (vazia, serve de âncora)
```

## Por que `env.py` é assíncrono

A aplicação é async-only (`create_async_engine` em `app/database.py`); não
existe engine síncrona. Um `env.py` síncrono padrão falharia, ou pior,
conectaria com um driver diferente do que a app usa em produção — e a
migration seria validada contra um banco que a aplicação nunca enxerga. A
ponte é `connection.run_sync`, que entrega a conexão no Greenlet.

## Fluxo normal

```bash
# 1. mudanca nos models
vim app/models/xxx_models.py

# 2. ver o que o Alembic entende da mudanca
alembic revision --autogenerate -m "add x em y"
vim alembic/versions/aaa_bbb_add_x_em_y.py   # LEIA o downgrade

# 3. revisar o SQL sem tocar no banco
alembic upgrade head --sql > revisar.sql
cat revisar.sql

# 4. aplicar
alembic upgrade head

# 5. conferir
alembic current
```

Desfazer: `alembic downgrade -1`.

## Banco já existente (o caso deste projeto)

O banco atual **não** foi criado pelo Alembic — veio de `Base.metadata.create_all`
e de `migrations/*.sql`. Para adotar a camada sem reescrever o histórico:

```bash
alembic stamp head     # marca como "já está na baseline", sem aplicar nada
alembic current        # deve mostrar a revision baseline
alembic check          # deve dizer "no new upgrade operations detected"
```

Depois do `stamp`, o próximo `revision --autogenerate` gera **apenas** o
delta entre os models e o banco.

> Só faça `stamp head` depois de confirmar que o banco real já está no
> formato dos models. Se ainda houver diferença, o `stamp` mente para o
> Alembic e a próxima migration vai tentar criar o que já existe.

## Relação com `migrations/*.sql`

Os 14 arquivos em `backend/migrations/` são o mecanismo **anterior**, com
`run_migrations.py`. Eles têm dois problemas que os torna inadequados daqui
para frente:

- não guardam registro do que já rodou;
- `run_migrations.py` quebra o arquivo em `;`, o que **destrói** blocos
  `DO $$ ... $$` (e a migration 010 usa três).

Não misture os dois sistemas no mesmo banco — é assim que nasce drift. O
plano é: congelar os `.sql` como histórico (não mexer mais) e passar a usar
só o Alembic daqui para frente. Para isso, o `migrations/010_*.sql` precisa
virar uma revision do Alembic, ou ser aplicado à mão e então `stamped`.
