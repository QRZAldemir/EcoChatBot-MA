# 🌳 EcoChatBot-MA · Estrutura do Projeto

> **Documento vivo** — atualize conforme implementa.
>
> **Legenda:**
> - ✅ Existe e funciona
> - ⏳ Parcial / incompleto
> - ❌ Não existe ainda
> - ❓ Precisa verificar
> - 🟡 Talvez ignorar

---

## 📁 Raiz do projeto

```
E:\EcoChatBot-MA\
├── .env.example                ✅
├── .gitignore                  ✅
├── README.md                   ❌ criar
├── package.json                ❌ criar
├── docker-compose.yml          ❌ criar
├── backend/                    ✅
├── docs/                       ✅
├── frontend/                   ✅
├── perplexity-code/            🟡
└── scripts/                    ❌ criar
```

## 🐍 Backend

```
backend/
├── package.json                ❌ criar
├── requirements.txt            ❌ criar
├── requirements-dev.txt        ❌ criar
├── main.py                     ❌ criar
├── export_openapi.py           ❌ criar
├── app/                        ✅
│   ├── exceptions/             ✅
│   ├── models/                 ✅
│   ├── repositories/           ✅
│   ├── routers/                ✅
│   ├── schemas/                ✅
│   ├── services/               ✅
│   └── tests/                  ✅
├── migrations/                 ✅
└── src/                        ❌ criar (Node helpers)
```

## 🎨 Frontend

```
frontend/
├── package.json                ❓ verificar
├── angular.json                ❓ verificar
├── tsconfig.json               ❓ verificar
└── src/
    ├── app/                    ❓ verificar
    │   ├── core/               ❓
    │   ├── features/           ❓
    │   ├── layouts/            ❓
    │   ├── shared/             ❓
    │   ├── app.component.ts    ❓
    │   ├── app.config.ts       ❓
    │   └── app.routes.ts       ❓
    ├── assets/                 ✅
    └── environments/           ✅
```

## 📚 Documentação

```
docs/
├── ESTRUTURA.md                🎯 este arquivo
├── ARQUITETURA.md              ❌ criar
├── API.md                      ❌ criar
├── BANCO-DE-DADOS.md           ❌ criar
├── ACESSIBILIDADE.md           ❌ criar
├── CANAIS.md                   ❌ criar
└── (22 arquivos existentes)    ✅
```

---

## 🎯 Prioridades

### 🔴 Alta

1. Criar `package.json` (raiz)
2. Criar `docker-compose.yml` (raiz)
3. Criar `backend/package.json`
4. Criar `backend/requirements.txt`
5. Verificar estrutura do frontend

### 🟡 Média

6. Criar `README.md`
7. Criar `backend/main.py`
8. Criar pasta `scripts/`

### 🟢 Baixa

9. Documentação em `docs/`
10. Pasta `backend/src/` (Node)

---

**Última atualização:** 2026-XX-XX
**Atualizado por:** Aldemir Queiroz