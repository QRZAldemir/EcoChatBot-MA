-- ==============================================================================
-- MIGRAÇÃO: Telefone como entidade, contratação por telefone, assinatura
--            e histórico de transferências
-- ==============================================================================
-- Data: 2026-09-26
-- Descrição:
--   1. Cria `telefones` — o número passa a ser ENTIDADE (antes era uma
--      String solta em `empresas.telefone` e ficava escondido dentro de
--      `canais_contratados.credenciais`, num JSON em TEXT).
--   2. Cria `assinaturas` — estrutura do contrato comercial. SEM REGRA DE
--      COBRANÇA: o modelo de mensalidade ainda não foi definido.
--   3. Cria `transferencias` — auditoria append-only de TODA troca de
--      departamento de um atendimento.
--   4. Altera `canais_contratados`: coluna `telefone_id` e troca da
--      unicidade de (empresa_id, tipo) para (telefone_id, tipo).
--
-- MOTIVO DA MUDANÇA:
-- A regra de negócio é "cada telefone comporta 1 canal de cada tipo".
-- Uma Empresa com 2 telefones PODE contratar 2 WhatsApp — o segundo em
-- outro número. A constraint anterior `UNIQUE (empresa_id, tipo)` proibia
-- isso mesmo com o 2º número cadastrado, porque o telefone não era
-- referência: para o banco, os dois números eram indistinguíveis.
--
-- Ver: docs/ESTUDO_DE_CASO_CONTRATO_DE_CANAIS.md
--
-- DIALETO
-- --------
-- SQL portátil, testado em SQLite 3.37 (o banco de dev, ecochat_dev.db).
-- Usa `INTEGER PRIMARY KEY AUTOINCREMENT` porque o SQLite não tem coluna
-- IDENTITY.
--
-- ⚠️ O diretório migrations/ tem dialetos misturados e esta consistência
--    PRECISA ser corrigida em separado:
--      • 007_add_cabecalho_usuario_cor_menu.sql → MySQL  ("ADD COLUMN x AFTER y")
--      • 008_create_pedidos.sql                 → PostgreSQL ("GENERATED ... AS IDENTITY")
--    Nenhum dos dois roda no SQLite. Não os alterei aqui — é escopo próprio.
-- ==============================================================================


-- ──────────────────────────────────────────────────────────────────────────────
-- 1. TELEFONES
-- ──────────────────────────────────────────────────────────────────────────────
-- E.164 sem separadores. `UNIQUE (empresa_id, numero)`: o mesmo número não
-- é cadastrado duas vezes na mesma Empresa.
CREATE TABLE IF NOT EXISTS telefones (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_id  INTEGER NOT NULL REFERENCES clientes(id),
    empresa_id  INTEGER NOT NULL REFERENCES empresas(id) ON DELETE CASCADE,

    numero      VARCHAR(20) NOT NULL,      -- E.164 — ex.: 556734167800
    pais        VARCHAR(4)  NOT NULL DEFAULT '55',

    descricao   VARCHAR(80),
    principal   BOOLEAN NOT NULL DEFAULT 0,
    ativo       BOOLEAN NOT NULL DEFAULT 1,

    created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at  TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_telefones_empresa_numero
    ON telefones (empresa_id, numero);

CREATE INDEX IF NOT EXISTS ix_telefones_empresa_id  ON telefones (empresa_id);
CREATE INDEX IF NOT EXISTS ix_telefones_cliente_id  ON telefones (cliente_id);
CREATE INDEX IF NOT EXISTS ix_telefones_numero      ON telefones (numero);
CREATE INDEX IF NOT EXISTS ix_telefones_deleted_at  ON telefones (deleted_at);


-- ──────────────────────────────────────────────────────────────────────────────
-- 2. ASSINATURAS
-- ──────────────────────────────────────────────────────────────────────────────
-- ⚠️ ESTRUTURA SEM REGRA DE COBRANÇA. `valor_base` é o valor fixo do plano.
--    O valor por canal contratado NÃO é calculado aqui — o modelo comercial
--    de mensalidade ainda não foi definido pelo negócio.
CREATE TABLE IF NOT EXISTS assinaturas (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_id       INTEGER NOT NULL REFERENCES clientes(id),
    empresa_id       INTEGER NOT NULL REFERENCES empresas(id) ON DELETE CASCADE,

    plano            VARCHAR(20) NOT NULL DEFAULT 'basic',   -- free|basic|pro|enterprise
    status           VARCHAR(20) NOT NULL DEFAULT 'ativa',    -- trial|ativa|inadimplente|suspensa|cancelada
    valor_base       NUMERIC(12,2),     -- NÃO inclui o valor por canal

    inicio_vigencia  DATE,
    fim_vigencia     DATE,             -- NULL = vigência indeterminada
    observacoes      TEXT,

    created_at       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at       TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_assinaturas_empresa_id ON assinaturas (empresa_id);
CREATE INDEX IF NOT EXISTS ix_assinaturas_cliente_id ON assinaturas (cliente_id);
CREATE INDEX IF NOT EXISTS ix_assinaturas_status      ON assinaturas (status);
CREATE INDEX IF NOT EXISTS ix_assinaturas_deleted_at  ON assinaturas (deleted_at);


-- ──────────────────────────────────────────────────────────────────────────────
-- 3. TRANSFERENCIAS  (auditoria append-only — sem soft delete)
-- ──────────────────────────────────────────────────────────────────────────────
-- O destino do atendimento vem do MENU (menu_itens.departamento_id), nunca
-- do canal. Esta tabela responde: quem transferiu, de qual departamento para
-- qual, quando e por quê.
--
-- Não há `deleted_at`: registro de auditoria não é apagável.
CREATE TABLE IF NOT EXISTS transferencias (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_id    INTEGER NOT NULL REFERENCES clientes(id),
    atendimento_id INTEGER NOT NULL REFERENCES atendimentos(id) ON DELETE CASCADE,

    tipo          VARCHAR(20) NOT NULL DEFAULT 'atendente',  -- menu|atendente|ramal|sistema

    -- origem
    departamento_origem_id INTEGER REFERENCES departamentos(id) ON DELETE SET NULL,
    usuario_origem_id       INTEGER REFERENCES usuarios(id)       ON DELETE SET NULL,
    ramal_origem            VARCHAR(20),

    -- destino
    departamento_destino_id INTEGER REFERENCES departamentos(id) ON DELETE SET NULL,
    usuario_destino_id       INTEGER REFERENCES usuarios(id)       ON DELETE SET NULL,
    ramal_destino            VARCHAR(20),

    -- contexto
    canal_contratado_id INTEGER REFERENCES canais_contratados(id) ON DELETE SET NULL,
    menu_item_id        INTEGER REFERENCES menu_itens(id)          ON DELETE SET NULL,
    motivo              TEXT,

    transferido_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_transferencias_atendimento_id         ON transferencias (atendimento_id);
CREATE INDEX IF NOT EXISTS ix_transferencias_departamento_origem_id ON transferencias (departamento_origem_id);
CREATE INDEX IF NOT EXISTS ix_transferencias_departamento_destino_id ON transferencias (departamento_destino_id);
CREATE INDEX IF NOT EXISTS ix_transferencias_usuario_origem_id     ON transferencias (usuario_origem_id);
CREATE INDEX IF NOT EXISTS ix_transferencias_canal_contratado_id   ON transferencias (canal_contratado_id);
CREATE INDEX IF NOT EXISTS ix_transferencias_tipo                 ON transferencias (tipo);
CREATE INDEX IF NOT EXISTS ix_transferencias_transferido_em       ON transferencias (transferido_em);
CREATE INDEX IF NOT EXISTS ix_transferencias_cliente_id           ON transferencias (cliente_id);


-- ──────────────────────────────────────────────────────────────────────────────
-- 4. CANAIS_CONTRATADOS — eixo da contratação passa a ser o TELEFONE
-- ──────────────────────────────────────────────────────────────────────────────
-- ⚠️ BLOCO PARA BANCO COM DADOS — rode manualmente, na ordem.
--    Em banco novo, `canais_contratados` ainda não existe: nesse caso pule
--    este bloco e crie a tabela já com `telefone_id NOT NULL`.
--
-- 4.1. Coluna do telefone
-- ALTER TABLE canais_contratados
--     ADD COLUMN telefone_id INTEGER REFERENCES telefones(id) ON DELETE CASCADE;
--
-- 4.2. Backfill: cria um Telefone por número distinto já cadastrado na
--     empresa e aponta o canal para ele.
-- INSERT INTO telefones (cliente_id, empresa_id, numero, pais, principal, ativo)
-- SELECT DISTINCT e.cliente_id, e.id, e.telefone, '55', 0, 1
--   FROM empresas e
--   JOIN canais_contratados c ON c.empresa_id = e.id
--  WHERE e.telefone IS NOT NULL AND e.telefone <> '';
--
-- UPDATE canais_contratados
--    SET telefone_id = (
--        SELECT t.id FROM telefones t
--         WHERE t.empresa_id = canais_contratados.empresa_id
--           AND t.numero    = (SELECT e.telefone FROM empresas e
--                                WHERE e.id = canais_contratados.empresa_id)
--    )
--  WHERE telefone_id IS NULL;
--
-- 4.3. Troca da unicidade: (empresa_id, tipo) -> (telefone_id, tipo)
--      A nova regra permite 2 WhatsApp quando existem 2 telefones.
--      No SQLite não existe DROP CONSTRAINT: apague o índice antigo e crie o novo.
-- DROP INDEX IF EXISTS uq_canais_contratados_empresa_tipo;
-- CREATE UNIQUE INDEX IF NOT EXISTS uq_canais_contratados_telefone_tipo
--     ON canais_contratados (telefone_id, tipo);
--
-- 4.4. Torna o telefone obrigatório (só depois do backfill)
--      SQLite exige recriar a tabela para aplicar NOT NULL numa coluna já
--      existente — ver o procedimento em migrations/README.md.
--      No MySQL/PostgreSQL:
-- ALTER TABLE canais_contratados ALTER COLUMN telefone_id SET NOT NULL;
-- ==============================================================================
