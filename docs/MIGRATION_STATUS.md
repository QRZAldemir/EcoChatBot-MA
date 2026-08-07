# 🔄 Status de Migração — Renomeação de Coluna `canal` → `tipo_canal`

**Data:** 2026-07-05  
**Status:** ⏳ PENDENTE DE EXECUÇÃO NO BANCO DE DADOS

---

## ✅ Já Feito (Código Python)

### 1. Modelo ORM — `/backend/app/models/__init__.py`
- ✅ Renomeado: `canal = Column(Integer)` → `tipo_canal = Column(Integer)`
- ✅ Comentário adicionado explicando o conflito
- ✅ Relacionamento mantido: `canal = relationship("Canal")`

**Código:**
```python
tipo_canal = Column(Integer, default=1)  # CORRIGIDO: Renomeado de 'canal'
                                          # 1=WhatsApp, 2=Interno
canal_id = Column(Integer, ForeignKey("canais.id"))
canal = relationship("Canal")  # Sem conflito agora!
```

### 2. Schema Pydantic — `/backend/app/routers/atendimento.py`
- ✅ Renomeado: `canal: Optional[int]` → `tipo_canal: Optional[int]`
- ✅ Adicionado: `canal_id: Optional[int]`
- ✅ Comentários explicativos

**Código:**
```python
class AtendimentoResponse(BaseModel):
    tipo_canal: Optional[int] = None  # CORRIGIDO: tipo do canal (1/2)
    canal_id: Optional[int] = None     # Foreign key explícita
```

### 3. Service Layer — `/backend/app/services/atendimento_service.py`
- ✅ Atualizado filtro: `Atendimento.canal` → `Atendimento.tipo_canal`
- ✅ Comentário: "CORRIGIDO"

**Código:**
```python
if canal:
    query = query.filter(Atendimento.tipo_canal == canal)
```

### 4. Router Layer — `/backend/app/routers/atendimento.py`
- ✅ Mantido uso do relacionamento: `atendimento.canal` (objeto Canal)
- ✅ Comentário: "Refere-se ao RELACIONAMENTO, não à coluna"

---

## ⏳ Falta Fazer (Banco de Dados)

### Executar a Migração SQL

**Arquivo:** `/backend/migrations/001_rename_canal_to_tipo_canal.sql`

```bash
# Para MySQL/MariaDB:
mysql -u usuario -p banco < backend/migrations/001_rename_canal_to_tipo_canal.sql

# Para PostgreSQL:
psql -U usuario -d banco -f backend/migrations/001_rename_canal_to_tipo_canal.sql

# Ou usar o script Python:
cd backend
python run_migrations.py
```

### Checklist de Execução

- [ ] 1. Fazer backup do banco de dados
- [ ] 2. Executar migração em **STAGING** primeiro
- [ ] 3. Verificar se coluna foi renomeada:
  ```sql
  SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_NAME='atendimentos' AND COLUMN_NAME='tipo_canal';
  ```
- [ ] 4. Testar endpoints:
  - GET `/atendimentos/listar` → verificar `tipo_canal` na resposta
  - POST `/atendimentos/encerrar` → usar relacionamento `canal.nome`
- [ ] 5. Executar migração em **PRODUÇÃO**

---

## 🔍 Sincronização de Componentes

| Componente | Status | Detalhe |
|-----------|--------|---------|
| **Python ORM** | ✅ | `tipo_canal` renomeado, sem conflito |
| **Pydantic Schema** | ✅ | `tipo_canal + canal_id` |
| **Service Layer** | ✅ | Filtros ajustados |
| **Router Layer** | ✅ | Relacionamento mantido |
| **Banco de Dados** | ⏳ | Aguarda migração 001 |

---

## 📝 Impacto da Mudança

### Benefícios
- ✅ Remove conflito de tipos (coluna vs relacionamento)
- ✅ Tipo safety no Pydantic (tipo_canal é int, canal é objeto)
- ✅ Documentação clara no código

### Risco Baixo
- ✅ Mudança apenas de nome (não funcionalidade)
- ✅ Compatível com banco (simples RENAME COLUMN)
- ✅ Código Python já atualizado e testado

---

## 🚀 Próximas Etapas

1. **Agora:** Revisar este documento
2. **Hoje:** Executar migração em staging
3. **Amanhã:** Testar endpoints em staging
4. **Semana:** Deploy em produção com backup

---

**Responsável:** Aldemir Queiroz  
**Banco de Dados:** MySQL/MariaDB (ajuste conforme seu banco)  
**Urgência:** Média (resolve conflito de tipos, melhora documentação)
