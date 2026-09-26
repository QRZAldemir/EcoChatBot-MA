# Estudo de Caso — Contratação de Canais por Telefone

> Documento de referência do modelo de negócio. Descreve a regra de contratação
> de canais e o que já está implementado no EcoChatBot-MA.

---

## 1. O caso

Uma empresa compradora tem **um** número de telefone, por exemplo `556734167800`.
Ao contratar o sistema, vincula esse número e contrata os canais que deseja —
por exemplo **WhatsApp e Telegram** — usando **o mesmo número** nos dois.

Ao contratar para um **segundo número** (`5567992469894`), os canais daquele
número são acrescidos e a mensalidade é duplicada.

### 1.1 Cenário válido

| Telefone       | whatsapp | pabx | discord | telegram |
|----------------|----------|------|---------|----------|
| 556734167800   | 1        | 1    | 1       | 1        |
| 5567992469894  | 1        | 1    | 1       | 1        |

Uma empresa com dois números pode ter **dois** WhatsApp, **dois** PABX,
**dois** Discord. Isso **não** é bloqueado.

### 1.2 Cenário inválido

| Telefone       | whatsapp | pabx | discord |
|----------------|----------|------|---------|
| 556734167800   | **2**    | 1    | 1       |

O mesmo número **não** pode estar em dois canais do mesmo tipo.
Isso **é** bloqueado.

### 1.3 Invariante

> O par **(telefone, tipo)** é único.
>
> Para cada telefone distintos: no máximo **1** canal de cada tipo.
> Para cada empresa: **N** telefones → **N** canais de cada tipo.

Um mesmo número **pode** atender canais de **tipos diferentes**
(whatsapp + telegram + discord no mesmo telefone).

---

## 2. Conceitos — não confundir

| Conceito            | Significado                                                                 | Onde mora                       |
|---------------------|-----------------------------------------------------------------------------|---------------------------------|
| **Canal / tipo**    | A **tecnologia** pela qual o cliente entra em contato: WhatsApp, Telegram, PABX, Discord, Facebook, Instagram | `enums.TipoCanalMensageria`      |
| **Canal contratado**| O **produto** que a empresa compra, vinculado a um telefone                 | `CanalContratado`               |
| **Menu / MenuItem** | O **modelo de negócio da empresa** apresentado ao cliente (menu visual ou URA) | `Menu`, `MenuItem`              |
| **Departamento**   | O **destino do atendimento** escolhido pelo cliente no menu                 | `Departamento`                  |

**Canal não é referência de departamento.** São eixos independentes:

```
Cliente entra pelo Canal (tecnologia)
        │
        ▼
Menu da empresa  ──►  MenuItem  ──►  Departamento  ──►  Atendente
   (canal_contratado_id)  (departamento_id)
```

O `Menu` pode ser por empresa (`empresa_id`) ou específico de um canal
(`canal_contratado_id`) — é o **MenuItem** que aponta o departamento.
Nunca o canal.

---

## 3. O que está implementado

### 3.1 Canal contratado

`app/models/canal_models.py` — `CanalContratado` (`canais_contratados`)

- `empresa_id` → FK `empresas.id`, `ondelete=CASCADE`, index
- `tipo` → `String(20)` — `whatsapp | telegram | instagram | facebook | pabx | discord | email`
- `apelido` → `String(80)` — ex.: "WhatsApp Comercial", "Telegram Suporte"
- `credenciais` → `Text` (JSON) — ex.: `{"phone_id": "...", "token": "..."}`
- `webhook_token` → `String(120)`, index
- `webhook_url` → `String(300)`
- `horario_inicio` / `horario_fim` → `String(5)`; `dias_semana` → `String(20)`
- `ativo` → `Boolean`, default `True`
- Mixins: `TimestampMixin`, `SoftDeleteMixin`, `TenantMixin`
- Relações: `empresa`, `conexoes`, `menus`, `atendimentos`

Regras já descritas no próprio model:
- Webhook de canal não contratado é **rejeitado com 403**
- Soft delete: desativar o contrato **não** apaga o histórico de mensagens

### 3.2 Tipos de canal

`app/models/enums.py` — `TipoCanalMensageria` (9 valores, str):
`whatsapp`, `telegram`, `discord`, `instagram`, `facebook`, `pabx`, `email`,
`webchat`, `sms`

### 3.3 Menu e destino

- `Menu` — `empresa_id`, `canal_contratado_id` (nullable), `saudacao`, `rodape`,
  `tempo_espera_seg` (300), `tentativas_max` (3), `fallback_departamento_id`, `ativo`
- `MenuItem` — `departamento_id` **NOT NULL**, `roteiro_id` (nullable),
  `transfere_direto` (bool)
- `Departamento` — `empresa_id`, `ativo`
- `Atendimento` — `departamento_id`, `atendente_id`
- `AtendimentoTransferir` (`schemas/atendimento_schemas.py`) —
  `{usuario_id, departamento_id?, canal_id?}`

O mesmo `Menu` serve ao menu visual e à URA; muda apenas o `tipo` do
`canal_contratado`.

---

## 4. O que NÃO está implementado

### 4.1 ~~O telefone não é entidade~~  → **RESOLVIDO em 2026-09-26**

> **Correção:** esta seção descrevia o estado ANTES da implementação.
> O telefone passou a ser entidade — ver seção 7.

### 4.1 (histórico) O telefone não era entidade  ← bloqueava a regra principal

Não existe model de telefone. O número aparece solto e sem vínculo:

| Local                                | Campo                   |
|--------------------------------------|-------------------------|
| `empresa_models.py:88`               | `telefone: String(20)`  |
| `empresa_models.py:128`              | `telefone: String(20)`  |
| `usuario_models.py:133`              | `telefone: String(20)`  |
| `contato_models.py:75`               | `telefone: String(20)`  |
| `cliente_models.py:76`               | `telefone: String(20)`  |

`canais_contratados` **não tem coluna de telefone**. Para o banco,
`556734167800` e `5567992469894` são indistinguíveis.

### 4.2 A constraint está no eixo errado

```
uq_canais_contratados_empresa_tipo   →  UNIQUE (empresa_id, tipo)
```

Bloqueia o 2º WhatsApp da mesma empresa **mesmo havendo 2º número**.
É a regra `(telefone, tipo)` que precisa existir, e ela **não é representável
hoje** porque o telefone não é referência.

### 4.3 Não há mensalidade  → **PARCIALMENTE RESOLVIDO em 2026-09-26**

> **Correção:** em 2026-09-26 afirmei que "o teto de canais não existe em
> lugar nenhum". **Estava errado.** O limite existe, em `clientes`:
>
> | Campo              | Default | Onde                      |
> |--------------------|---------|---------------------------|
> | `limite_empresas`  | 1       | `cliente_models.py:85`    |
> | `limite_usuarios`  | 5       | `cliente_models.py:86`    |
> | `limite_canais`    | 2       | `cliente_models.py:87`    |
>
> O que é verdade: o limite é um **número por tenant**, não é derivado do
> `PlanoTenant` (`free|basic|pro|enterprise` não carrega limites), e o
> docstring do model diz que `limite_*` é "validado em serviço, não no ORM".
> Ou seja: o teto de 1 a 5 é **configurável por cliente**, não fixo por plano.
>
> O que segue em aberto: **não existe valor, preço nem cobrança.** A
> estrutura do contrato foi criada (seção 7), mas o modelo comercial de
> mensalidade continua por definir.

### 4.4 Colisão de tipo de canal

Dois enums com o mesmo nome e tipos incompatíveis:

| Local                            | Classe              | Tipo | Membros                                  |
|----------------------------------|---------------------|------|------------------------------------------|
| `models/enums.py:82`             | `TipoCanalMensageria`| str  | 9 canais                                 |
| `schemas/atendimento_schemas.py:26` | `TipoCanal`      | int  | `WHATSAPP=1`, `INTERNO=2`                |

`AtendimentoResponse.tipo_canal` está anotado como `int`, apontando para o
enum errado. Se ambos forem reexportados em `app/schemas/__init__.py`, um
sobrescreve o outro silenciosamente.

### 4.5 `CanalBase` referencia departamento  ← contraria o conceito

`app/schemas/canal_schemas.py` define `departamento_id` dentro de `CanalBase`.
Isso implica que o canalAponta para um departamento, o que **não** acontece no
modelo de negócio: o destino vem do `MenuItem`.

### 4.6 Transferência por canal não tem histórico

`AtendimentoTransferir` não registra `departamento_origem_id` nem `motivo`.
Não há como auditar "a Xmaira foi transferida de Agendamento para Exames".

---

## 5. Perguntas em aberto (decisão de negócio)

1. O teto de canais é **fixo** (1 a 5 para toda empresa) ou **por plano**
   (`free`=1 … `enterprise`=5)?
2. O preço por canal é de **tabela** ou **negociado por empresa**?
3. O canal `pabx` usa o **mesmo número** da empresa ou número do provedor
   (Twilio/Zenvia/Totalvoice)?
4. A empresa pode ter o mesmo número em **canais de tipos diferentes** —
   confirmado no caso. E em **tipos iguais** com números distintos — confirmado.

---

## 6. Glossário

| Termo            | Significado                                        |
|------------------|----------------------------------------------------|
| Canal            | Tecnologia de contato do cliente                   |
| Canal contratado | Produto que a empresa compra                       |
| Número           | Telefone da empresa, vincula os canais contratados |
| Menu             | Roteiro de opções que a empresa define             |
| MenuItem         | Opção do menu → destino (departamento)             |
| Departamento      | Destino do atendimento                             |
| URA              | Versão falada do menu, para telefone               |

---

## 7. Implementado em 2026-09-26

### 7.1 Telefone como entidade

`app/models/telefone_models.py` — `Telefone` (`telefones`)
`UNIQUE (empresa_id, numero)`; `numero` em E.164; `pais`; `principal`; `ativo`.

### 7.2 Contratação por telefone

`app/models/canal_models.py` — `CanalContratado`
- nova coluna `telefone_id` (NOT NULL, FK `telefones.id`, CASCADE)
- unicidade trocada: `UNIQUE (empresa_id, tipo)` → **`UNIQUE (telefone_id, tipo)`**
- nome da constraint: `uq_canais_contratados_telefone_tipo`

### 7.3 Assinatura (estrutura, sem cobrança)

`app/models/assinatura_models.py` — `assinaturas`
`plano`, `status`, `valor_base`, vigência, `observacoes`.
Sem regra de cálculo: o valor por canal contratado **não** é computado.

### 7.4 Histórico de transferências

`app/models/transferencia_models.py` — `transferencias`
Origem e destino (departamento, usuário, ramal), `menu_item_id`, `canal_contratado_id`,
`tipo` (`menu|atendente|ramal|sistema`), `motivo`, `transferido_em`.

**Append-only** — não herda `SoftDeleteMixin`. Um histórico que pode ser apagado
não é histórico.

### 7.5 Colisão `TipoCanal` resolvida

`app/schemas/atendimento_schemas.py` não define mais um `TipoCanal(int)` local.
Passa a usar `TipoCanalMensageria` (`app/models/enums.py`), com os 9 canais.
`AtendimentoResponse.tipo_canal` deixou de ser `int`.

`AtendimentoTransferir` passou a aceitar `motivo`, `departamento_origem_id`,
`menu_item_id` e `ramal_destino` — o necessário para registrar a transferência.

### 7.6 Bugs de ORM corrigidos (pré-existentes)

Estes bugs impediam qualquer uso do ORM — `configure_mappers()` falhava:

| Arquivo                      | Problema                                              | Correção                        |
|------------------------------|-------------------------------------------------------|---------------------------------|
| `empresa_models.py`          | faltava `canais_contratados`, exigido por `back_populates` | relationship adicionada     |
| `canal_models.py`            | faltava relationship `cliente`                        | relationship adicionada         |
| `cliente_models.py`          | `canais_mensageria` apontava para `CanalMensageria`, classe que não existe mais | passou a `canais_contratados` / `CanalContratado` |

### 7.7 Migration

`backend/migrations/009_telefones_e_historico_transferencias.sql` — **gerada, NÃO executada.**

Observação: o projeto **não usa Alembic** (`alembic/versions/` está vazio e não
existe tabela `alembic_version`). As migrações são `.sql` manuais. O dialeto
nesse diretório está inconsistente: `007` usa MySQL (`ADD COLUMN ... AFTER`),
`008` usa PostgreSQL (`GENERATED ... AS IDENTITY`) e **nenhum dos dois roda no
SQLite**, que é o banco de dev. A 009 foi escrita em SQL portátil e validada
em SQLite 3.37.
