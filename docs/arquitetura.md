# EcoChat Mackenzie — Arquitetura do Sistema

## Visão Geral

Sistema de atendimento inteligente para o Hospital Mackenzie, com suporte a múltiplos canais, departamentos e integração com IA (DeepSeek).

---

## Estrutura de Dados Principal

```
Usuário
 ├── nivel: atendente | supervisor | gerente | administrador
 ├── departamento → Departamento (ex: Call-Center, Recepção, Ouvidoria)
 └── canal → Canal (ex: Portaria, Atendimento-Cliente)
                └── arquivoMenu → "7portaria-mackenzie.html"
```

### Exemplos reais cadastrados:
| Usuário   | Nível      | Departamento | Canal                   | Arquivo Menu                          |
|-----------|------------|--------------|-------------------------|---------------------------------------|
| Aldemir   | Atendente  | Call-Center  | Exames-Diagnostico      | 3examesdiagnostico-mackenzie.html     |
| Ana       | Atendente  | Call-Center  | Atendimento-Cliente     | 1atendimento-mackenzie.html           |
| João      | Atendente  | Recepção     | Portaria                | 7portaria-mackenzie.html              |
| Francisca | Atendente  | Ouvidoria    | Ouvidoria               | 8ouvidoria-mackenzie.html             |
| Daniele   | Atendente  | Call-Center  | Agendamento-Ambulatorial| 2agendamento-mackenzie.html           |

---

## Estrutura de Pastas

```
EcoChatMackenize/
├── frontend/                      # Angular 17 (standalone components)
│   └── src/app/
│       ├── core/
│       │   ├── models/            # TypeScript interfaces
│       │   │   ├── usuario.model.ts
│       │   │   ├── departamento.model.ts
│       │   │   ├── canal.model.ts
│       │   │   └── nivel-usuario.model.ts
│       │   └── services/          # Comunicação com API
│       │       ├── usuario.service.ts
│       │       ├── departamento.service.ts
│       │       ├── canal.service.ts
│       │       └── deepseek.service.ts
│       ├── pages/
│       │   ├── admin/
│       │   │   ├── usuarios/      # CRUD usuários (agrupado por depto)
│       │   │   ├── departamentos/ # CRUD departamentos
│       │   │   ├── canais/        # CRUD canais + vínculo com arquivo menu
│       │   │   ├── niveis/        # CRUD níveis de acesso
│       │   │   └── relatorio/     # Relatórios
│       │   └── chat/
│       │       ├── hub-menu/      # Menu principal (cliente CLICA, não digita)
│       │       └── atendimento/   # Chat por canal
│       └── app.routes.ts          # Roteamento lazy-load
│
├── backend/                       # Java 21 + Quarkus 3.9
│   └── src/main/java/.../
│       ├── model/                 # Entidades JPA
│       │   ├── Usuario.java
│       │   ├── Departamento.java
│       │   └── Canal.java
│       ├── resource/              # REST endpoints
│       │   ├── UsuarioResource.java    → /api/usuarios
│       │   ├── CanalResource.java      → /api/canais
│       │   ├── DepartamentoResource.java → /api/departamentos
│       │   └── IAResource.java         → /api/ia/opcao
│       └── service/
│           ├── UsuarioService.java
│           └── DeepSeekService.java    # Integração DeepSeek API
│
├── prototipos/                    # HTMLs originais (referência visual)
└── docs/                          # Documentação
```

---

## Fluxo do Cliente (Chat)

```
1. Cliente acessa /chat/menu
2. HubMenuComponent carrega canais ativos via GET /api/canais
3. Cliente CLICA em uma opção (ex: 📞 Atendimento-Cliente)
4. Sistema navega para /chat/atendimento?canal=1
5. AtendimentoComponent carrega perguntas do canal
6. Cliente CLICA nas perguntas (não digita)
7. POST /api/ia/opcao → DeepSeekService → resposta IA
```

---

## APIs Necessárias

| Endpoint                     | Método | Descrição                       |
|------------------------------|--------|---------------------------------|
| /api/usuarios                | GET    | Listar com filtros              |
| /api/usuarios                | POST   | Criar usuário                   |
| /api/usuarios/{id}           | PUT    | Atualizar usuário               |
| /api/usuarios/{id}           | DELETE | Excluir usuário                 |
| /api/departamentos           | GET    | Listar departamentos            |
| /api/departamentos           | POST   | Criar departamento              |
| /api/canais                  | GET    | Listar canais                   |
| /api/canais                  | POST   | Criar canal                     |
| /api/ia/opcao                | POST   | IA responde opção do menu       |

---

## Como Iniciar o Ambiente de Desenvolvimento

### Pré-requisitos
```bash
# Node.js 20+ e Angular CLI
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs
npm install -g @angular/cli

# Java 21
sudo apt install -y openjdk-21-jdk

# Maven
sudo apt install -y maven

# PostgreSQL
sudo apt install -y postgresql
sudo -u postgres createdb ecochat_mackenzie
sudo -u postgres psql -c "CREATE USER ecochat WITH PASSWORD 'ecochat123';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE ecochat_mackenzie TO ecochat;"
```

### Iniciar Backend (Quarkus)
```bash
cd backend
export DEEPSEEK_API_KEY=sua_chave_aqui
mvn quarkus:dev
# Disponível em http://localhost:8080
```

### Iniciar Frontend (Angular)
```bash
cd frontend
npm install
ng serve
# Disponível em http://localhost:4200
```

---

## Próximas Etapas (Roadmap)

- [ ] Etapa 1: Configurar ambiente (Node + Java + PostgreSQL)
- [ ] Etapa 2: Completar CRUD de Usuários/Departamentos/Canais no Angular
- [ ] Etapa 3: Implementar REST Client DeepSeek no Quarkus
- [ ] Etapa 4: Interface de chat com clique nas opções (hub-menu)
- [ ] Etapa 5: Autenticação JWT (login por usuário/senha)
- [ ] Etapa 6: Dashboard e relatórios
- [ ] Etapa 7: Integração futura com Chatwoot (webhook)
- [ ] Etapa 8: Personalização para outros modelos de negócio (multi-tenant)
