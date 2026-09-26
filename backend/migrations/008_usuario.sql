-- ==============================================================================
-- ARQUIVO.....: migrations/008_usuario.sql
-- AUTOR.......: Aldemir Queiroz
-- EMAIL.......: queiroz@almarcx.com.br
-- PROJETO.....: EcoChatBot-MA - Sistema Multi-Tenant de Atendimento
-- MÓDULO......: Migração SQL — Objeto Usuario
-- VERSÃO......: 3.0.0
-- CRIADO EM...: 2024-01-15
-- ATUALIZADO..: 2026-09-19
-- BANCO.......: PostgreSQL 14+
-- ==============================================================================
-- DESCRIÇÃO...:
-- Cria a estrutura completa do objeto Usuario com todos os relacionamentos
-- (Empresa, NivelUsuario, Canal, Departamento, Turno, Conexao M:N).
-- ==============================================================================

-- 1. ALTERAÇÃO DA TABELA USUARIOS
ALTER TABLE usuarios
ADD COLUMN IF NOT EXISTS empresa_id          INTEGER,
ADD COLUMN IF NOT EXISTS usuario             VARCHAR(50),
ADD COLUMN IF NOT EXISTS foto                TEXT,
ADD COLUMN IF NOT EXISTS nivel_id            INTEGER,
ADD COLUMN IF NOT EXISTS departamento_id     INTEGER,
ADD COLUMN IF NOT EXISTS canal_id            INTEGER,
ADD COLUMN IF NOT EXISTS turno_id            INTEGER,
ADD COLUMN IF NOT EXISTS conexao_padrao_id   INTEGER,
ADD COLUMN IF NOT EXISTS status              VARCHAR(20) DEFAULT 'ativo' NOT NULL,
ADD COLUMN IF NOT EXISTS atualizado_em       TIMESTAMPTZ DEFAULT NOW();

-- Backfill para registros legados
UPDATE usuarios SET empresa_id = 1 WHERE empresa_id IS NULL;
UPDATE usuarios SET usuario = LOWER(SPLIT_PART(email, '@', 1)) WHERE usuario IS NULL;
UPDATE usuarios SET status = CASE WHEN ativo THEN 'ativo' ELSE 'inativo' END WHERE status IS NULL;

ALTER TABLE usuarios ALTER COLUMN empresa_id SET NOT NULL;
ALTER TABLE usuarios ALTER COLUMN usuario SET NOT NULL;

-- 2. CONSTRAINTS
ALTER TABLE usuarios
ADD CONSTRAINT fk_usuarios_empresa FOREIGN KEY (empresa_id) REFERENCES empresas(id) ON DELETE CASCADE,
ADD CONSTRAINT fk_usuarios_nivel FOREIGN KEY (nivel_id) REFERENCES nivel_usuario(id),
ADD CONSTRAINT fk_usuarios_departamento FOREIGN KEY (departamento_id) REFERENCES departamentos(id),
ADD CONSTRAINT fk_usuarios_canal FOREIGN KEY (canal_id) REFERENCES canais(id),
ADD CONSTRAINT fk_usuarios_turno FOREIGN KEY (turno_id) REFERENCES turnos(id),
ADD CONSTRAINT fk_usuarios_conexao_padrao FOREIGN KEY (conexao_padrao_id) REFERENCES conexoes(id),
ADD CONSTRAINT uq_usuarios_empresa_email UNIQUE (empresa_id, email),
ADD CONSTRAINT uq_usuarios_empresa_usuario UNIQUE (empresa_id, usuario);

-- 3. TABELA ASSOCIATIVA M:N — USUARIOS <-> CONEXOES
CREATE TABLE IF NOT EXISTS usuarios_conexoes (
    usuario_id INTEGER NOT NULL,
    conexao_id INTEGER NOT NULL,
    PRIMARY KEY (usuario_id, conexao_id),
    CONSTRAINT fk_uc_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    CONSTRAINT fk_uc_conexao FOREIGN KEY (conexao_id) REFERENCES conexoes(id) ON DELETE CASCADE
);

-- 4. ÍNDICES
CREATE INDEX IF NOT EXISTS idx_usuarios_empresa ON usuarios(empresa_id);
CREATE INDEX IF NOT EXISTS idx_usuarios_email ON usuarios(email);
CREATE INDEX IF NOT EXISTS idx_usuarios_usuario ON usuarios(usuario);
CREATE INDEX IF NOT EXISTS idx_usuarios_nivel ON usuarios(nivel_id);
CREATE INDEX IF NOT EXISTS idx_usuarios_departamento ON usuarios(departamento_id);
CREATE INDEX IF NOT EXISTS idx_usuarios_canal ON usuarios(canal_id);
CREATE INDEX IF NOT EXISTS idx_usuarios_turno ON usuarios(turno_id);

-- ==============================================================================
-- FIM DO ARQUIVO
-- ==============================================================================