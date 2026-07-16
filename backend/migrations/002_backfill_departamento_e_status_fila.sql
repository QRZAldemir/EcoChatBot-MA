-- ==============================================================================
-- MIGRAÇÃO: Backfill de departamento_id e normalização do status "fila"
-- ==============================================================================
-- Data: 2026-07-16
-- Descrição: Corrige dados gravados antes da mudança que passou a preencher
--            Atendimento.departamento_id junto com canal_id, e que passou a
--            usar o status "fila" para atendimentos entregues a um
--            departamento/canal mas ainda sem atendente (usuario_id) puxando.
--
-- MOTIVO DA MUDANÇA:
-- O relatório de atendimento da ZigChat não expõe um campo "Departamento",
-- o que torna impossível distinguir, quando o cliente não é atendido: (a)
-- o robô não conseguiu entregar a conversa a um departamento, de (b) a
-- conversa foi entregue mas nenhum atendente a puxou. O bot_service e o
-- AtendimentoService deste projeto agora gravam essa distinção no momento
-- em que ela acontece (departamento_id preenchido a partir do canal; status
-- "fila" só vira "em_atendimento" quando um usuario_id é de fato atribuído).
-- Esta migração corrige os registros que já existiam antes dessa mudança.
-- ==============================================================================

-- 1) Preenche departamento_id a partir do canal já atribuído, quando ainda nulo.
--    Sintaxe de subquery correlacionada — funciona em MySQL/MariaDB, PostgreSQL e SQLite.
UPDATE atendimentos
SET departamento_id = (
    SELECT canais.departamento_id FROM canais WHERE canais.id = atendimentos.canal_id
)
WHERE departamento_id IS NULL
  AND canal_id IS NOT NULL;

-- 2) Normaliza status: atendimentos que estavam "em_atendimento" sem nunca
--    terem tido um atendente (usuario_id) atribuído são, na verdade, fila.
UPDATE atendimentos
SET status = 'fila'
WHERE status = 'em_atendimento'
  AND usuario_id IS NULL;

-- ==============================================================================
-- VERIFICAÇÃO PÓS-MIGRAÇÃO
-- ==============================================================================
-- SELECT COUNT(*) FROM atendimentos WHERE canal_id IS NOT NULL AND departamento_id IS NULL;
-- Resultado esperado: 0
--
-- SELECT COUNT(*) FROM atendimentos WHERE status = 'em_atendimento' AND usuario_id IS NULL;
-- Resultado esperado: 0
-- ==============================================================================
