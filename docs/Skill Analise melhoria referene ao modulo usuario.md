================================================================================
SKILL: ANÁLISE, REVISÃO E IMPLEMENTAÇÃO DE MELHORIAS - ECOCHAT MARCX
ARQUIVO: skill_analise_melhorias_ecochat.txt
VERSÃO: 1.0.0
STACK ALVO: Angular 17+ (frontend) + Python/FastAPI (backend) - SEM JAVA
BASE DE ANÁLISE: Protótipo HTML "Cadastro de Usuários - EcoChat Marcx"
                 + capturas de referência do sistema em produção
                 (Usuários, Turnos de Trabalho, Departamentos, Abas de
                 Atendimento, filtros, paginação e formulários completos).
================================================================================

--------------------------------------------------------------------------------
1. OBJETIVO E INVOCACÃO
--------------------------------------------------------------------------------
Executar revisão estruturada das interfaces do EcoChat Marcx, produzindo:
  (a) Relatório de constatações (diagnóstico técnico e funcional);
  (b) Plano priorizado de melhorias (Crítico > Alto > Médio > Baixo);
  (c) Implementação das melhorias na stack Angular + Python.
triggers:
  - revisar/melhorar telas de usuários, turnos, departamentos ou canais
  - analisar lacunas (gap analysis) frente ao sistema de referência
  - refatorar protótipo HTML para Angular + API Python
  - auditar segurança, UX, acessibilidade e qualidade de código do painel

--------------------------------------------------------------------------------
2. ESCOPO DA ANÁLISE (AS-IS)
--------------------------------------------------------------------------------
MOD-01 Usuários        : formulário (foto, dados, tipo, departamento, canal,
                         senhas, status, conexões WhatsApp, turno) + lista com
                         filtros e agrupamento por departamento.
MOD-02 Turnos          : formulário com grade semanal de horários, ações para
                         novos atendimentos e mensagens + lista.
MOD-03 Departamentos   : formulário (nome, descrição, status) + lista.
MOD-04 Canais          : formulário (nome, ícone, descrição, arquivo de menu
                         HTML, status) + lista + diagrama conceitual de ponte.
MOD-05 Níveis de Acesso: presente no menu, NÃO implementado (fallback p/ alert).
MOD-06 Abas de Atendimento: presente na referência, AUSENTE no protótipo.

--------------------------------------------------------------------------------
3. METODOLOGIA (6 FASES)
--------------------------------------------------------------------------------
FASE 1 - Inventario AS-IS     : catalogar módulos, campos, ações e regras.
FASE 2 - Gap Analysis         : comparar com o sistema de referência (TO-BE).
FASE 3 - Revisão Técnica      : segurança, UX/acessibilidade, qualidade de
                                código, desempenho e arquitetura.
FASE 4 - Plano Priorizado     : classificar melhorias (Crítico/Alto/Médio/Baixo).
FASE 5 - Implementação        : Angular (componentes, guards, services) +
                                FastAPI (routers, modelos, migrações).
FASE 6 - Validação            : testes AAA (pytest/Jest) + checklist de regressão.

--------------------------------------------------------------------------------
4. DIAGNÓSTICO INICIAL (CONSTATAÇÕES DA BASELINE)
--------------------------------------------------------------------------------
ID    | SEV.    | CATEGORIA      | CONSTATAÇÃO
F-01  | Crítico | Segurança      | XSS: innerHTML com dados do usuário (nome/
      |         |                | usuario) sem escape em renderTabela/
      |         |                | renderDeptos/renderCanais.
F-02  | Crítico | Segurança      | Sem backend/autenticação: painel admin
      |         |                | aberto; validação apenas client-side; senha
      |         |                | sem hash (exige BCrypt + JWT).
F-03  | Alto    | Arquitetura    | Persistência em localStorage (cota ~5MB,
      |         |                | monocliente, sem concorrência); foto Base64
      |         |                | agrava a cota.
F-04  | Alto    | Bug            | Inconsistência de valores: selects hardcode
      |         |                | usam chaves kebab ('call-center'), mas
      |         |                | sincronizarSelects() substitui por nomes
      |         |                | ("Call-Center"); filtroDepto mantém chaves
      |         |                | antigas -> filtragem falha; contagens por
      |         |                | conversão frágil de strings.
F-05  | Alto    | Funcional      | Ausência de EDITAR usuário e REDEFINIR SENHA
      |         |                | (referência exibe botões lápis e chave);
      |         |                | existe apenas excluir.
F-06  | Médio   | Funcional      | Faltam, vs. referência: Último acesso,
      |         |                | Atividade (online/offline), filtros por
      |         |                | Usuário e Atividade, paginação com contador
      |         |                | "Listado X de Y usuário(s)".
F-07  | Médio   | Funcional      | Departamentos e Canais devem aceitar
      |         |                | múltipla seleção (referência); protótipo
      |         |                | é single-select.
F-08  | Médio   | Funcional      | "Níveis de Acesso" e "Abas de Atendimento"
      |         |                | não implementados.
F-09  | Médio   | UX/Acessib.    | Navegação por <div onclick> (sem teclado/
      |         |                | ARIA); confirm() nativo; sem validação por
      |         |                | campo; labels sem associação for/id.
F-10  | Médio   | Funcional      | Departamento (referência) possui campos
      |         |                | operacionais ausentes: retenção de
      |         |                | mensagens, finalizar inativos (horas), menu
      |         |                | de coleta, fila de atendimento, encerra
      |         |                | atendimento, turno vinculado, grupo/cód./
      |         |                | cliente.
F-11  | Baixo   | Qualidade      | HTML monolítico com JS/CSS inline; funções
      |         |                | globais; constantes duplicadas (HTML x JS);
      |         |                | estilos inline misturados a classes.
F-12  | Baixo   | Qualidade      | IDs via Date.now() (risco de colisão); stat
      |         |                | "st-conexoes" hardcoded.

--------------------------------------------------------------------------------
5. CATÁLOGO DE MELHORIAS (PLANO DE IMPLEMENTAÇÃO)
--------------------------------------------------------------------------------
M-01 (F-01) Angular: renderização 100% por data binding (sanitização nativa);
         proibido innerHTML com dados externos.
M-02 (F-02) FastAPI + JWT + BCrypt (skill engenharia-seguranca v3); validação
         server-side com Pydantic; perfis via exigir_role (PoLP).
M-03 (F-03) Banco real (PostgreSQL/SQLite) + Alembic; fotos como arquivo/
         storage com URL, nunca Base64 no registro.
M-04 (F-04) Fonte única de verdade: catálogos servidos pela API com
         id/valor/label; FKs normalizadas (departamento_id, canal_id).
M-05 (F-05) CRUD completo: PUT /api/usuarios/{id} e POST /api/usuarios/{id}/
         reset-senha; botões Editar e Chave na tabela.
M-06 (F-06) Paginação server-side (page/size) + filtros nome/usuário/status/
         atividade; colunas Último acesso e Atividade (heartbeat/presença).
M-07 (F-07) Multi-select com chips para Departamentos e Canais; relações N:N
         nos modelos (usuario_departamento, usuario_canal).
M-08 (F-08) Implementar rotas/páginas niveis-acesso e abas-atendimento.
M-09 (F-09) routerLink/botões reais, ARIA e foco visível; modal de confirmação
         no lugar de confirm(); Reactive Forms com erro por campo.
M-10 (F-10) Estender o modelo Departamento com os campos operacionais da
         referência (retenção, inatividade, coleta, fila, turno).
M-11 (F-11) Componentização Angular + design tokens (variáveis CSS); services
         compartilhados (Toast, Confirmação, Catálogos).
M-12 (F-12) UUIDs para identificadores; estatísticas calculadas no backend
         (GET /api/stats).

--------------------------------------------------------------------------------
6. ARQUITETURA ALVO
--------------------------------------------------------------------------------
FRONTEND (Angular):
  shell (sidebar + topbar)
  usuarios-lista | usuario-form (foto, multi-selects, conexões, turno)
  turnos | departamentos | canais | niveis-acesso | abas-atendimento
  shared: tabela-paginada, modal-confirmacao, toast, filtros, auth.*

BACKEND (Python/FastAPI):
  /api/auth          (login, refresh, logout - JWT/BCrypt)
  /api/usuarios      (CRUD + reset-senha + último acesso/atividade)
  /api/departamentos (CRUD + campos operacionais)
  /api/canais        (CRUD + vínculo a arquivo de menu)
  /api/turnos        (CRUD + grade semanal JSON)
  /api/niveis        (CRUD de papéis/permissões)
  /api/abas          (configuração de abas de atendimento)
  /api/conexoes      (números WhatsApp; status; QR Code)
  /api/stats         (contadores do topo)

MODELOS (SQLAlchemy):
  Usuario, Departamento, Canal, Turno, NivelAcesso, AbaAtendimento,
  ConexaoWhatsApp; N:N usuario<->departamento e usuario<->canal;
  FKs turno_id e conexao_padrao_id; campos ultimo_acesso e status_atividade.

--------------------------------------------------------------------------------
7. CHECKLIST DE REVISÃO (EXECUTAR A CADA ENTREGA)
--------------------------------------------------------------------------------
[ ] Sem XSS (ausência de innerHTML com dados externos)
[ ] Autenticação/autorização server-side (JWT + roles; PoLP)
[ ] Persistência real com migrações (Alembic); sem localStorage para dados
[ ] IDs UUID e catálogos normalizados (sem strings duplicadas)
[ ] CRUD completo, incluindo editar e redefinir senha
[ ] Filtros + paginação + contador "Listado X de Y"
[ ] Navegação por teclado e ARIA; modais acessíveis
[ ] Validação reativa por campo (mensagens específicas)
[ ] Paridade funcional com o sistema de referência
[ ] Testes AAA (pytest no backend; Jest no frontend)

--------------------------------------------------------------------------------
8. INTEGRAÇÃO COM AS SKILLS ANTERIORES
--------------------------------------------------------------------------------
- engenharia-seguranca-identidade v3 : JWT, BCrypt, headers, PoLP, segredos.
- testes-unitarios-aaa              : suíte AAA para services/routers.
- skill_11_modulos                  : padrão de sidebar com ícones e destaque
                                      do módulo ativo (identidade de navegação).

--------------------------------------------------------------------------------
9. ESTRUTURA DE ARQUIVOS DA SKILL
--------------------------------------------------------------------------------
skills/
└── analise-melhorias-ecochat/
    ├── SKILL.md
    ├── references/
    │   ├── diagnostico_baseline.md   (Seção 4)
    │   ├── catalogo_melhorias.md     (Seção 5)
    │   ├── arquitetura_alvo.md       (Seção 6)
    │   └── checklist_revisao.md      (Seção 7)
    └── templates/
        ├── relatorio_analise.txt
        └── plano_implementacao.txt
================================================================================