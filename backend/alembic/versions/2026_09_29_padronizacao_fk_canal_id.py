"""padronizacao_fk_canal_id

Gerado por Alembic em 2026-09-29 00:00:00 UTC. NAO edite a logica deste arquivo depois de
aplicado: o Alembic guarda o hash da revision no banco e um arquivo editado
na mao quebra a cadeia.

Documentacao da revision
------------------------
Padronizacao da chave estrangeira de Canal em Menu, Atendimento e ContatoCanais.

MOTIVO:
- Inconsistencia de nomenclatura e alvo: Modulos usavam `canal_contratado_id` 
  apontando para `canais_contratados.id`, enquanto o dominio unificado utiliza 
  `canal_id` apontando para `canais.id`.
- Isso gerava friccao no mapeamento de DTOs, consultas relacionais e risco de 
  integridade caso a tabela `canais_contratados` fosse descontinuada.

ACAO:
1. Renomeia `canal_contratado_id` para `canal_id` em `menus`, `atendimentos` e `contato_canais`.
2. Recria as constraints de chave estrangeira apontando para a tabela unificada `canais`.
3. Aplica as regras de `ondelete` corretas (`CASCADE` para menus e contato_canais, 
   `RESTRICT` para atendimentos, protegendo o historico).
4. Atualiza os indices compostos e simples para refletir a nova nomenclatura.
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'padronizacao_fk_canal_id'
# A cadeia agora aponta corretamente para a última migration existente.
down_revision = 'a1c4f7e29b83'  
branch_labels = None
depends_on = None


def upgrade() -> None:
    # =========================================================================
    # 1. Tabela: menus
    # =========================================================================
    op.drop_constraint('fk_menus_canal_contratado_id_canais_contratados', 'menus', type_='foreignkey')
    op.alter_column('menus', 'canal_contratado_id', new_column_name='canal_id')
    op.create_foreign_key(
        'fk_menus_canal_id_canais', 
        'menus', 'canais', 
        ['canal_id'], ['id'], 
        ondelete='CASCADE'
    )

    # =========================================================================
    # 2. Tabela: atendimentos
    # =========================================================================
    op.drop_index('ix_atendimentos_empresa_canal', table_name='atendimentos')
    op.drop_constraint('fk_atendimentos_canal_contratado_id_canais_contratados', 'atendimentos', type_='foreignkey')
    op.alter_column('atendimentos', 'canal_contratado_id', new_column_name='canal_id')
    op.create_foreign_key(
        'fk_atendimentos_canal_id_canais', 
        'atendimentos', 'canais', 
        ['canal_id'], ['id'], 
        ondelete='RESTRICT'
    )
    op.create_index(
        'ix_atendimentos_empresa_canal', 
        'atendimentos', 
        ['empresa_id', 'canal_id']
    )

    # =========================================================================
    # 3. Tabela: contato_canais (Correção adicionada para consistência total)
    # =========================================================================
    op.drop_index('ix_contato_canais_canal_contratado_id', table_name='contato_canais')
    op.drop_constraint('fk_contato_canais_canal_contratado', 'contato_canais', type_='foreignkey')
    op.alter_column('contato_canais', 'canal_contratado_id', new_column_name='canal_id')
    op.create_foreign_key(
        'fk_contato_canais_canal_id_canais', 
        'contato_canais', 'canais', 
        ['canal_id'], ['id'], 
        ondelete='CASCADE'
    )
    op.create_index(
        'ix_contato_canais_canal_id', 
        'contato_canais', 
        ['canal_id']
    )
    # A UniqueConstraint também precisa ser recriada com o novo nome da coluna
    op.drop_constraint('uq_contato_canais_canal_identificador', 'contato_canais', type_='unique')
    op.create_unique_constraint(
        'uq_contato_canais_canal_identificador', 
        'contato_canais', 
        ['canal_id', 'identificador']
    )


def downgrade() -> None:
    # =========================================================================
    # 3. Tabela: contato_canais (Ordem inversa)
    # =========================================================================
    op.drop_constraint('uq_contato_canais_canal_identificador', 'contato_canais', type_='unique')
    op.drop_index('ix_contato_canais_canal_id', table_name='contato_canais')
    op.drop_constraint('fk_contato_canais_canal_id_canais', 'contato_canais', type_='foreignkey')
    op.alter_column('contato_canais', 'canal_id', new_column_name='canal_contratado_id')
    op.create_foreign_key(
        'fk_contato_canais_canal_contratado', 
        'contato_canais', 'canais_contratados', 
        ['canal_contratado_id'], ['id'], 
        ondelete='CASCADE'
    )
    op.create_index(
        'ix_contato_canais_canal_contratado_id', 
        'contato_canais', 
        ['canal_contratado_id']
    )
    op.create_unique_constraint(
        'uq_contato_canais_canal_identificador', 
        'contato_canais', 
        ['canal_contratado_id', 'identificador']
    )

    # =========================================================================
    # 2. Tabela: atendimentos (Ordem inversa)
    # =========================================================================
    op.drop_index('ix_atendimentos_empresa_canal', table_name='atendimentos')
    op.drop_constraint('fk_atendimentos_canal_id_canais', 'atendimentos', type_='foreignkey')
    op.alter_column('atendimentos', 'canal_id', new_column_name='canal_contratado_id')
    op.create_foreign_key(
        'fk_atendimentos_canal_contratado_id_canais_contratados', 
        'atendimentos', 'canais_contratados', 
        ['canal_contratado_id'], ['id'], 
        ondelete='RESTRICT'
    )
    op.create_index(
        'ix_atendimentos_empresa_canal', 
        'atendimentos', 
        ['empresa_id', 'canal_contratado_id']
    )

    # =========================================================================
    # 1. Tabela: menus (Ordem inversa)
    # =========================================================================
    op.drop_constraint('fk_menus_canal_id_canais', 'menus', type_='foreignkey')
    op.alter_column('menus', 'canal_id', new_column_name='canal_contratado_id')
    op.create_foreign_key(
        'fk_menus_canal_contratado_id_canais_contratados', 
        'menus', 'canais_contratados', 
        ['canal_contratado_id'], ['id'], 
        ondelete='CASCADE'
    )