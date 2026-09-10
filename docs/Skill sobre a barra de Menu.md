================================================================================
SKILL: SISTEMA DE GESTÃO COM 11 MÓDULOS - MENU LATERAL DE ÍCONES
ARQUIVO: skill_11_modulos.txt
VERSÃO: 1.0.0
================================================================================

--------------------------------------------------------------------------------
1. ARQUITETURA DA SKILL
--------------------------------------------------------------------------------
A skill consiste em um menu lateral fixo com 11 ícones de navegação. Cada ícone,
ao ser clicado, invoca a função do módulo correspondente e carrega a interface
associada, conforme demonstrado nas telas entregues.

Características arquiteturas:
  - Barra lateral fixa (sidebar) contendo os 11 ícones, na ordem definida.
  - Área de conteúdo única, com troca de interface por invocação de função.
  - Destaque visual (azul) para o ícone do módulo ativo.
  - Identidade visual uniforme e textos em português em todas as telas.
  - Padrão de navegação: 1 ícone = 1 função = 1 interface.

--------------------------------------------------------------------------------
2. MAPEAMENTO DAS 11 FUNCIONALIDADES
--------------------------------------------------------------------------------

01) ÍCONE: Casa
    FUNÇÃO: modulo_dashboard
    INTERFACE: Painel de relatórios das ações executadas pelo programa.
               Indicadores: Ações executadas, Mensagens enviadas, Atendimentos
               realizados, Empresas ativas. Gráficos de ações por dia (linha e
               barras) e tabela "Relatório das ações executadas do programa"
               (Data, Módulo, Ação, Usuário, Status).

02) ÍCONE: Dois bonecos
    FUNÇÃO: modulo_usuarios
    INTERFACE: Tela de cadastro de usuários. Formulário "Novo Usuário": Nome
               completo, E-mail, Telefone, Perfil de acesso (Administrador,
               Atendente, Gestor) e Senha; botão "Salvar usuário". Listagem
               "Usuários cadastrados" com ações Editar e Desativar.

03) ÍCONE: Cartão de identificação
    FUNÇÃO: modulo_contatos
    INTERFACE: Cadastro de clientes/contatos vinculado à API do WhatsApp (selo
               "Integrado à API do WhatsApp"). Formulário "Novo Contato
               (Cliente)": Nome, Número WhatsApp, E-mail, Tags, Observações;
               botão "Salvar contato". Tabela "Contatos vinculados" (Nome,
               WhatsApp, Tags, Última mensagem, Status).

04) ÍCONE: Prédio
    FUNÇÃO: modulo_empresas
    INTERFACE: Cadastro da empresa contratante (que compra/paga o sistema).
               Formulário "Nova Empresa Contratante": Razão Social, CNPJ,
               E-mail administrativo, Plano (Mensal/Anual), Status de
               pagamento. Centralização administrativa: cada empresa que aluga
               o espaço vincula 1 ou vários números administrativos de
               WhatsApp, com botão "+ Adicionar número". Tabela "Empresas
               contratadas" (Empresa, CNPJ, Números vinculados, Plano, Status).

05) ÍCONE: Balões de chat
    FUNÇÃO: modulo_atendimento
    INTERFACE: Central de atendimento ao cliente. Conforme a configuração, os
               contatos dos clientes caem para a determinada empresa
               contratada. Composição: "Fila de contatos recebidos", painel de
               conversa (chat com campo de mensagem e botão de envio) e
               "Detalhes do contato" com a empresa contratada responsável.

06) ÍCONE: Envelope
    FUNÇÃO: modulo_mensagens
    INTERFACE: Caixa de mensagens. Lista de mensagens recebidas (Assunto e
               pré-visualização), painel de leitura ("Enviado em"), botões
               Responder e Arquivar, e botão "Nova mensagem".

07) ÍCONE: Relógio com seta
    FUNÇÃO: modulo_historico
    INTERFACE: Histórico/auditoria das ações executadas. Filtros por Período,
               Módulo e Usuário, com botão "Filtrar". Tabela: Data/Hora,
               Usuário, Módulo, Ação, Status; paginação ao final.

08) ÍCONE: Wi-Fi
    FUNÇÃO: modulo_conexao
    INTERFACE: Conexão com a API do WhatsApp (selo "API WhatsApp: Online").
               Cartões por número administrativo com status Conectado/
               Desconectado, botões "Desconectar" e "Conectar via QR Code",
               e painel com QR Code para vincular novo número administrativo.

09) ÍCONE: Calendário
    FUNÇÃO: modulo_agenda
    INTERFACE: Agenda mensal (Dom a Sáb) com marcadores de agendamentos e
               painel lateral "Próximos agendamentos". Botão "Novo
               agendamento".

10) ÍCONE: Avião de papel
    FUNÇÃO: modulo_envios
    INTERFACE: Disparos de mensagens/campanhas. Formulário "Nova campanha":
               Nome da campanha, Lista de contatos, Modelo de mensagem,
               Data/hora agendada; botão "Disparar campanha". Tabela de
               campanhas: Enviadas, Entregues, Falhas, Status (Ativa/
               Concluída).

11) ÍCONE: Pasta
    FUNÇÃO: modulo_arquivos
    INTERFACE: Gestor de arquivos. Pastas com contadores: Documentos, Mídias e
               Modelos de mensagem. Listagem de arquivos (ex.: contrato.pdf,
               logo.png, modelo-boasvindas.txt). Botão "Enviar arquivo".

--------------------------------------------------------------------------------
3. ESTRUTURA DE IMPLEMENTAÇÃO DA SKILL
--------------------------------------------------------------------------------

# Registro dos módulos da skill (ícone -> função)
SKILL_MODULOS = {
    "icone_casa":       modulo_dashboard,    # Relatórios das ações executadas
    "icone_usuarios":   modulo_usuarios,     # Cadastro de usuários
    "icone_contatos":   modulo_contatos,     # Cadastro de clientes (API WhatsApp)
    "icone_empresa":    modulo_empresas,     # Empresas contratantes + números adm.
    "icone_chat":       modulo_atendimento,  # Atendimento direcionado por configuração
    "icone_envelope":   modulo_mensagens,    # Caixa de mensagens
    "icone_relogio":    modulo_historico,    # Auditoria de ações
    "icone_wifi":       modulo_conexao,      # Conexão WhatsApp / QR Code
    "icone_calendario": modulo_agenda,       # Agenda de compromissos
    "icone_aviao":      modulo_envios,       # Disparos e campanhas
    "icone_pasta":      modulo_arquivos,     # Gestor de arquivos
}

def ao_clicar_icone(icone):
    """Carrega a interface do módulo correspondente ao ícone clicado."""
    modulo = SKILL_MODULOS[icone]
    return modulo.abrir_interface()

--------------------------------------------------------------------------------
4. REGRAS DE NEGÓCIO INCORPORADAS
--------------------------------------------------------------------------------
  - modulo_empresas: relação 1-N entre empresa e números administrativos de
    WhatsApp (a contratante pode possuir um ou vários números), com
    centralização por espaço alugado.
  - modulo_atendimento: o roteamento dos contatos dos clientes obedece à
    configuração da empresa contratada, exibindo a empresa responsável no
    painel de detalhes do contato.
  - modulo_conexao: vinculação de novos números administrativos exclusivamente
    via QR Code; controle de status Conectado/Desconectado por número.
  - modulo_usuarios: perfis de acesso (Administrador, Atendente, Gestor),
    aplicando separação de privilégios por papel.

--------------------------------------------------------------------------------
5. ANEXO - SUGESTÃO DE IMPLEMENTAÇÃO NA STACK ANGULAR + PYTHON
--------------------------------------------------------------------------------
Frontend (Angular): componente de sidebar com 11 botões e router-outlet.
Rotas sugeridas:
  /dashboard    -> DashboardComponent    (modulo_dashboard)
  /usuarios     -> UsuariosComponent     (modulo_usuarios)
  /contatos     -> ContatosComponent     (modulo_contatos)
  /empresas     -> EmpresasComponent     (modulo_empresas)
  /atendimento  -> AtendimentoComponent  (modulo_atendimento)
  /mensagens    -> MensagensComponent    (modulo_mensagens)
  /historico    -> HistoricoComponent    (modulo_historico)
  /conexao      -> ConexaoComponent      (modulo_conexao)
  /agenda       -> AgendaComponent       (modulo_agenda)
  /envios       -> EnviosComponent       (modulo_envios)
  /arquivos     -> ArquivosComponent     (modulo_arquivos)

Backend (Python/FastAPI): routers REST por módulo.
  /api/dashboard/relatorios      -> métricas e relatório de ações
  /api/usuarios                  -> CRUD de usuários e perfis
  /api/contatos                  -> CRUD de contatos (integração WhatsApp)
  /api/empresas                  -> CRUD de empresas + números administrativos
  /api/atendimento               -> fila, conversa e roteamento por empresa
  /api/mensagens                 -> caixa de mensagens (responder/arquivar)
  /api/historico                 -> consulta auditada com filtros
  /api/conexao                   -> status dos números e QR Code de vínculo
  /api/agenda                    -> agendamentos e próximos compromissos
  /api/envios                    -> campanhas e métricas de disparo
  /api/arquivos                  -> upload e listagem de arquivos

--------------------------------------------------------------------------------
6. ESTRUTURA DE ARQUIVOS SUGERIDA
--------------------------------------------------------------------------------
skills/
└── skill_11_modulos/
    ├── SKILL.md
    ├── frontend_angular/
    │   ├── sidebar.component.ts
    │   ├── app.routes.ts
    │   └── modulos/ (11 componentes, um por módulo)
    └── backend_python/
        └── routers/ (11 routers, um por módulo)

--------------------------------------------------------------------------------
7. NOTAS FINAIS
--------------------------------------------------------------------------------
  - As onze telas entregues constituem os protótipos visuais de cada função,
    mantendo identidade visual uniforme e destaque azul para o módulo ativo.
  - A navegação é determinística: cada ícone invoca exatamente uma função e
    carrega exatamente uma interface.
================================================================================