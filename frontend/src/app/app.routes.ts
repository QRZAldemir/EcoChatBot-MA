<<<<<<< HEAD
import { Routes } from '@angular/router';
import { authGuard } from './core/guards/auth.guard';
import { nivelGuard } from './core/guards/nivel.guard';
=======
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
>>>>>>> 37038798148d95e3284b5959b5d7ab66266a4507


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
<<<<<<< HEAD
        canActivate: [nivelGuard],
        data: { nivelMinimo: 'atendente' },
        loadComponent: () => import('./pages/admin/atendimentos/atendimentos.component').then(m => m.AtendimentosComponent),
        title: 'Atendimentos — EcoChat Marcx'
      },
      {
        path: 'usuarios',
        canActivate: [nivelGuard],
        data: { nivelMinimo: 'supervisor' },
        loadComponent: () => import('./pages/admin/usuarios/usuarios.component').then(m => m.UsuariosComponent),
        title: 'Usuários — EcoChat Marcx'
=======
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
>>>>>>> 37038798148d95e3284b5959b5d7ab66266a4507
      },

      // ── DEPARTAMENTOS ───────────────────────────────────────────────────
      // URL: http://dominio/admin/departamentos
      {
        path: 'departamentos',
<<<<<<< HEAD
        canActivate: [nivelGuard],
        data: { nivelMinimo: 'gerente' },
        loadComponent: () => import('./pages/admin/departamentos/departamentos.component').then(m => m.DepartamentosComponent),
        title: 'Departamentos — EcoChat Marcx'
=======
        loadComponent: () =>
          import('./pages/admin/departamentos/departamentos.component')
            .then(m => m.DepartamentosComponent),
        title: 'Departamentos — EcoChatBotMarcx'
>>>>>>> 37038798148d95e3284b5959b5d7ab66266a4507
      },

      // ── CANAIS DE ATENDIMENTO ───────────────────────────────────────────
      // URL: http://dominio/admin/canais
      {
        path: 'canais',
<<<<<<< HEAD
        canActivate: [nivelGuard],
        data: { nivelMinimo: 'gerente' },
        loadComponent: () => import('./pages/admin/canais/canais.component').then(m => m.CanaisComponent),
        title: 'Canais de Atendimento — EcoChat Marcx'
=======
        loadComponent: () =>
          import('./pages/admin/canais/canais.component')
            .then(m => m.CanaisComponent),
        title: 'Canais de Atendimento — EcoChatBotMarcx'
>>>>>>> 37038798148d95e3284b5959b5d7ab66266a4507
      },

      // ── CONEXÕES ────────────────────────────────────────────────────────
      // URL: http://dominio/admin/conexoes
      {
        path: 'conexoes',
<<<<<<< HEAD
        canActivate: [nivelGuard],
        data: { nivelMinimo: 'administrador' },
        loadComponent: () => import('./pages/admin/conexoes/conexoes.component').then(m => m.ConexoesComponent),
        title: 'Conexões — EcoChat Marcx'
=======
        loadComponent: () =>
          import('./pages/admin/conexoes/conexoes.component')
            .then(m => m.ConexoesComponent),
        title: 'Conexões — EcoChatBotMarcx'
>>>>>>> 37038798148d95e3284b5959b5d7ab66266a4507
      },

      // ── CONTATOS ────────────────────────────────────────────────────────
      // URL: http://dominio/admin/contatos
      {
        path: 'contatos',
<<<<<<< HEAD
        canActivate: [nivelGuard],
        data: { nivelMinimo: 'gerente' },
        loadComponent: () => import('./pages/admin/contatos/contatos.component').then(m => m.ContatosComponent),
        title: 'Contatos — EcoChat Marcx'
=======
        loadComponent: () =>
          import('./pages/admin/contatos/contatos.component')
            .then(m => m.ContatosComponent),
        title: 'Contatos — EcoChatBotMarcx'
>>>>>>> 37038798148d95e3284b5959b5d7ab66266a4507
      },

      // ── E-MAIL ──────────────────────────────────────────────────────────
      // URL: http://dominio/admin/email
      {
        path: 'email',
<<<<<<< HEAD
        canActivate: [nivelGuard],
        data: { nivelMinimo: 'gerente' },
        loadComponent: () => import('./pages/admin/email/email.component').then(m => m.EmailComponent),
        title: 'E-mail — EcoChat Marcx'
=======
        loadComponent: () =>
          import('./pages/admin/email/email.component')
            .then(m => m.EmailComponent),
        title: 'E-mail — EcoChatBotMarcx'
>>>>>>> 37038798148d95e3284b5959b5d7ab66266a4507
      },

      // ── CAMPANHAS ───────────────────────────────────────────────────────
      // URL: http://dominio/admin/campanhas
      {
        path: 'campanhas',
<<<<<<< HEAD
        canActivate: [nivelGuard],
        data: { nivelMinimo: 'gerente' },
        loadComponent: () => import('./pages/admin/campanhas/campanhas.component').then(m => m.CampanhasComponent),
        title: 'Campanhas — EcoChat Marcx'
=======
        loadComponent: () =>
          import('./pages/admin/campanhas/campanhas.component')
            .then(m => m.CampanhasComponent),
        title: 'Campanhas — EcoChatBotMarcx'
>>>>>>> 37038798148d95e3284b5959b5d7ab66266a4507
      },

      // ── ARQUIVOS ────────────────────────────────────────────────────────
      // URL: http://dominio/admin/arquivos
      {
        path: 'arquivos',
<<<<<<< HEAD
        canActivate: [nivelGuard],
        data: { nivelMinimo: 'atendente' },
        loadComponent: () => import('./pages/admin/arquivos/arquivos.component').then(m => m.ArquivosComponent),
        title: 'Arquivos — EcoChat Marcx'
=======
        loadComponent: () =>
          import('./pages/admin/arquivos/arquivos.component')
            .then(m => m.ArquivosComponent),
        title: 'Arquivos — EcoChatBotMarcx'
>>>>>>> 37038798148d95e3284b5959b5d7ab66266a4507
      },

      // ── MENSAGENS ───────────────────────────────────────────────────────
      // URL: http://dominio/admin/mensagens
      {
        path: 'mensagens',
<<<<<<< HEAD
        canActivate: [nivelGuard],
        data: { nivelMinimo: 'gerente' },
        loadComponent: () => import('./pages/admin/mensagens/mensagens.component').then(m => m.MensagensComponent),
        title: 'Mensagens — EcoChat Marcx'
      },
      {
        path: 'niveis',
        canActivate: [nivelGuard],
        data: { nivelMinimo: 'administrador' },
        loadComponent: () => import('./pages/admin/niveis/niveis.component').then(m => m.NiveisComponent),
        title: 'Níveis de Usuário — EcoChat Marcx'
=======
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
>>>>>>> 37038798148d95e3284b5959b5d7ab66266a4507
      },

      // ── ESCALAS ─────────────────────────────────────────────────────────
      // URL: http://dominio/admin/escalas
      {
        path: 'escalas',
<<<<<<< HEAD
        canActivate: [nivelGuard],
        data: { nivelMinimo: 'gerente' },
        loadComponent: () => import('./pages/admin/escalas/escalas.component').then(m => m.EscalasComponent),
        title: 'Painel de Escalas — EcoChat Marcx'
=======
        loadComponent: () =>
          import('./pages/admin/escalas/escalas.component')
            .then(m => m.EscalasComponent),
        title: 'Painel de Escalas — EcoChatBotMarcx'
>>>>>>> 37038798148d95e3284b5959b5d7ab66266a4507
      },

      // ── RELATÓRIO ───────────────────────────────────────────────────────
      // URL: http://dominio/admin/relatorio
      {
        path: 'relatorio',
<<<<<<< HEAD
        canActivate: [nivelGuard],
        data: { nivelMinimo: 'supervisor' },
        loadComponent: () => import('./pages/admin/relatorio/relatorio.component').then(m => m.RelatorioComponent),
        title: 'Relatório — EcoChat Marcx'
      },
    ]
  },

  // ── Chat (interface do cliente) ────────────────────────────────
=======
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
>>>>>>> 37038798148d95e3284b5959b5d7ab66266a4507
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
<<<<<<< HEAD
        // /chat/:canal → atendimento do canal
        // Exemplos: /chat/atendimento  /chat/comercial
=======
>>>>>>> 37038798148d95e3284b5959b5d7ab66266a4507
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