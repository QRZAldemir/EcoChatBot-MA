-- ==============================================================================
-- MIGRAÇÃO: Renomear coluna 'canal' para 'tipo_canal' na tabela 'atendimentos'
-- ==============================================================================
-- Data: 2026-07-05
-- Descrição: Resolve conflito de nome entre a coluna de tipo (1=WhatsApp, 2=Interno)
--            e o relacionamento com a tabela 'canais'
--
-- MOTIVO DA MUDANÇA:
-- O modelo ORM tinha:
--   1. canal = Column(Integer) - tipo de canal (1=WhatsApp, 2=Interno)
--   2. canal = relationship("Canal") - relacionamento com tabela canais
-- O segundo sobrescrevia o primeiro, causando conflito de tipos no schema Pydantic.
--
-- SOLUÇÃO:
-- Renomear a coluna 'canal' para 'tipo_canal', mantendo o relacionamento com o nome 'canal'
-- ==============================================================================

-- Para MySQL/MariaDB:
ALTER TABLE atendimentos CHANGE COLUMN canal tipo_canal INT DEFAULT 1;

-- Para PostgreSQL (use este em vez do MySQL se estiver usando PostgreSQL):
-- ALTER TABLE atendimentos RENAME COLUMN canal TO tipo_canal;

-- Para SQLite (use este se estiver usando SQLite):
-- Nota: SQLite tem limitações com ALTER COLUMN, então recomenda-se:
-- 1. Criar nova tabela com estrutura corrigida
-- 2. Copiar dados
-- 3. Remover tabela antiga
-- 4. Renomear nova tabela
-- Consulte a documentação do SQLite para detalhes completos.

-- ==============================================================================
-- VERIFICAÇÃO PÓS-MIGRAÇÃO
-- ==============================================================================
-- Execute a query abaixo para confirmar que a coluna foi renomeada:
-- SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
-- WHERE TABLE_NAME='atendimentos' AND COLUMN_NAME IN ('canal', 'tipo_canal');
--
-- Resultado esperado: Uma linha com 'tipo_canal' (sem 'canal')
-- ==============================================================================
