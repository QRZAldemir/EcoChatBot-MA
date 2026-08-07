-- ==============================================================================
-- MIGRAÇÃO: Criação da tabela tokens_revogados
-- ==============================================================================
-- Data: 2026-08-07
-- Descrição: Suporte a logout real para JWT (stateless por natureza — sem
--            isso, um token roubado continuaria válido até expirar mesmo
--            após o usuário sair). Ver backend/app/security.py.
-- ==============================================================================

CREATE TABLE IF NOT EXISTS tokens_revogados (
    jti        VARCHAR(36) PRIMARY KEY,
    expira_em  DATETIME NOT NULL,
    criado_em  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ==============================================================================
-- NOTA DE PORTABILIDADE
-- ==============================================================================
-- "DATETIME"/tipos aqui já são portáveis entre MySQL, PostgreSQL e SQLite —
-- ver migrations/004_create_conexoes.sql para a nota completa sobre
-- AUTO_INCREMENT (não se aplica nesta tabela, cuja PK é o próprio jti).
-- ==============================================================================

-- ==============================================================================
-- MANUTENÇÃO
-- ==============================================================================
-- Linhas com expira_em no passado podem ser removidas periodicamente
-- (o token já venceria de qualquer forma, então mantê-las na tabela só
-- ocupa espaço, não é um risco de segurança):
--   DELETE FROM tokens_revogados WHERE expira_em < CURRENT_TIMESTAMP;
-- ==============================================================================

-- ==============================================================================
-- VERIFICAÇÃO PÓS-MIGRAÇÃO
-- ==============================================================================
-- SELECT COUNT(*) FROM tokens_revogados;  -- esperado: 0
-- ==============================================================================
