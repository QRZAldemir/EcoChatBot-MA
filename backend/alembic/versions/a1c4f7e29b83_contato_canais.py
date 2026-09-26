"""contato_canais: identidade por canal sai de Contato para tabela propria

Por que
------
`Contato` carregava `canal_tipo` + `canal_identificador` NOT NULL, com UNIQUE
(empresa_id, canal_tipo, canal_identificador). Isso contradizia o doctodo da
propria classe ("um mesmo Contato pode existir em varios canais") de duas
formas:

  1. O UNIQUE nao permitia a MESMA pessoa em dois canais — o segundo insert
     batia na constraint.
  2. Os campos NOT NULL impediam um contato sem canal (lead de campanha, lead
     cadastrado a mao so com telefone) de existir.

Pior: nao dava para dizer DE QUE CANAL era o identificador, porque a tabela
nao guardava `canal_contratado_id`. Num tenant com dois WhatsApp, "5511..." era
ambiguo. Evolution resolve com `@@unique([remoteJid, instanceId])` em
`Contact`; Chatwoot resolve com o join `contact_inboxes`. Aqui a identidade por
canal vai para `contato_canais`, com `@@unique([canal_contratado_id,
identificador])`.

O QUE ESTA MIGRATION NAO CONSEGUE FAZER
---------------------------------------
NAO existe backfill possivel de `contatos` -> `contato_canais`: a tabela antiga
nao guardava `canal_contratado_id`, entao nao ha como saber a qual canal
contratado cada linha pertencia. Inventar um `canal_contratado_id` seria criar
ligacao falsa.

Por isso o upgrade ABORTA se houver linhas com `canal_identificador` preenchido.
Para um banco pre-lancamento (o caso normal aqui) a tabela esta vazia e a
migration passa. Para um banco com dado real, o operador precisa resolver o
vínculo manualmente antes — a guarda existe para nao fazer isso as cegas.
"""
from __future__ import annotations

from alembic import context, op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "a1c4f7e29b83"
down_revision = "5e6e1fc3d096"
branch_labels = None
depends_on = None


def _contatos_com_canal(ligacao) -> int:
    """Conta linhas de `contatos` que perderiam o vinculo com o canal.

    Guard de integridade: so faz sentido contra um banco conectado. Em modo
    offline (`--sql`) nao ha dados para inspecionar, e `execute()` devolve
    `None` — o guard e pulado.
    """
    if context.is_offline_mode():
        return 0
    return (
        ligacao.execute(
            sa.text(
                "SELECT count(*) FROM contatos "
                "WHERE canal_identificador IS NOT NULL "
                "OR canal_tipo IS NOT NULL"
            )
        ).scalar()
        or 0
    )


def upgrade() -> None:
    ligacao = op.get_bind()

    orfaos = _contatos_com_canal(ligacao)
    if orfaos:
        raise RuntimeError(
            f"Migration abortada: {orfaos} linha(s) em `contatos` tem "
            "`canal_identificador`/`canal_tipo` preenchido. A identidade por canal "
            "esta sendo movida para `contato_canais`, mas a tabela antiga nao "
            "guardava `canal_contratado_id` -- nao existe como saber a qual canal "
            "cada linha pertencia, e um backfill inventaria um vinculo falso.\n"
            "  Resolva manualmente antes de rodar de novo:\n"
            "    1. Para cada `contatos.canal_identificador`, identifique o "
            "`canais_contratados` correspondente;\n"
            "    2. INSERT em `contato_canais` (contato_id, canal_contratado_id, "
            "identificador);\n"
            "    3. UPDATE `contatos` SET canal_identificador = NULL, "
            "canal_tipo = NULL;\n"
            "  Se este banco nunca teve dado real (pre-lancamento), ignore: a "
            "tabela esta vazia e a migration prossegue."
        )

    op.create_table(
        "contato_canais",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("contato_id", sa.Integer(), nullable=False),
        sa.Column("canal_contratado_id", sa.Integer(), nullable=False),
        sa.Column("identificador", sa.String(length=120), nullable=False),
        sa.Column("push_name", sa.String(length=150), nullable=True),
        # `sa.func.now()` e nao `sa.text("now()")`: o texto cru geraria
        # `DEFAULT now()`, que so existe no Postgres. Compilado pelo SQLAlchemy,
        # vira `now()` no Postgres e `CURRENT_TIMESTAMP` no SQLite, que e o
        # mesmo que o `TimestampMixin` pede.
        sa.Column(
            "criado_em",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "atualizado_em",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["contato_id"], ["contatos.id"], ondelete="CASCADE", name="fk_contato_canais_contato"
        ),
        sa.ForeignKeyConstraint(
            ["canal_contratado_id"],
            ["canais_contratados.id"],
            ondelete="CASCADE",
            name="fk_contato_canais_canal_contratado",
        ),
        sa.PrimaryKeyConstraint("id"),
        # A mesma constraint do Evolution: um identificador POR CANAL. Sem o
        # canal no UNIQUE, o contato de duas unidades colidiria.
        sa.UniqueConstraint(
            "canal_contratado_id", "identificador",
            name="uq_contato_canais_canal_identificador",
        ),
    )
    op.create_index("ix_contato_canais_contato_id", "contato_canais", ["contato_id"])
    op.create_index(
        "ix_contato_canais_canal_contratado_id", "contato_canais", ["canal_contratado_id"]
    )
    op.create_index("ix_contato_canais_identificador", "contato_canais", ["identificador"])

    # `canal_tipo`/`canal_identificador` viram informativas: a identidade canonica
    # esta em `contato_canais`.
    #
    # Postgres faz os tres por ALTER TABLE direto. SQLite nao suporta
    # `ALTER TABLE ... DROP CONSTRAINT` nem `DROP NOT NULL`, entao la usamos
    # `batch_alter_table`, que recria a tabela. O caminho do Postgres NAO e
    # afetado — e o Postgres e o alvo. O modo batch existe para esta migration
    # ser testavel localmente, onde nao ha servidor de Postgres.
    if op.get_bind().dialect.name == "sqlite":
        with op.batch_alter_table("contatos") as batch:
            batch.alter_column(
                "canal_tipo", existing_type=sa.String(length=20), nullable=True
            )
            batch.alter_column(
                "canal_identificador", existing_type=sa.String(length=120), nullable=True
            )
            batch.drop_constraint("uq_contatos_empresa_canal", type_="unique")
    else:
        op.alter_column(
            "contatos", "canal_tipo", existing_type=sa.String(length=20), nullable=True
        )
        op.alter_column(
            "contatos", "canal_identificador", existing_type=sa.String(length=120), nullable=True
        )
        op.drop_constraint("uq_contatos_empresa_canal", "contatos", type_="unique")


def downgrade() -> None:
    ligacao = op.get_bind()

    # O NOT NULL volta, entao ninguem pode ficar com `canal_identificador` nulo.
    sem_canal = 0
    if not context.is_offline_mode():
        sem_canal = (
            ligacao.execute(
                sa.text("SELECT count(*) FROM contatos WHERE canal_identificador IS NULL")
            ).scalar()
            or 0
        )
    if sem_canal:
        raise RuntimeError(
            f"Downgrade abortado: {sem_canal} linha(s) em `contatos` estao com "
            "`canal_identificador` NULL, e a constraint restaurada exige NOT NULL. "
            "Copie o valor de `contato_canais.identificador` para o contato antes "
            "de reverter, ou a reversao vai falhar no meio."
        )

    op.drop_index("ix_contato_canais_identificador", table_name="contato_canais")
    op.drop_index("ix_contato_canais_canal_contratado_id", table_name="contato_canais")
    op.drop_index("ix_contato_canais_contato_id", table_name="contato_canais")
    op.drop_table("contato_canais")

    if op.get_bind().dialect.name == "sqlite":
        with op.batch_alter_table("contatos") as batch:
            batch.create_unique_constraint(
                "uq_contatos_empresa_canal",
                ["empresa_id", "canal_tipo", "canal_identificador"],
            )
            batch.alter_column(
                "canal_identificador", existing_type=sa.String(length=120), nullable=False
            )
            batch.alter_column("canal_tipo", existing_type=sa.String(length=20), nullable=False)
    else:
        op.create_unique_constraint(
            "uq_contatos_empresa_canal",
            "contatos",
            ["empresa_id", "canal_tipo", "canal_identificador"],
        )
        op.alter_column(
            "contatos", "canal_identificador", existing_type=sa.String(length=120), nullable=False
        )
        op.alter_column("contatos", "canal_tipo", existing_type=sa.String(length=20), nullable=False)
