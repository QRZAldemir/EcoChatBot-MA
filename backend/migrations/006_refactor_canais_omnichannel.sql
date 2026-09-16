-- ==============================================================================
-- MIGRAÇÃO: 006_refactor_canais_omnichannel.sql
-- AUTOR: Aldemir Queiroz
-- DATA: 2026-09-16
-- VERSÃO: 2.0.0
-- OBJETIVO: Refatorar tabela de canais para suportar múltiplos tipos de canais
--           omnichannel (WhatsApp, Telegram, Instagram, Discord, VoIP, etc.)
--           com isolamento multi-tenant rigoroso.
-- PASTA: backend/migrations/
-- ==============================================================================

-- INÍCIO DA TRANSAÇÃO
BEGIN;

-- ==============================================================================
-- 1. ADICIONAR COLUNA cliente_id (ISOLAMENTO MULTI-TENANT)
-- ==============================================================================
-- Adiciona vínculo obrigatório com a tabela de clientes/tenants
ALTER TABLE canais 
ADD COLUMN IF NOT EXISTS cliente_id INTEGER;

-- Cria foreign key com cascade (deleta canais se tenant for removido)
ALTER TABLE canais 
ADD CONSTRAINT fk_canais_cliente 
FOREIGN KEY (cliente_id) 
REFERENCES clientes(id) 
ON DELETE CASCADE;

-- Cria índice para performance em queries por tenant
CREATE INDEX IF NOT EXISTS idx_canais_cliente_id ON canais(cliente_id);

-- ==============================================================================
-- 2. ADICIONAR COLUNA tipo (TIPO DO CANAL)
-- ==============================================================================
-- Adiciona coluna para identificar o tipo de canal
ALTER TABLE canais 
ADD COLUMN IF NOT EXISTS tipo VARCHAR(30) NOT NULL DEFAULT 'whatsapp';

-- Adiciona constraint para validar tipos permitidos
ALTER TABLE canais 
DROP CONSTRAINT IF EXISTS chk_canal_tipo_valido;

ALTER TABLE canais 
ADD CONSTRAINT chk_canal_tipo_valido 
CHECK (
    tipo IN (
        'whatsapp', 
        'telegram', 
        'instagram', 
        'facebook', 
        'discord', 
        'voip_telefonia', 
        'email', 
        'chat_web'
    )
);

-- Cria índice para filtros por tipo
CREATE INDEX IF NOT EXISTS idx_canais_tipo ON canais(tipo);

-- ==============================================================================
-- 3. ADICIONAR COLUNA identificador (TOKEN/NÚMERO/ID TÉCNICO)
-- ==============================================================================
-- Identificador único técnico do canal (token, número, page_id, etc.)
ALTER TABLE canais 
ADD COLUMN IF NOT EXISTS identificador VARCHAR(255) NOT NULL DEFAULT '';

-- Cria índice para busca rápida
CREATE INDEX IF NOT EXISTS idx_canais_identificador ON canais(identificador);

-- ==============================================================================
-- 4. ADICIONAR COLUNA configuracao (JSON COM SETTINGS ESPECÍFICOS)
-- ==============================================================================
-- Armazena configurações específicas de cada tipo de canal
ALTER TABLE canais 
ADD COLUMN IF NOT EXISTS configuracao TEXT;

-- ==============================================================================
-- 5. ADICIONAR COLUNAS DE WEBHOOK
-- ==============================================================================
-- URL configurada para receber webhooks da plataforma externa
ALTER TABLE canais 
ADD COLUMN IF NOT EXISTS webhook_url VARCHAR(500);

-- Token de verificação do webhook (Meta/Telegram)
ALTER TABLE canais 
ADD COLUMN IF NOT EXISTS webhook_verify_token VARCHAR(255);

-- ==============================================================================
-- 6. ADICIONAR COLUNA ultimo_sync (AUDITORIA)
-- ==============================================================================
-- Data do último sync com a API externa
ALTER TABLE canais 
ADD COLUMN IF NOT EXISTS ultimo_sync TIMESTAMP;

-- ==============================================================================
-- 7. ATUALIZAR COLUNA atualizado_em (TIMESTAMP)
-- ==============================================================================
-- Garante que a coluna existe e tem default correto
ALTER TABLE canais 
ADD COLUMN IF NOT EXISTS atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- ==============================================================================
-- 8. ATUALIZAR CONSTRAINT DE UNIQUE (NOME POR TENANT)
-- ==============================================================================
-- Remove constraint antiga se existir
ALTER TABLE canais 
DROP CONSTRAINT IF EXISTS canais_nome_key;

-- Adiciona constraint de nome único por tenant
ALTER TABLE canais 
ADD CONSTRAINT unq_canais_nome_cliente 
UNIQUE (cliente_id, nome);

-- ==============================================================================
-- 9. CRIAR TABELA canal_metricas (MÉTRICAS DE USO)
-- ==============================================================================
CREATE TABLE IF NOT EXISTS canal_metricas (
    id SERIAL PRIMARY KEY,
    canal_id INTEGER NOT NULL REFERENCES canais(id) ON DELETE CASCADE,
    data DATE NOT NULL DEFAULT CURRENT_DATE,
    mensagens_enviadas INTEGER DEFAULT 0,
    mensagens_recebidas INTEGER DEFAULT 0,
    minutos_chamada INTEGER DEFAULT 0,  -- Para VoIP
    usuarios_atendidos INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(canal_id, data)
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_canal_metricas_data ON canal_metricas(data);
CREATE INDEX IF NOT EXISTS idx_canal_metricas_canal ON canal_metricas(canal_id);

-- ==============================================================================
-- 10. ATUALIZAR DADOS EXISTENTES (MIGRAÇÃO DE DADOS)
-- ==============================================================================
-- Se houver canais existentes, definir tipo como 'whatsapp' e cliente_id
-- NOTA: Ajuste conforme necessidade do seu banco

-- Atualizar canais existentes para tipo whatsapp (se não tiver tipo)
UPDATE canais 
SET tipo = 'whatsapp' 
WHERE tipo IS NULL OR tipo = '';

-- Se houver uma forma de inferir cliente_id, faça aqui
-- Exemplo: se canais tem relacionamento com departamentos
-- UPDATE canais 
-- SET cliente_id = (
--     SELECT d.cliente_id 
--     FROM departamentos d 
--     WHERE d.id = canais.departamento_id
-- )
-- WHERE cliente_id IS NULL;

-- ==============================================================================
-- 11. COMENTÁRIOS NAS COLUNAS (DOCUMENTAÇÃO)
-- ==============================================================================
COMMENT ON COLUMN canais.cliente_id IS 'ID do tenant/empresa (isolamento multi-tenant)';
COMMENT ON COLUMN canais.tipo IS 'Tipo do canal: whatsapp, telegram, instagram, facebook, discord, voip_telefonia, email, chat_web';
COMMENT ON COLUMN canais.identificador IS 'Identificador técnico: token do bot, número de telefone, page_id, etc.';
COMMENT ON COLUMN canais.configuracao IS 'JSON com configurações específicas (WABA_ID, app_secret, etc.)';
COMMENT ON COLUMN canais.webhook_url IS 'URL configurada para receber webhooks da plataforma';
COMMENT ON COLUMN canais.webhook_verify_token IS 'Token de verificação do webhook (Meta/Telegram)';
COMMENT ON COLUMN canais.ultimo_sync IS 'Data do último sync com a API externa';

-- ==============================================================================
-- CONFIRMAÇÃO DA TRANSAÇÃO
-- ==============================================================================
COMMIT;

-- ==============================================================================
-- ROLLBACK (EM CASO DE ERRO)
-- ==============================================================================
-- Para rollback, execute:
-- ROLLBACK;
-- ==============================================================================