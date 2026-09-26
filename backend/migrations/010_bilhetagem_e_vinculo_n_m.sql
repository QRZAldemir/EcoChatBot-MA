-- =============================================================================
-- MIGRACAO: 010_bilhetagem_e_vinculo_n_m.sql
-- AUTOR: Aldemir Queiroz
-- DATA: 2026-09-26
-- OBJETIVO: Alinhar o banco ao model v3 (ChamadaPABX) e criar o vinculo N:M
--          usuario <-> canal. Preserva os dados ja gravados.
-- PASTA: backend/migrations/
--
-- ############################################################################
-- # LEIA ANTES DE EXECUTAR                                                  #
-- #                                                                          #
-- # ESTA MIGRACAO NAO FOI TESTADA CONTRA O BANCO REAL.                       #
-- # Foi escrita a partir dos DDLs de 004/006/009 e do model v3. O banco real #
-- # pode ter sido alterado na mao depois disso.                              #
-- #                                                                          #
-- # A secao 2 (backfill canais -> canais_contratados) depende de colunas     #
-- # que NUNCA foram criadas por migration (ver nota nela). Confira a secao   #
-- # 0 antes. Se algum SELECT nao bater com o que voce espera, PARE.          #
-- #                                                                          #
-- # RECOMENDACAO: rode dentro de uma transacao e so faca COMMIT depois de    #
-- # ler a secao 9 (verificacao). O script ja abre BEGIN/COMMIT.              #
-- ############################################################################
--
-- O QUE ESTA MIGRACAO FAZ
--   1. Cria `canais_contratados` (nenhuma migration cria: a 009 apenas a usa)
--   2. Move os dados de `canais` para `canais_contratados`
--   3. Acrescenta as colunas de auditoria que o banco nao tem em
--      `chamadas_pabx` e realinha o model aos nomes que o banco ja usa
--   4. DERRUBA os ON DELETE CASCADE da bilhetagem (ver 4.2 - importante)
--   5. Cria `usuarios_canais` (o N:M nao tinha migration nenhuma)
--   6. Inclui 'pabx' na CHECK de tipo de canal (hoje ela REJEITA pabx)
-- =============================================================================

BEGIN;

-- =============================================================================
-- 0. VERIFICACAO PREVIA - rode antes, anote os numeros
-- =============================================================================
-- SELECT count(*) AS canais_antigos        FROM canais;
-- SELECT count(*) AS clientes             FROM clientes;
-- SELECT count(*) AS empresas             FROM empresas;
-- SELECT count(*) AS atendimentos          FROM atendimentos;
-- SELECT count(*) AS usuarios             FROM usuarios;
-- SELECT count(*) AS chamadas_antigas     FROM chamadas_pabx;
-- SELECT count(*) AS usuarios_com_canal   FROM usuarios WHERE canal_id IS NOT NULL;
-- SELECT DISTINCT status FROM chamadas_pabx;      -- deve conter 'iniciando'
-- SELECT to_regclass('canais_contratados');      -- esperado: NULL (ainda nao existe)
-- SELECT to_regclass('usuarios_canais');          -- esperado: NULL (ainda nao existe)
-- SELECT column_name FROM information_schema.columns
--   WHERE table_name = 'canais' ORDER BY ordinal_position;
-- =============================================================================

-- =============================================================================
-- 1. canais_contratados - a tabela que NINGUEM migration criava
-- =============================================================================
-- A 009 diz "em banco novo, canais_contratados ainda nao existe: pule este
-- bloco" - mas em banco novo ela nunca era criada. Resultado: o model
-- referenciava uma tabela inexistente.
CREATE TABLE IF NOT EXISTS canais_contratados (
    id             SERIAL PRIMARY KEY,
    -- Tenant. ON DELETE CASCADE aqui e seguro: apagar a EMPRESA e um ato
    -- explicito de encerrar a operacao, e a empresa e a unica entidade que
    -- pode levar tudo junto. O que nao pode e o mesmo valendo para canal
    -- (secao 4) ou cliente (secao 4.2) - essas duas erodeem historico.
    empresa_id     INTEGER      NOT NULL REFERENCES empresas(id)       ON DELETE CASCADE,
    telefone_id    INTEGER      NOT NULL REFERENCES telefones(id)      ON DELETE CASCADE,
    tipo           VARCHAR(20)  NOT NULL DEFAULT 'whatsapp',
    apelido        VARCHAR(80)  NOT NULL DEFAULT '',
    credenciais    TEXT,
    webhook_url    VARCHAR(300),
    webhook_token  VARCHAR(120),
    -- Janela de atendimento. NULL = sem restricao. Alem disso o schema
    -- valida que horario_inicio < horario_fim e que os dias sao conhecidos.
    horario_inicio VARCHAR(5),
    horario_fim    VARCHAR(5),
    dias_semana    VARCHAR(20),
    ativo          BOOLEAN     NOT NULL DEFAULT TRUE,
    criado_em      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em  TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at     TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_canais_contratados_empresa
    ON canais_contratados (empresa_id);
CREATE INDEX IF NOT EXISTS idx_canais_contratados_telefone
    ON canais_contratados (telefone_id);

-- =============================================================================
-- 2. BACKFILL canais -> canais_contratados
-- =============================================================================
-- ⚠️ ESTE BLOCO DEPENDE DE COLUNAS DE `canais` QUE EU NAO VI SENDO CRIADAS
-- POR NENHUMA MIGRATION. Reconstrui os nomes a partir de como outras
-- migrations os CITAM (grep: canais.id, .cliente_id, .tipo, .identificador,
-- .configuracao, .webhook_url, .webhook_verify_token, .ultimo_sync,
-- .departamento_id), e a 007 menciona um `AFTER descricao`.
--
-- Se a tabela `canais` foi criada fora das migrations, ela pode ter colunas
-- com outros nomes. CONFIRME com o SELECT da secao 0 antes de rodar isto.
--
-- MAPEAMENTO
--   canais.nome                -> apelido        (model nao tem mais `nome`)
--   canais.identificador       -> dentro de credenciais (JSON)
--   canais.configuracao        -> dentro de credenciais (JSON)
--   canais.cliente_id          -> empresa_id     (via clientes.id -> empresas)
--   canais.webhook_verify_token-> webhook_token
--   canais.status_conexao      -> ativo
--   canais.departamento_id     -> DESCARTADO (departamento nao pertence ao canal;
--                                 quem decide destino e o menu / roteamento)
-- =============================================================================

-- 2.1 Telefone: derivamos do telefone da empresa.
--     NOTA: aqui NAO uso `ON CONFLICT DO NOTHING` de proposito. Ele exige que a
--     coluna de conflito tenha um indice unique, e eu nao criei a tabela
--     telefones - se ela nao tiver o indice, a migration inteira aborta por um
--     detalhe que nao tem nada a ver com o objetivo. O `WHERE NOT EXISTS` faz o
--     mesmo trabalho e so depende do que eu sei existir.
INSERT INTO telefones (cliente_id, empresa_id, numero, pais, principal, ativo)
SELECT e.cliente_id, e.id, e.telefone, '55', FALSE, TRUE
  FROM empresas e
 WHERE e.telefone IS NOT NULL AND e.telefone <> ''
   AND NOT EXISTS (
       SELECT 1 FROM telefones t2
        WHERE t2.empresa_id = e.id AND t2.numero = e.telefone);

-- 2.2 Copia dos canais, convertendo o tenant e fundindo as credenciais.
--     `telefone_id` e NOT NULL, entao o 2.1 precisa ter produzido um telefone
--     para CADA empresa que tiver canal. A secao 9 verifica os orfaos.
INSERT INTO canais_contratados
    (empresa_id, telefone_id, tipo, apelido, credenciais, webhook_url,
     webhook_token, ativo, criado_em, atualizado_em)
SELECT
    e.id,
    t.id,
    c.tipo,
    COALESCE(NULLIF(c.nome, ''), 'Canal migrado ' || c.id),
    -- `identificador` e `configuracao` viram um unico JSON, porque o model
    -- passou a guardar as credenciais num campo so. A chave CHAVE_IDENTIFICADOR
    -- e a mesma que o CanalService le.
    json_build_object(
        'identificador',      c.identificador,
        'configuracao',       c.configuracao,
        'ultimo_sync',        c.ultimo_sync,
        'departamento_id',    c.departamento_id
    )::text,
    c.webhook_url,
    c.webhook_verify_token,
    (COALESCE(c.status_conexao, 'ativo') = 'ativo'),
    COALESCE(c.criado_em, NOW()),
    COALESCE(c.atualizado_em, NOW())
  FROM canais c
  LEFT JOIN clientes  cl ON cl.id = c.cliente_id
  LEFT JOIN empresas   e  ON e.cliente_id = c.cliente_id
  LEFT JOIN telefones  t  ON t.empresa_id = e.id
                         AND t.numero    = e.telefone
 WHERE NOT EXISTS (SELECT 1 FROM canais_contratados cc WHERE cc.apelido = c.nome)
   AND e.id IS NOT NULL;   -- canal sem empresa nao entra: ficaria orfao

-- =============================================================================
-- 3. chamadas_pabx - colunas que o BANCO nao tem e o model v3 exige
-- =============================================================================
-- Cada ADD COLUMN IF NOT EXISTS e seguro para re-execucao.
-- empresa_id: NOT NULL nao pode ser aplicado antes do backfill da secao 5.
ALTER TABLE chamadas_pabx ADD COLUMN IF NOT EXISTS empresa_id      INTEGER;
ALTER TABLE chamadas_pabx ADD COLUMN IF NOT EXISTS iniciada_em     TIMESTAMPTZ;
ALTER TABLE chamadas_pabx ADD COLUMN IF NOT EXISTS atendida_em     TIMESTAMPTZ;
ALTER TABLE chamadas_pabx ADD COLUMN IF NOT EXISTS tipo            VARCHAR(20) NOT NULL DEFAULT 'entrada';
ALTER TABLE chamadas_pabx ADD COLUMN IF NOT EXISTS gravacao_hash   VARCHAR(64);
ALTER TABLE chamadas_pabx ADD COLUMN IF NOT EXISTS atualizado_em  TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP;

-- Soft delete: e o que sustenta a auditoria. Sem esta coluna, qualquer
-- delete() em service apaga a bilhetagem.
ALTER TABLE chamadas_pabx ADD COLUMN IF NOT EXISTS deleted_at     TIMESTAMPTZ;

CREATE INDEX IF NOT EXISTS idx_chamadas_empresa   ON chamadas_pabx (empresa_id);
CREATE INDEX IF NOT EXISTS idx_chamadas_iniciada  ON chamadas_pabx (iniciada_em);
CREATE INDEX IF NOT EXISTS idx_chamadas_hash      ON chamadas_pabx (gravacao_hash);

-- =============================================================================
-- 4. chamadas_pabx - TIRAR O CASCADE (a parte que mais importa)
-- =============================================================================
-- 4.1 O FK do canal aponta para `canais(id)`, que a 2 substituiu. Repontamos
--     para `canais_contratados` e usamos SET NULL: se o canal for removido, a
--     ligacao continua registrada, so que sem canal. Perder a bilhetagem por
--     causa de uma mudanca de configuracao de canal e inaceitavel.
ALTER TABLE chamadas_pabx DROP CONSTRAINT IF EXISTS fk_chamadas_canal;
DROP INDEX IF EXISTS idx_chamadas_pabx_canal_id;
ALTER TABLE chamadas_pabx DROP COLUMN IF EXISTS canal_id;

ALTER TABLE chamadas_pabx ADD COLUMN IF NOT EXISTS canal_contratado_id INTEGER;
ALTER TABLE chamadas_pabx
    ADD CONSTRAINT fk_chamadas_canal_contratado
    FOREIGN KEY (canal_contratado_id) REFERENCES canais_contratados(id) ON DELETE SET NULL;

-- 4.2 O CASCADE DO CLIENTE. Este era o pior: apagar um cliente da conta
--     comercial levava junto TODAS as ligacoes billing dele. Vira RESTRICT.
ALTER TABLE chamadas_pabx DROP CONSTRAINT IF EXISTS fk_chamadas_cliente;
ALTER TABLE chamadas_pabx
    ADD CONSTRAINT fk_chamadas_cliente
    FOREIGN KEY (cliente_id) REFERENCES clientes(id) ON DELETE RESTRICT;

-- 4.3 cliente_id era NOT NULL. O tenant agora e empresa_id; cliente_id fica
--     so como vinculo com a conta comercial e passa a ser opcional.
--     So relaxa depois do backfill da 5, e so se nao houver orfao.
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
         WHERE table_name = 'chamadas_pabx'
           AND column_name = 'cliente_id'
           AND is_nullable = 'NO'
    ) THEN
        EXECUTE 'ALTER TABLE chamadas_pabx ALTER COLUMN cliente_id DROP NOT NULL';
    END IF;
END $$;

-- =============================================================================
-- 5. chamadas_pabx - backfill do tenant
-- =============================================================================
-- empresa_id vem da cadeia cliente -> empresa, que e a unica ligacao confiavel
-- antes da 2 (nao depende de a copia de canais ter rodado).
UPDATE chamadas_pabx cp
   SET empresa_id = e.id
  FROM clientes cl
  JOIN empresas  e ON e.cliente_id = cl.id
 WHERE cp.cliente_id = cl.id
   AND cp.empresa_id IS NULL;

-- iniciada_em: nas ligacoes antigas so existe criado_em. A duracao da billing
-- e medida a partir de iniciada_em, entao sem isto a metrica fica sem base.
UPDATE chamadas_pabx
   SET iniciada_em = criado_em
 WHERE iniciada_em IS NULL AND criado_em IS NOT NULL;

-- Normaliza o status: o DEFAULT do banco e 'iniciando', mas a 002 e o codigo
-- antigo gravavam 'iniciada'. Os dois precisam virar o mesmo valor senao o
-- filtro de "ligacoes em curso" nao acha nada.
UPDATE chamadas_pabx SET status = 'iniciando' WHERE status = 'iniciada';

-- ONDE A EMPRESA NAO PUDE SER DEDUZIDA: fique explicito, nao silencioso.
DO $$
DECLARE orfaos INT;
BEGIN
    SELECT count(*) INTO orfaos FROM chamadas_pabx WHERE empresa_id IS NULL;
    IF orfaos > 0 THEN
        RAISE EXCEPTION
            'Migration 010 abortada: % chamada(s) sem empresa possivel (cliente_id orfao). '
            'Rode a secao 0 e resolva manualmente antes.', orfaos;
    END IF;
END $$;

-- Agora empresa_id e obrigatorio, como o model exige.
-- (o IF evita erro em banco onde a coluna ja era NOT NULL)
DO $$
BEGIN
    EXECUTE 'ALTER TABLE chamadas_pabx ALTER COLUMN empresa_id SET NOT NULL';
EXCEPTION WHEN others THEN
    RAISE NOTICE 'empresa_id ja era NOT NULL: nada a fazer';
END $$;

-- =============================================================================
-- 6. usuarios_canais - o vinculo N:M que nao tinha migration
-- =============================================================================
CREATE TABLE IF NOT EXISTS usuarios_canais (
    id                  SERIAL PRIMARY KEY,
    usuario_id          INTEGER      NOT NULL REFERENCES usuarios(id)  ON DELETE CASCADE,
    canal_contratado_id INTEGER      NOT NULL REFERENCES canais_contratados(id) ON DELETE CASCADE,
    principal           BOOLEAN     NOT NULL DEFAULT FALSE,
    ativo               BOOLEAN     NOT NULL DEFAULT TRUE,
    criado_em           TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em       TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_usuarios_canais_vinculo UNIQUE (usuario_id, canal_contratado_id)
);

CREATE INDEX IF NOT EXISTS idx_usuarios_canais_canal
    ON usuarios_canais (canal_contratado_id);
-- No maximo um canal principal por usuario. O Postgres nao faz "índice unico
-- parcial" sem `WHERE`, que e exatamente o caso aqui.
CREATE UNIQUE INDEX IF NOT EXISTS uq_usuarios_canais_principal
    ON usuarios_canais (usuario_id) WHERE principal;

-- 6.1 Backfill: o `canais.usuario_id` legado vira um vinculo, marcado como
--     principal (era o unico canal do usuario).
INSERT INTO usuarios_canais
    (usuario_id, canal_contratado_id, principal, ativo)
SELECT u.id, cc.id, TRUE, TRUE
  FROM usuarios u
  JOIN canais c  ON c.usuario_id = u.id
  LEFT JOIN canais_contratados cc
         ON cc.apelido = c.nome
        AND cc.empresa_id = (SELECT e.id FROM empresas e WHERE e.cliente_id = c.cliente_id)
 -- `cc.id IS NOT NULL` e obrigatorio: sem ele, um canal que nao casou com
 -- nenhum canais_contratados entraria com canal_contratado_id NULL, e a coluna
 -- e NOT NULL - a migration quebraria com um erro de constraint em vez de
 -- pular o registro e deixar o orfao visivel.
 WHERE cc.id IS NOT NULL
   AND NOT EXISTS (
        SELECT 1 FROM usuarios_canais uc
         WHERE uc.usuario_id = u.id AND uc.canal_contratado_id = cc.id);

-- =============================================================================
-- 7. chk_canal_tipo_valido - hoje REJEITA 'pabx'
-- =============================================================================
-- A CHECK criada na 006 lista 8 tipos e 'pabx' nao esta entre eles. O
-- TipoCanal do schema aceita 'pabx'. Resultado: criar um canal PABX estourava
-- violacao de constraint - e PABX e justamente o canal que o usuario
-- contrata para billing.
-- 'webchat' entra junto: e o valor que o enum TypeCanalMensageria usa.
ALTER TABLE canais_contratados DROP CONSTRAINT IF EXISTS chk_canal_tipo_valido;
ALTER TABLE canais_contratados
    ADD CONSTRAINT chk_canal_tipo_valido
    CHECK (tipo IN ('whatsapp','telegram','instagram','facebook','discord',
                    'pabx','voip_telefonia','email','chat_web','webchat','sms'));

-- 8. Status de atendimento: o schema da API aceitava 'aberto'/'fila', que o
--    model nao tem. Este CHECK impede que a divergencia volte a entrar.
ALTER TABLE atendimentos DROP CONSTRAINT IF EXISTS chk_atendimento_status;
ALTER TABLE atendimentos
    ADD CONSTRAINT chk_atendimento_status
    CHECK (status IN ('aguardando','em_andamento','pausado',
                      'transferido','finalizado','cancelado'));

COMMIT;

-- =============================================================================
-- 9. VERIFICACAO POS-MIGRACAO - leia antes de dar COMMIT (veja a nota acima)
-- =============================================================================
-- -- nada pode ter ficado sem tenant:
-- SELECT count(*) FROM chamadas_pabx WHERE empresa_id IS NULL;          -- 0
-- SELECT count(*) FROM chamadas_pabx WHERE cliente_id IS NULL;         -- ok se 0
--
-- -- a FK do canal tem que apontar para canais_contratados:
-- SELECT count(*) FROM chamadas_pabx WHERE canal_contratado_id IS NULL; -- suspeita
--
-- -- 'pabx' tem de ser aceito:
-- INSERT INTO canais_contratados (empresa_id, tipo, apelido)
--   VALUES (1, 'pabx', 'teste') RETURNING id;   -- deve funcionar
--
-- -- N:M criado e populado:
-- SELECT count(*) FROM usuarios_canais;
-- SELECT count(*) FROM usuarios_canais WHERE principal;  -- 1 por usuario, no max
--
-- -- o CASCADE nao pode ter voltado:
-- SELECT conname, confdeltype FROM pg_constraint
--  WHERE conrelid = 'chamadas_pabx'::regclass AND contype = 'f';
--   confdeltype: 'a' = NO ACTION, 'r' = RESTRICT, 'c' = CASCADE, 'n' = SET NULL
--   NENHUM pode ser 'c'.
-- =============================================================================
