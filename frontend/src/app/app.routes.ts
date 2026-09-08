//╔══════════════════════════════════════════════════════════════════════════════╗
// ║  PROJETO.......: EcoChatBotMarcx — Sistema de Atendimento Digital          ║
// ║  ARQUIVO.......: app.routes.ts                                             ║
// ║  LOCALIZAÇÃO...: Frontend/App/app.routes.ts                                ║
// ║  AUTOR.........: Ademir Queiroz                                            ║
// ║  DATA..........: 08/09/2026                                                ║
// ║  VERSÃO........: 1.0.0                                                     ║
// ║                                                                            ║
// ║  DESCRIÇÃO                                                                 ║
// ║  Configuração moderna de rotas usando o padrão standalone do Angular 17+.  ║
// ║  Define toda a navegação do sistema:                                       ║
// ║    • Login (público)                                                       ║
// ║    • Painel administrativo (protegido por authGuard)                       ║
// ║    • Interface pública de chat do cliente/paciente                         ║
// ║                                                                            ║
// ║  DIFERENÇA PARA app-routing.module.ts:                                     ║
// ║    • Não utiliza @NgModule                                                 ║
// ║    • Usa loadComponent() ao invés de loadChildren()                        ║
// ║    • Registra rotas via provideRouter() no main.ts                         ║
// ║    • É o padrão recomendado a partir do Angular 17                         ║
// ╚══════════════════════════════════════════════════════════════════════════════╝


// ─────────────────────────────────────────────────────────────────────────────
// IMPORTAÇÕES
// ─────────────────────────────────────────────────────────────────────────────
import { Routes } from '@angular/router';
//   Routes → interface TypeScript que define o formato do array de rotas.
//   Fornece autocomplete e validação em tempo de compilação.

import { authGuard } from './core/guards/auth.guard';
//   authGuard → função de guarda de rota.
//   Verifica se o usuário está autenticado antes de permitir o acesso.
//   Se não estiver autenticado, redireciona para /login.
//
//   GUARDS (canActivate, canDeactivate, canLoad):
//     São funções/métodos que executam lógica ANTES da ativação da rota.
//     Retornam:
//       true            → permite a navegação
//       false           → bloqueia a navegação
//       UrlTree         → redireciona para outra URL
//       Observable/Promise dos valores acima → versão assíncrona


// ─────────────────────────────────────────────────────────────────────────────
// ARRAY DE ROTAS
// ─────────────────────────────────────────────────────────────────────────────
// O "export const" torna a constante acessível para importação em outros
// arquivos (como o main.ts, que a registra via provideRouter(routes)).
// ─────────────────────────────────────────────────────────────────────────────
export const routes: Routes = [

  // ── ROTA RAIZ ─────────────────────────────────────────────────────────────
  { path: '', redirectTo: 'admin/dashboard', pathMatch: 'full' },


  // ─────────────────────────────────────────────────────────────────────────
  // LOGIN — Rota pública
  // ─────────────────────────────────────────────────────────────────────────
  // URL: http://dominio/login
  // Acesso: qualquer pessoa (sem autenticação necessária)
  //
  // loadComponent() → carrega o componente sob demanda (lazy loading).
  //   Diferente de loadChildren() que carrega um módulo inteiro,
  //   loadComponent() carrega apenas UM componente específico.
  //
  // title → define o título da aba do navegador (<title>).
  // ─────────────────────────────────────────────────────────────────────────
  {
    path: 'login',
    loadComponent: () =>
      import('./pages/login/login.component')
        .then(m => m.LoginComponent),
    title: 'Login — EcoChatBotMarcx'
  },


  // ─────────────────────────────────────────────────────────────────────────
  // ADMIN — Rotas protegidas por autenticação
  // ─────────────────────────────────────────────────────────────────────────
  // URL: http://dominio/admin/*
  // Acesso: apenas usuários autenticados (verificado pelo authGuard)
  //
  // canActivate: [authGuard]
  //   Array de guards executados ANTES da ativação da rota.
  //   Se authGuard retornar false, o usuário é redirecionado para /login.
  //
  // loadComponent() → carrega o AdminLayoutComponent, que contém:
  //   • Sidebar (menu lateral)
  //   • Topbar (barra superior)
  //   • <router-outlet> interno para as rotas filhas
  //
  // children → array de rotas filhas, renderizadas DENTRO do layout admin.
  // ─────────────────────────────────────────────────────────────────────────
  {
    path: 'admin',
    canActivate: [authGuard],
    loadComponent: () =>
      import('./shared/components/admin-layout/admin-layout.component')
        .then(m => m.AdminLayoutComponent),
    children: [

      // ── DASHBOARD ───────────────────────────────────────────────────────
      // URL: http://dominio/admin/dashboard
      {
        path: 'dashboard',
        loadComponent: () =>
          import('./pages/admin/dashboard/dashboard.component')
            .then(m => m.DashboardComponent),
        title: 'Dashboard — EcoChatBotMarcx'
      },

      // ── ATENDIMENTOS ────────────────────────────────────────────────────
      // URL: http://dominio/admin/atendimentos
      {
        path: 'atendimentos',
        loadComponent: () =>
          import('./pages/admin/atendimentos/atendimentos.component')
            .then(m => m.AtendimentosComponent),
        title: 'Atendimentos — EcoChatBotMarcx'
      },

      // ── USUÁRIOS ────────────────────────────────────────────────────────
      // URL: http://dominio/admin/usuarios
      {
        path: 'usuarios',
        loadComponent: () =>
          import('./pages/admin/usuarios/usuarios.component')
            .then(m => m.UsuariosComponent),
        title: 'Usuários — EcoChatBotMarcx'
      },

      // ── DEPARTAMENTOS ───────────────────────────────────────────────────
      // URL: http://dominio/admin/departamentos
      {
        path: 'departamentos',
        loadComponent: () =>
          import('./pages/admin/departamentos/departamentos.component')
            .then(m => m.DepartamentosComponent),
        title: 'Departamentos — EcoChatBotMarcx'
      },

      // ── CANAIS DE ATENDIMENTO ───────────────────────────────────────────
      // URL: http://dominio/admin/canais
      {
        path: 'canais',
        loadComponent: () =>
          import('./pages/admin/canais/canais.component')
            .then(m => m.CanaisComponent),
        title: 'Canais de Atendimento — EcoChatBotMarcx'
      },

      // ── CONEXÕES ────────────────────────────────────────────────────────
      // URL: http://dominio/admin/conexoes
      {
        path: 'conexoes',
        loadComponent: () =>
          import('./pages/admin/conexoes/conexoes.component')
            .then(m => m.ConexoesComponent),
        title: 'Conexões — EcoChatBotMarcx'
      },

      // ── CONTATOS ────────────────────────────────────────────────────────
      // URL: http://dominio/admin/contatos
      {
        path: 'contatos',
        loadComponent: () =>
          import('./pages/admin/contatos/contatos.component')
            .then(m => m.ContatosComponent),
        title: 'Contatos — EcoChatBotMarcx'
      },

      // ── E-MAIL ──────────────────────────────────────────────────────────
      // URL: http://dominio/admin/email
      {
        path: 'email',
        loadComponent: () =>
          import('./pages/admin/email/email.component')
            .then(m => m.EmailComponent),
        title: 'E-mail — EcoChatBotMarcx'
      },

      // ── CAMPANHAS ───────────────────────────────────────────────────────
      // URL: http://dominio/admin/campanhas
      {
        path: 'campanhas',
        loadComponent: () =>
          import('./pages/admin/campanhas/campanhas.component')
            .then(m => m.CampanhasComponent),
        title: 'Campanhas — EcoChatBotMarcx'
      },

      // ── ARQUIVOS ────────────────────────────────────────────────────────
      // URL: http://dominio/admin/arquivos
      {
        path: 'arquivos',
        loadComponent: () =>
          import('./pages/admin/arquivos/arquivos.component')
            .then(m => m.ArquivosComponent),
        title: 'Arquivos — EcoChatBotMarcx'
      },

      // ── MENSAGENS ───────────────────────────────────────────────────────
      // URL: http://dominio/admin/mensagens
      {
        path: 'mensagens',
        loadComponent: () =>
          import('./pages/admin/mensagens/mensagens.component')
            .then(m => m.MensagensComponent),
        title: 'Mensagens — EcoChatBotMarcx'
      },

      // ── NÍVEIS DE USUÁRIO ───────────────────────────────────────────────
      // URL: http://dominio/admin/niveis
      {
        path: 'niveis',
        loadComponent: () =>
          import('./pages/admin/niveis/niveis.component')
            .then(m => m.NiveisComponent),
        title: 'Níveis de Usuário — EcoChatBotMarcx'
      },

      // ── ESCALAS ─────────────────────────────────────────────────────────
      // URL: http://dominio/admin/escalas
      {
        path: 'escalas',
        loadComponent: () =>
          import('./pages/admin/escalas/escalas.component')
            .then(m => m.EscalasComponent),
        title: 'Painel de Escalas — EcoChatBotMarcx'
      },

      // ── RELATÓRIO ───────────────────────────────────────────────────────
      // URL: http://dominio/admin/relatorio
      {
        path: 'relatorio',
        loadComponent: () =>
          import('./pages/admin/relatorio/relatorio.component')
            .then(m => m.RelatorioComponent),
        title: 'Relatório — EcoChatBotMarcx'
      }
    ]
  },


  // ─────────────────────────────────────────────────────────────────────────
  // CHAT — Interface pública do cliente/paciente
  // ─────────────────────────────────────────────────────────────────────────
  // URL: http://dominio/chat/*
  // Acesso: público (sem autenticação)
  //
  // Esta seção expõe a interface de atendimento para o cliente final.
  // O cliente acessa via link/QR Code fornecido pelo bot do WhatsApp.
  // ─────────────────────────────────────────────────────────────────────────
  {
    path: 'chat',
    children: [

      // ── MENU PRINCIPAL DO CHAT ──────────────────────────────────────────
      // URL: http://dominio/chat/menu
      // Exibe as opções de atendimento disponíveis.
      {
        path: 'menu',
        loadComponent: () =>
          import('./pages/chat/hub-menu/hub-menu.component')
            .then(m => m.HubMenuComponent),
        title: 'Atendimento — EcoChatBotMarcx'
      },

      // ── ATENDIMENTO POR CANAL ───────────────────────────────────────────
      // URL: http://dominio/chat/:canal
      //   Exemplos:
      //     /chat/portaria
      //     /chat/agendamento-ambulatorial
      //     /chat/financeiro
      //
      // :canal → PARÂMETRO DE ROTA (route parameter).
      //   O valor após /chat/ é capturado e disponibilizado via ActivatedRoute.
      //
      //   No componente, para acessar o parâmetro:
      //     constructor(private route: ActivatedRoute) { }
      //     this.route.params.subscribe(p => console.log(p['canal']));
      //
      //   Ou usando signal (Angular 16+):
      //     canal = toSignal(this.route.paramMap).pipe(
      //       map(params => params.get('canal'))
      //     );
      {
        path: ':canal',
        loadComponent: () =>
          import('./pages/chat/atendimento/atendimento.component')
            .then(m => m.AtendimentoComponent)
      }
    ]
  },


  // ── WILDCARD (catch-all) ──────────────────────────────────────────────────
  // path: '**' → casa com qualquer URL não mapeada.
  // SEMPRE deve ser a última rota do array.
  { path: '**', redirectTo: 'admin/dashboard' }
];