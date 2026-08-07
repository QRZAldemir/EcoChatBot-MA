-- ==============================================================================
-- MIGRAÇÃO: Criação das tabelas contatos, emails_enviados, campanhas,
--           campanha_contatos e arquivos
-- ==============================================================================
-- Data: 2026-08-07
-- Descrição: Completa os itens do menu lateral referenciados em
--            docs/Barra Menu.png que ainda não tinham página/tabela própria:
--              - contatos          → agenda de clientes WhatsApp
--              - emails_enviados   → histórico da central de E-mail
--              - campanhas / campanha_contatos → disparo em massa via WhatsApp
--              - arquivos          → biblioteca de mídia do chat
-- ==============================================================================

CREATE TABLE IF NOT EXISTS contatos (
    id             INTEGER PRIMARY KEY AUTO_INCREMENT,
    nome           VARCHAR(100) NOT NULL,
    telefone       VARCHAR(20) NOT NULL UNIQUE,
    email          VARCHAR(100),
    empresa        VARCHAR(100),
    observacao     VARCHAR(300),
    origem         VARCHAR(20) NOT NULL DEFAULT 'manual',
    ativo          BOOLEAN NOT NULL DEFAULT TRUE,
    criado_em      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em  DATETIME
);

CREATE INDEX idx_contatos_telefone ON contatos (telefone);

CREATE TABLE IF NOT EXISTS emails_enviados (
    id            INTEGER PRIMARY KEY AUTO_INCREMENT,
    contato_id    INTEGER REFERENCES contatos(id),
    destinatario  VARCHAR(150) NOT NULL,
    assunto       VARCHAR(200) NOT NULL,
    corpo         TEXT NOT NULL,
    status        VARCHAR(20) NOT NULL DEFAULT 'pendente',
    erro_mensagem VARCHAR(300),
    enviado_em    DATETIME,
    criado_em     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS campanhas (
    id              INTEGER PRIMARY KEY AUTO_INCREMENT,
    nome            VARCHAR(100) NOT NULL,
    mensagem        TEXT NOT NULL,
    conexao_id      INTEGER NOT NULL REFERENCES conexoes(id),
    status          VARCHAR(20) NOT NULL DEFAULT 'rascunho',
    total_contatos  INTEGER NOT NULL DEFAULT 0,
    enviados        INTEGER NOT NULL DEFAULT 0,
    falhas          INTEGER NOT NULL DEFAULT 0,
    criado_em       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    enviado_em      DATETIME
);

CREATE TABLE IF NOT EXISTS campanha_contatos (
    id            INTEGER PRIMARY KEY AUTO_INCREMENT,
    campanha_id   INTEGER NOT NULL REFERENCES campanhas(id),
    contato_id    INTEGER NOT NULL REFERENCES contatos(id),
    status        VARCHAR(20) NOT NULL DEFAULT 'pendente',
    erro_mensagem VARCHAR(300),
    enviado_em    DATETIME
);

CREATE INDEX idx_campanha_contatos_campanha ON campanha_contatos (campanha_id);

CREATE TABLE IF NOT EXISTS arquivos (
    id              INTEGER PRIMARY KEY AUTO_INCREMENT,
    nome_original   VARCHAR(200) NOT NULL,
    nome_arquivo    VARCHAR(200) NOT NULL,
    tipo_mime       VARCHAR(100),
    tamanho_bytes   INTEGER,
    descricao       VARCHAR(300),
    atendimento_id  INTEGER REFERENCES atendimentos(id),
    criado_em       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ==============================================================================
-- NOTA DE PORTABILIDADE
-- ==============================================================================
-- "INTEGER PRIMARY KEY AUTO_INCREMENT" é sintaxe MySQL/MariaDB. Se o banco
-- alvo for PostgreSQL, trocar por "SERIAL PRIMARY KEY" (e remover
-- AUTO_INCREMENT); se for SQLite, "INTEGER PRIMARY KEY AUTOINCREMENT" já
-- basta (SQLite ignora o tipo declarado nas demais colunas) — ver
-- migrations/004_create_conexoes.sql para o mesmo padrão já usado aqui.
-- ==============================================================================

-- ==============================================================================
-- VERIFICAÇÃO PÓS-MIGRAÇÃO
-- ==============================================================================
-- SELECT COUNT(*) FROM contatos;          -- esperado: 0
-- SELECT COUNT(*) FROM emails_enviados;    -- esperado: 0
-- SELECT COUNT(*) FROM campanhas;          -- esperado: 0
-- SELECT COUNT(*) FROM campanha_contatos;  -- esperado: 0
-- SELECT COUNT(*) FROM arquivos;           -- esperado: 0
-- ==============================================================================
