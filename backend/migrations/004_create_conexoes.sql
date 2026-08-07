-- ==============================================================================
-- MIGRAÇÃO: Criação da tabela conexoes
-- ==============================================================================
-- Data: 2026-08-07
-- Descrição: Cria a tabela de conexões WhatsApp (WABA) geridas via Evolution
--            API — painel de controle referenciado em
--            docs/Painel de Controle com vinculo da empresa que contratou  o sistema.png.
--            Cada linha é um número WhatsApp vinculado ao sistema; a coluna
--            "padrao" identifica o número administrativo principal da empresa.
-- ==============================================================================

CREATE TABLE IF NOT EXISTS conexoes (
    id                       INTEGER PRIMARY KEY AUTO_INCREMENT,
    nome                     VARCHAR(100) NOT NULL,
    telefone                 VARCHAR(20),
    tipo                     VARCHAR(20) NOT NULL DEFAULT 'whatsapp',
    conexao                  VARCHAR(30) NOT NULL DEFAULT 'waba',
    atendimento              VARCHAR(20) NOT NULL DEFAULT 'automatico',
    status                   VARCHAR(20) NOT NULL DEFAULT 'desconectada',
    padrao                   BOOLEAN NOT NULL DEFAULT FALSE,
    ativo                    BOOLEAN NOT NULL DEFAULT TRUE,
    evolution_instance_name  VARCHAR(100),
    criado_em                DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em            DATETIME
);

CREATE INDEX idx_conexoes_status ON conexoes (status);

-- ==============================================================================
-- NOTA DE PORTABILIDADE
-- ==============================================================================
-- "INTEGER PRIMARY KEY AUTO_INCREMENT" é sintaxe MySQL/MariaDB. Se o banco
-- alvo for PostgreSQL, trocar por "SERIAL PRIMARY KEY" (e remover
-- AUTO_INCREMENT); se for SQLite, "INTEGER PRIMARY KEY AUTOINCREMENT" já
-- basta (SQLite ignora o tipo declarado nas demais colunas).
-- ==============================================================================

-- ==============================================================================
-- VERIFICAÇÃO PÓS-MIGRAÇÃO
-- ==============================================================================
-- SELECT COUNT(*) FROM conexoes;
-- Resultado esperado: 0 (tabela recém-criada, sem erro)
-- ==============================================================================
