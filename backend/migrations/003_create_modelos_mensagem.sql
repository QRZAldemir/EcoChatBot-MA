-- ==============================================================================
-- MIGRAÇÃO: Criação da tabela modelos_mensagem
-- ==============================================================================
-- Data: 2026-07-16
-- Descrição: Cria a tabela de mensagens padrão (memorando), cadastradas pelo
--            administrador e reutilizáveis no envio a clientes. Espelha, para
--            mensagens de texto/arquivo livre, o que a tabela "menus" já faz
--            para mensagens interativas (com botões).
--
-- MOTIVO DA MUDANÇA:
-- O módulo de cadastro de mensagens (equivalente ao menu "Mensagens" do
-- ZigChat) precisa de dois tipos de mensagem reutilizável: Padrão (texto ou
-- arquivo livre, memorando) e Interativa (com botões — já coberta pela
-- tabela "menus"/"menu_opcoes" existente). Esta migração cria a parte que
-- ainda não existia: as mensagens Padrão.
-- ==============================================================================

CREATE TABLE IF NOT EXISTS modelos_mensagem (
    id               INTEGER PRIMARY KEY AUTO_INCREMENT,
    descricao        VARCHAR(100) NOT NULL,
    corpo            TEXT NOT NULL,
    arquivo          VARCHAR(300),
    departamento_id  INTEGER,
    ativo            BOOLEAN NOT NULL DEFAULT TRUE,
    criado_em        DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em    DATETIME,
    CONSTRAINT fk_modelos_mensagem_departamento
        FOREIGN KEY (departamento_id) REFERENCES departamentos(id)
);

CREATE INDEX idx_modelos_mensagem_departamento ON modelos_mensagem (departamento_id);

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
-- SELECT COUNT(*) FROM modelos_mensagem;
-- Resultado esperado: 0 (tabela recém-criada, sem erro)
-- ==============================================================================
