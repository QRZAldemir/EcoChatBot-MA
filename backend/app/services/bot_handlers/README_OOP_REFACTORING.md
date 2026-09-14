# 🏗️ Refatoração OOP — Bot Service

## Resumo da Arquitetura

Este módulo refatora o `bot_service.py` original (1692 linhas procedurais) em uma arquitetura **100% OOP** baseada nos 4 pilares:

### 1. **ENCAPSULAMENTO**
- Cada classe encapsula seu estado privado (prefixo `_`)
- `BotMáquinaEstados`: encapsula `_db`, `_evolution`, `_handlers`
- `EvolutionApiClient`: encapsula `_base_url`, `_api_key`, `_auth_header`
- `DepartamentoHandler`: encapsula `_db`, `_evolution`

### 2. **HERANÇA**
- `AtendimentoHandler` herda de `DepartamentoHandler`
- `AgendamentoHandler` herda de `DepartamentoHandler` (a implementar)
- `ExamesHandler` herda de `DepartamentoHandler` (a implementar)
- Todos reutilizam `_enviar_texto()`, `_enviar_lista()`, `_guardar_contexto()`

### 3. **POLIMORFISMO**
- Cada handler implementa `processar()` diferente
- `AtendimentoHandler.processar()` ≠ `AgendamentoHandler.processar()`
- `BotMáquinaEstados` despacha chamando `handler.processar()` — funciona com qualquer subclasse

### 4. **ABSTRAÇÃO**
- `DepartamentoHandler` abstrai detalhes de banco/API
- Subclasses focam apenas em lógica de negócio
- `EvolutionApiClient` abstrai HTTP — mudanças internas não afetam handlers

---

## Estrutura de Arquivos

```
backend/app/services/
├── bot_handlers/
│   ├── __init__.py                  # Exports
│   ├── base_handler.py              # Classe abstrata (interface)
│   ├── evolution_client.py          # Encapsula Evolution API
│   ├── bot_machine.py               # Orquestrador principal
│   ├── atendimento.py               # Handler de Atendimento (exemplo)
│   ├── agendamento.py               # Exemplo de fluxo configurável (TODO)
│   ├── pedidos_handler.py           # Fluxo genérico de pedidos
│   ├── fluxo_customizado.py         # Extensão para regras específicas (TODO)
│   ├── ouvidoria.py                 # Exemplo de feedback (TODO)
│   └── README_OOP_REFACTORING.md    # Este arquivo
├── bot_service.py                   # LEGADO (a remover gradualmente)
└── ...
```

---

## Como Usar

### 1. Criar Instância da Máquina de Estados

```python
from sqlalchemy.orm import Session
from app.services.bot_handlers import (
    BotMáquinaEstados,
    EvolutionApiClient,
    AtendimentoHandler,
)

def criar_bot_machine(db: Session) -> BotMáquinaEstados:
    """Factory function com Dependency Injection"""
    
    # Cria cliente da Evolution API
    evolution = EvolutionApiClient(
        base_url="http://localhost:8080",
        api_key="sua_chave_aqui",
    )
    
    # Cria handlers dos departamentos
    handlers = {
        "AT": AtendimentoHandler(db, evolution),
        "AG": AgendamentoHandler(db, evolution),  # TODO: implementar
        "FL": FluxoCustomizadoHandler(db, evolution), # TODO: implementar
        "OV": OuvidoriaHandler(db, evolution),        # TODO: implementar
    }
    
    # Cria máquina de estados
    bot = BotMáquinaEstados(db, evolution, handlers)
    return bot
```

### 2. Usar em Router FastAPI

```python
# app/routers/webhook.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.bot_handlers import BotMáquinaEstados

router = APIRouter()

def get_bot_machine(db: Session = Depends(get_db)) -> BotMáquinaEstados:
    """Dependency Injection para FastAPI"""
    return criar_bot_machine(db)

@router.post("/webhook/messages")
async def receber_mensagem(
    payload: dict,
    bot: BotMáquinaEstados = Depends(get_bot_machine),
):
    """Processa mensagem webhook"""
    await bot.processar_mensagem_recebida(
        instance_nome=payload["instance"],
        remote_jid=payload["remoteJid"],
        push_name=payload.get("pushName"),
        msg_type=payload["messageType"],
        content=payload["content"],
    )
    return {"status": "ok"}
```

### 3. Testar de Forma Isolada (Sem ContextVar!)

```python
# tests/test_handlers.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.models import Atendimento
from app.services.bot_handlers import AtendimentoHandler

@pytest.mark.asyncio
async def test_atendimento_handler_menu_principal():
    """Teste sem mágica de ContextVar 🎉"""
    
    # Mock das dependências
    db_mock = MagicMock()
    evolution_mock = AsyncMock()
    
    # Cria handler com mocks injetados
    handler = AtendimentoHandler(db_mock, evolution_mock)
    
    # Cria atendimento para teste
    at = Atendimento(
        id=1,
        telefone="67999999999",
        nome_contato="João",
        ativo=True,
        status="aberto",
    )
    
    # Chama método
    await handler.processar(at, "AT:MENU", None)
    
    # Verifica chamadas (explícitas!)
    assert evolution_mock.enviar_lista.called
    call_args = evolution_mock.enviar_lista.call_args
    assert "Atendimento ao Cliente" in str(call_args)
```

---

## Comparação: Antes vs Depois

### ANTES (Anti-pattern)

```python
# bot_service.py — 1692 linhas procedurais
_ctx_db = contextvars.ContextVar("_ctx_db")
_ctx_at = contextvars.ContextVar("_ctx_at")

async def processar_mensagem_recebida(...):
    _ctx_db.set(db)
    _ctx_at.set(at)
    # ...

async def _atendimento(...):
    db = _ctx_db.get()  # "Mágica" implícita
    at = _ctx_at.get()
    await _txt(...)     # Função solta, sem contexto claro

async def _txt(...):
    db = _ctx_db.get()  # Recupera "por magia"
    at = _ctx_at.get()  # Recupera "por magia"
    # ...
```

**Problemas:**
- ❌ Dependências implícitas (ContextVar)
- ❌ Difícil testar (precisa mockar ContextVar)
- ❌ Código duplicado entre departamentos
- ❌ 1 arquivo gigante = difícil manter
- ❌ Não segue padrão OOP

### DEPOIS (OOP Puro)

```python
# bot_machine.py + handlers — Classes encapsuladas
class BotMáquinaEstados:
    def __init__(self, db, evolution, handlers):
        self._db = db                    # Atributo privado
        self._evolution = evolution      # Injetado explicitamente
        self._handlers = handlers
    
    async def processar_mensagem_recebida(...):
        handler = self._handlers["AT"]   # Recupera handler
        await handler.processar(at, step, msg)

class AtendimentoHandler(DepartamentoHandler):
    def __init__(self, db, evolution):
        self._db = db                    # Encapsulado
        self._evolution = evolution      # Encapsulado
    
    async def processar(self, at, step, msg):
        # Lógica com dependências explícitas
        await self._enviar_texto(at, msg)  # Usa método da classe base

    async def _enviar_texto(self, at, msg):
        # Encapsula detalhes, mantém privado
        await self._evolution.enviar_texto(...)
```

**Benefícios:**
- ✅ Dependências explícitas (injeção no construtor)
- ✅ Fácil testar (mocka classes normais)
- ✅ Sem duplicação (herança + reutilização)
- ✅ Múltiplos arquivos pequenos = fácil manter
- ✅ Segue padrão OOP completo

---

## Próximos Passos (Implementação Completa)

### Fase 2: Implementar Handlers Restantes

1. **`agendamento.py`** (400 linhas do bot_service.py)
   - Seguir mesmo padrão: herdar de `DepartamentoHandler`
   - Implementar `processar()` com estados AG:*

2. **`exames.py`** (350 linhas do bot_service.py)
   - Mesmo padrão
   - Estados EX:*

3. **`fluxo_customizado.py`** (extensão para regras específicas do tenant)
   - Mesmo padrão
   - Estados PO:*

4. **`ouvidoria.py`** (300 linhas)
   - Mesmo padrão
   - Estados OV:*

### Fase 3: Teste Unitário Completo

```python
# tests/bot_handlers/test_atendimento.py
# tests/bot_handlers/test_agendamento.py
# ... etc
```

### Fase 4: Integração com Routers

Atualizar `app/routers/webhook.py` para usar nova arquitetura.

### Fase 5: Remover `bot_service.py`

Depois que tudo estiver refatorado e testado, deletar arquivo legado.

---

## Princípios SOLID Aplicados

| Princípio | Como Implementado |
|-----------|-------------------|
| **S**RP (Single Responsibility) | Cada handler é responsável por 1 departamento |
| **O**CP (Open/Closed) | Aberto para extensão (novo handler = herança), fechado para modificação (BotMáquinaEstados não muda) |
| **L**SP (Liskov Substitution) | Qualquer subclasse de DepartamentoHandler funciona na máquina de estados |
| **I**SP (Interface Segregation) | DepartamentoHandler expõe apenas o essencial (processar) |
| **D**IP (Dependency Inversion) | Handlers dependem de abstração (DepartamentoHandler), não de implementação |

---

## Diagrama de Classes

```
┌─────────────────────────────────────────┐
│    BotMáquinaEstados                    │
│  ┌───────────────────────────────────┐  │
│  │ - _db: Session                    │  │
│  │ - _evolution: EvolutionApiClient  │  │
│  │ - _handlers: Dict[str, Handler]   │  │
│  ├───────────────────────────────────┤  │
│  │ + processar_mensagem_recebida()   │  │
│  │ - _despachar_estado()             │  │
│  │ - _handler_boot()                 │  │
│  │ - _handler_lgpd()                 │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
           │ injeta
           ▼
┌──────────────────────────────────────┐
│ DepartamentoHandler (Abstrata)       │
│ ┌──────────────────────────────────┐ │
│ │ # _db: Session                   │ │
│ │ # _evolution: EvolutionApiClient │ │
│ ├──────────────────────────────────┤ │
│ │ + processar() [abstrato]         │ │
│ │ # _enviar_texto()                │ │
│ │ # _enviar_lista()                │ │
│ │ # _guardar_contexto()            │ │
│ └──────────────────────────────────┘ │
└──────────────────────────────────────┘
  △            △            △           △
  │            │            │           │
  │ herda      │ herda      │ herda     │ herda
  │            │            │           │
┌──────────┐ ┌──────────┐ ┌────────┐ ┌──────────┐
│Atendimento│ │Agendamen.│ │Exames  │ │Ouvidoria │
│ Handler  │ │ Handler  │ │Handler │ │ Handler  │
└──────────┘ └──────────┘ └────────┘ └──────────┘
```

---

## Debugging Tips

### Como debugar sem ContextVar

**Antes (difícil):**
```python
# Função solta, contexto implícito
async def _txt(...):
    db = _ctx_db.get()  # De onde veio? Quando foi setado?
    # Precisa rastrear ContextVar em múltiplos lugares
```

**Depois (fácil):**
```python
# Método de classe, contexto explícito no construtor
class AtendimentoHandler:
    def __init__(self, db, evolution):
        self._db = db  # Origem clara: veio do construtor
        self._evolution = evolution  # Rastreável
    
    async def _enviar_texto(self, at, msg):
        # self._db é 100% rastreável
        # Breakpoint aqui mostra exatamente o que é self._db
```

### Teste de Integração

```python
# tests/integration/test_bot_flow.py
@pytest.mark.asyncio
async def test_fluxo_completo_atendimento():
    """Testa fluxo inteiro: BOOT → LGPD → NOME → HUB → AT:MENU"""
    
    db = criar_db_teste()
    evolution = EvolutionApiClientMock()
    
    bot = BotMáquinaEstados(db, evolution, {
        "AT": AtendimentoHandler(db, evolution),
    })
    
    # Simula chegada de mensagem
    await bot.processar_mensagem_recebida(
        instance_nome="default",
        remote_jid="67999999999@s.whatsapp.net",
        push_name="João",
        msg_type="text",
        content="Olá",
    )
    
    # Verifica se progrediu para LGPD
    estado = bot._obter_estado(1)
    assert estado == "AGUARDAR_LGPD"
    
    # Simula aceite LGPD
    await bot.processar_mensagem_recebida(
        instance_nome="default",
        remote_jid="67999999999@s.whatsapp.net",
        push_name="João",
        msg_type="list_response",
        content="LGPD_ACEITO",
    )
    
    # Verifica se foi para NOME
    assert bot._obter_estado(1) == "AGUARDAR_NOME"
```

---

## Conclusão

Esta refatoração transforma `bot_service.py` de **1692 linhas procedurais** em uma arquitetura **OOP pura, testável e escalável**.

**Benefícios Conquistados:**
- ✅ Encapsulamento: Estado privado, interface pública clara
- ✅ Herança: Reutilização de código via classe base
- ✅ Polimorfismo: Cada handler implementa processar() diferente
- ✅ Abstração: Esconde complexidade, expõe apenas essencial
- ✅ Testabilidade: Sem ContextVar, dependências explícitas
- ✅ Manutenibilidade: 7 arquivos pequenos > 1 gigante
- ✅ Escalabilidade: Novo departamento = 1 classe nova
- ✅ Conformidade: Alinha com padrão Angular/TypeScript

**Alinhamento com Delphi:**
Se você desenvolveu em Delphi com OOP puro, essa arquitetura segue os mesmos princípios:
- Classes com atributos privados
- Métodos virtuais (polimorfismo)
- Interfaces abstratas
- Padrão Factory para injeção de dependência
