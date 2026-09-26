<%! import datetime %>
"""${message}

Gerado por Alembic em ${datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")} UTC. NAO edite a logica deste arquivo depois de
aplicado: o Alembic guarda o hash da revision no banco e um arquivo editado
na mao quebra a cadeia.

Documentacao da revision
------------------------
Escreva AQUI o por que, nao o que. O "o que" ja esta no codigo gerado
("create table X", "add column Y"); o que o codigo nao conta e a decisao.

Checklist antes de commitar:
  [ ] O que o --autogenerate gerou e o que voce esperava? Confira com
      `alembic upgrade head --sql` e LEIA o SQL.
  [ ] Altera coluna NOT NULL? Precisa de backfill antes do NOT NULL, ou
      o banco recusa linhas antigas.
  [ ] Renomeou coluna? O Alembic gera DROP+ADD e PERDE OS DADOS. Troque
      por `op.alter_column(..., new_column_name=...)`, que vira RENAME.
  [ ] Criou coluna NOT NULL sem DEFAULT em tabela com dados? Vai falhar.
  [ ] O downgrade desfaz tudo que o upgrade fez, na ordem inversa?
  [ ] Rodou em mais de um banco (dev/homolog/prod) na mesma ordem?
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision = ${repr(up_revision)}
down_revision = ${repr(down_revision)}
branch_labels = ${repr(branch_labels)}
depends_on = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
