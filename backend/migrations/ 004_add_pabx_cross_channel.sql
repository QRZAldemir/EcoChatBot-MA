-- ==============================================================================
-- MIGRAÇÃO: 004_add_pabx_cross_channel.sql
-- OBJETIVO: Preparar a base para Integração Cross-Channel com PABX/IPVoIP.
-- ==============================================================================

BEGIN;

-- 1. Adicionar ramal físico no modelo de Usuário (Para transferência Cross-Channel)
ALTER TABLE usuarios
ADD COLUMN IF NOT EXISTS ramal_pabx VARCHAR(20) NULL;

COMMENT ON COLUMN usuarios.ramal_pabx IS 
'Ramal físico do PABX do cliente. Usado para transferir chamadas do painel web para o telefone do atendente.';

-- 2. Adicionar status de conexão no modelo de Canal (Healthcheck)
ALTER TABLE canais
ADD COLUMN IF NOT EXISTS status_conexao VARCHAR(30) DEFAULT 'ativo' NOT NULL;

-- 3. Criar a tabela de Bilhetagem (CDR) e Rastreamento de Chamadas PABX
CREATE TABLE IF NOT EXISTS chamadas_pabx (
    id SERIAL PRIMARY KEY,
    atendimento_id INTEGER NULL, -- Vínculo com o ticket Omnichannel (ex: veio do WhatsApp)
    canal_id INTEGER NOT NULL,   -- Vínculo com o Canal VoIP do Tenant
    cliente_id INTEGER NOT NULL, -- Isolamento Multi-Tenant
    pabx_call_id VARCHAR(100) NOT NULL UNIQUE, -- ID gerado pelo PABX do cliente
    numero_origem VARCHAR(30) NOT NULL,
    numero_destino VARCHAR(30) NOT NULL,
    status VARCHAR(30) DEFAULT 'iniciando' NOT NULL,
    duracao_segundos INTEGER DEFAULT 0,
    url_gravacao VARCHAR(500) NULL,
    resumo_ia TEXT NULL, -- Resumo gerado pelo DeepSeek ao final da chamada
    criado_em TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    finalizado_em TIMESTAMP WITH TIME ZONE NULL,
    
    CONSTRAINT fk_chamadas_atendimento FOREIGN KEY (atendimento_id) REFERENCES atendimentos(id) ON DELETE SET NULL,
    CONSTRAINT fk_chamadas_canal FOREIGN KEY (canal_id) REFERENCES canais(id) ON DELETE CASCADE,
    CONSTRAINT fk_chamadas_cliente FOREIGN KEY (cliente_id) REFERENCES clientes(id) ON DELETE CASCADE
);

-- Índices para performance e isolamento
CREATE INDEX IF NOT EXISTS idx_chamadas_pabx_canal ON chamadas_pabx(canal_id);
CREATE INDEX IF NOT EXISTS idx_chamadas_pabx_cliente ON chamadas_pabx(cliente_id);
CREATE INDEX IF NOT EXISTS idx_chamadas_pabx_call_id ON chamadas_pabx(pabx_call_id);

COMMIT;