# 📋 Migrações de Banco de Dados — EcoChatBot-MA

## Visão Geral

Este diretório contém scripts SQL para manter sincronizados o modelo ORM (Python/SQLAlchemy) e o esquema do banco de dados.

## 🔄 Como Aplicar Migrações

### Para MySQL/MariaDB:
```bash
mysql -u seu_usuario -p seu_banco < migrations/001_rename_canal_to_tipo_canal.sql
```

### Para PostgreSQL:
```bash
psql -U seu_usuario -d seu_banco -f migrations/001_rename_canal_to_tipo_canal.sql
```

### Para SQLite:
```bash
sqlite3 seu_banco.db < migrations/001_rename_canal_to_tipo_canal.sql
```

---

## 📝 Migrações Disponíveis

### 001_rename_canal_to_tipo_canal.sql
**Status:** ⚠️ PENDENTE (não aplicada em produção)

**O que faz:**
- Renomeia coluna `canal` → `tipo_canal` na tabela `atendimentos`

**Por quê:**
- Resolvia conflito entre coluna de tipo (1=WhatsApp, 2=Interno) e relacionamento ORM
- Schema Pydantic esperava `tipo_canal: int`, mas ORM retornava objeto `Canal`

**Sincronização com código:**
- ✅ Modelo ORM atualizado (`canal` → `tipo_canal`)
- ✅ Schema Pydantic atualizado (`canal` → `tipo_canal`)
- ✅ Service layer atualizado (filtros ajustados)
- ⏳ **FALTA:** Executar migração no banco de dados

**Como verificar se foi aplicada:**
```sql
-- MySQL
SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME='atendimentos' AND COLUMN_NAME='tipo_canal';

-- PostgreSQL
SELECT column_name FROM information_schema.columns
WHERE table_name='atendimentos' AND column_name='tipo_canal';

-- SQLite
PRAGMA table_info(atendimentos);
```

---

## ⚠️ Próximas Etapas

1. **Backup do banco de dados** (CRÍTICO)
   ```bash
   mysqldump -u usuario -p seu_banco > backup_$(date +%Y%m%d_%H%M%S).sql
   ```

2. **Aplicar migração** em ambiente de STAGING primeiro
   - Verificar se não há erros
   - Testar endpoints que usam `atendimento.tipo_canal`

3. **Validar sincronização**
   - Criar novo atendimento
   - Listar atendimentos (verificar resposta do schema)
   - Confirmar que `tipo_canal` aparece corretamente

4. **Aplicar em PRODUÇÃO** somente após validação

---

## 🗄️ Estrutura de Nomes

Migrações seguem o padrão: `NNN_descricao.sql`
- **NNN**: Número sequencial (001, 002, 003...)
- **descricao**: Descrição curta da mudança em snake_case

Exemplo: `002_add_canal_relationship.sql`

---

## 📌 Notas Importantes

- ✅ Todas as migrações têm reversão documentada (caso necessário)
- ✅ Sempre fazer backup antes de aplicar migrações
- ✅ Testar em staging antes de produção
- ✅ Documentar qualquer divergência entre script e banco real

---

## 🔍 Status de Sincronização

| Componente | Status | Observações |
|-----------|--------|-------------|
| Modelo ORM | ✅ Atualizado | `tipo_canal` renomeado |
| Schema Pydantic | ✅ Atualizado | `tipo_canal` + `canal_id` |
| Service Layer | ✅ Atualizado | Filtros ajustados |
| Banco de Dados | ⏳ PENDENTE | Aguarda execução da migração 001 |

---

**Última atualização:** 2026-07-05
