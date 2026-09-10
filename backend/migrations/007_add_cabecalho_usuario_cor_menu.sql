-- ==============================================================================
-- MIGRAÇÃO: Cabeçalho, usuário vinculado e cor do botão em Mensagens Interativas
-- ==============================================================================
-- Data: 2026-08-11
-- Descrição: Adiciona à tabela "menus" as colunas "cabecalho" (header, até 60
--            caracteres) e "usuario_vinculado_id" (FK opcional para
--            "usuarios"); adiciona à tabela "menu_opcoes" a coluna "cor"
--            (cor do botão: verde | azul | vermelho | amarelo | roxo | cinza).
--
-- MOTIVO DA MUDANÇA:
-- O protótipo de referência do módulo de Mensagens (assets/menus/
-- modulo_mensagens.html) já previa esses três campos no formulário de
-- Mensagem Interativa; esta migração alinha o schema real a eles.
-- ==============================================================================

ALTER TABLE menus
    ADD COLUMN cabecalho VARCHAR(60) AFTER descricao;

ALTER TABLE menus
    ADD COLUMN usuario_vinculado_id INTEGER AFTER canal_id;

ALTER TABLE menus
    ADD CONSTRAINT fk_menus_usuario_vinculado
        FOREIGN KEY (usuario_vinculado_id) REFERENCES usuarios(id);

ALTER TABLE menu_opcoes
    ADD COLUMN cor VARCHAR(20) NOT NULL DEFAULT 'verde' AFTER ordem;

CREATE INDEX idx_menus_usuario_vinculado ON menus (usuario_vinculado_id);

-- ==============================================================================
-- NOTA DE PORTABILIDADE
-- ==============================================================================
-- A cláusula "AFTER coluna" é sintaxe MySQL/MariaDB (só reordena a exibição,
-- não afeta dados). Em PostgreSQL/SQLite, remover "AFTER ..." — a nova coluna
-- é adicionada ao final da tabela, o que não tem impacto funcional.
-- ==============================================================================

-- ==============================================================================
-- VERIFICAÇÃO PÓS-MIGRAÇÃO
-- ==============================================================================
-- SELECT cabecalho, usuario_vinculado_id FROM menus LIMIT 1;
-- SELECT cor FROM menu_opcoes LIMIT 1;
-- Resultado esperado: colunas presentes, sem erro; "cor" nunca NULL.
-- ==============================================================================
