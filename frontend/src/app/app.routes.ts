<<<<<<< HEAD
//╔══════════════════════════════════════════════════════════════════════════════╗
// ║  PROJETO.......: EcoChatBotMarcx — Sistema de Atendimento Digital          ║
// ║  ARQUIVO.......: app.routes.ts                                             ║
// ║  LOCALIZAÇÃO...: frontend/src/app/app.routes.ts                            ║
// ║  AUTOR.........: Ademir Queiroz                                            ║
// ║  DATA..........: 08/09/2026                                                ║
// ║  VERSÃO........: 1.0.1                                                     ║
// ║                                                                            ║
// ║  DESCRIÇÃO                                                                 ║
// ║  Configuração moderna de rotas usando o padrão standalone do Angular 17+.  ║
// ║  Define toda a navegação do sistema:                                       ║
// ║    • Login (público)                                                       ║
// ║    • Painel administrativo (protegido por authGuard + nivelGuard)          ║
// ║    • Interface pública de chat do cliente/paciente                         ║
// ║                                                                            ║
// ║  DIFERENÇA PARA app-routing.module.ts:                                     ║
// ║    • Não utiliza @NgModule                                                 ║
// ║    • Usa loadComponent() ao invés de loadChildren()                        ║
// ║    • Registra rotas via provideRouter() no app.config.ts                   ║
// ║    • É o padrão recomendado a partir do Angular 17                         ║
// ╚══════════════════════════════════════════════════════════════════════════════╝

// ─────────────────────────────────────────────────────────────────────────────
// IMPORTAÇÕES
// ─────────────────────────────────────────────────────────────────────────────
import { Routes } from '@angular/router';
//   Routes → interface TypeScript que define o formato do array de rotas.
//   Fornece autocomplete e validação em tempo de compilação.

import { authGuard } from './core/guards/auth.guard';
//   authGuard → verifica se o usuário está autenticado antes de permitir acesso.
//   Se não estiver autenticado, redireciona para /login.

import { nivelGuard } from './core/guards/nivel.guard';
//   nivelGuard → verifica se o usuário tem o nível MÍNIMO exigido pela rota.
//   O nível é lido de `data.nivelMinimo` definido em cada rota filha.
//   Hierarquia esperada: atendente < supervisor < gerente < administrador.

// ─────────────────────────────────────────────────────────────────────────────
// ARRAY DE ROTAS
// ─────────────────────────────────────────────────────────────────────────────
export const routes: Routes = [

  // ── ROTA RAIZ ─────────────────────────────────────────────────────────────
  // Redireciona a raiz para o dashboard administrativo.
  { path: '', redirectTo: 'admin/dashboard', pathMatch: 'full' },

  // ─────────────────────────────────────────────────────────────────────────
  // LOGIN — Rota pública
  // ─────────────────────────────────────────────────────────────────────────
  // URL: http://dominio/login
  // Acesso: qualquer pessoa (sem autenticação necessária)
  //
  // loadComponent() → carrega o componente sob demanda (lazy loading).
  // title → define o título da aba do navegador (<title>).
  // ─────────────────────────────────────────────────────────────────────────
  {
    path: 'login',
    loadComponent: () =>
      import('./pages/login/login.component').then(m => m.LoginComponent),
    title: 'Login — EcoChatBotMarcx'
  },

  // ─────────────────────────────────────────────────────────────────────────
  // ADMIN — Rotas protegidas por autenticação + nível
  // ─────────────────────────────────────────────────────────────────────────
  // URL: http://dominio/admin/*
  // Acesso: apenas usuários autenticados (verificado pelo authGuard)
  //
  // canActivate: [authGuard] → executado ANTES da ativação da rota.
  //   Se authGuard retornar false, o usuário é redirecionado para /login.
  //
  // loadComponent() → carrega o AdminLayoutComponent (sidebar + topbar +
  //   <router-outlet> interno para as rotas filhas).
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
      // Acesso: qualquer usuário autenticado (sem exigência de nível)
      {
        path: 'dashboard',
        loadComponent: () =>
          import('./pages/admin/dashboard/dashboard.component')
            .then(m => m.DashboardComponent),
        title: 'Dashboard — EcoChatBotMarcx'
      },

      // ── ATENDIMENTOS ────────────────────────────────────────────────────
      // URL: http://dominio/admin/atendimentos
      // Nível mínimo: atendente
      {
        path: 'atendimentos',
        canActivate: [nivelGuard],
        data: { nivelMinimo: 'atendente' },
        loadComponent: () =>
          import('./pages/admin/atendimentos/atendimentos.component')
            .then(m => m.AtendimentosComponent),
        title: 'Atendimentos — EcoChatBotMarcx'
      },

      // ── USUÁRIOS ────────────────────────────────────────────────────────
      // URL: http://dominio/admin/usuarios
      // Nível mínimo: supervisor
      {
        path: 'usuarios',
        canActivate: [nivelGuard],
        data: { nivelMinimo: 'supervisor' },
        loadComponent: () =>
          import('./pages/admin/usuarios/usuario.component')
            .then(m => m.UsuariosComponent),
        title: 'Usuários — EcoChatBotMarcx'
      },

      // ── DEPARTAMENTOS ───────────────────────────────────────────────────
      // URL: http://dominio/admin/departamentos
      // Nível mínimo: gerente
      {
        path: 'departamentos',
        canActivate: [nivelGuard],
        data: { nivelMinimo: 'gerente' },
        loadComponent: () =>
          import('./pages/admin/departamentos/departamentos.component')
            .then(m => m.DepartamentosComponent),
        title: 'Departamentos — EcoChatBotMarcx'
      },

      // ── CANAIS DE ATENDIMENTO ───────────────────────────────────────────
      // URL: http://dominio/admin/canais
      // Nível mínimo: gerente
      {
        path: 'canais',
        canActivate: [nivelGuard],
        data: { nivelMinimo: 'gerente' },
        loadComponent: () =>
          import('./pages/admin/canais/canais.component')
            .then(m => m.CanaisComponent),
        title: 'Canais de Atendimento — EcoChatBotMarcx'
      },

      // ── CONEXÕES ────────────────────────────────────────────────────────
      // URL: http://dominio/admin/conexoes
      // Nível mínimo: administrador
      {
        path: 'conexoes',
        canActivate: [nivelGuard],
        data: { nivelMinimo: 'administrador' },
        loadComponent: () =>
          import('./pages/admin/conexoes/conexoes.component')
            .then(m => m.ConexoesComponent),
        title: 'Conexões — EcoChatBotMarcx'
      },

      // ── CONTATOS ────────────────────────────────────────────────────────
      // URL: http://dominio/admin/contatos
      // Nível mínimo: gerente
      {
        path: 'contatos',
        canActivate: [nivelGuard],
        data: { nivelMinimo: 'gerente' },
        loadComponent: () =>
          import('./pages/admin/contatos/contatos.component')
            .then(m => m.ContatosComponent),
        title: 'Contatos — EcoChatBotMarcx'
      },

      // ── E-MAIL ──────────────────────────────────────────────────────────
      // URL: http://dominio/admin/email
      // Nível mínimo: gerente
      {
        path: 'email',
        canActivate: [nivelGuard],
        data: { nivelMinimo: 'gerente' },
        loadComponent: () =>
          import('./pages/admin/email/email.component')
            .then(m => m.EmailComponent),
        title: 'E-mail — EcoChatBotMarcx'
      },

      // ── CAMPANHAS ───────────────────────────────────────────────────────
      // URL: http://dominio/admin/campanhas
      // Nível mínimo: gerente
      {
        path: 'campanhas',
        canActivate: [nivelGuard],
        data: { nivelMinimo: 'gerente' },
        loadComponent: () =>
          import('./pages/admin/campanhas/campanhas.component')
            .then(m => m.CampanhasComponent),
        title: 'Campanhas — EcoChatBotMarcx'
      },

      // ── ARQUIVOS ────────────────────────────────────────────────────────
      // URL: http://dominio/admin/arquivos
      // Nível mínimo: atendente
      {
        path: 'arquivos',
        canActivate: [nivelGuard],
        data: { nivelMinimo: 'atendente' },
        loadComponent: () =>
          import('./pages/admin/arquivos/arquivos.component')
            .then(m => m.ArquivosComponent),
        title: 'Arquivos — EcoChatBotMarcx'
      },

      // ── MENSAGENS ───────────────────────────────────────────────────────
      // URL: http://dominio/admin/mensagens
      // Nível mínimo: gerente
      {
        path: 'mensagens',
        canActivate: [nivelGuard],
        data: { nivelMinimo: 'gerente' },
        loadComponent: () =>
          import('./pages/admin/mensagens/mensagens.component')
            .then(m => m.MensagensComponent),
        title: 'Mensagens — EcoChatBotMarcx'
      },

      // ── NÍVEIS DE USUÁRIO ───────────────────────────────────────────────
      // URL: http://dominio/admin/niveis
      // Nível mínimo: administrador
      {
        path: 'niveis',
        canActivate: [nivelGuard],
        data: { nivelMinimo: 'administrador' },
        loadComponent: () =>
          import('./pages/admin/niveis/niveis.component')
            .then(m => m.NiveisComponent),
        title: 'Níveis de Usuário — EcoChatBotMarcx'
      },

      // ── ESCALAS ─────────────────────────────────────────────────────────
      // URL: http://dominio/admin/escalas
      // Nível mínimo: gerente
      {
        path: 'escalas',
        canActivate: [nivelGuard],
        data: { nivelMinimo: 'gerente' },
        loadComponent: () =>
          import('./pages/admin/escalas/escalas.component')
            .then(m => m.EscalasComponent),
        title: 'Painel de Escalas — EcoChatBotMarcx'
      },

      // ── RELATÓRIO ───────────────────────────────────────────────────────
      // URL: http://dominio/admin/relatorio
      // Nível mínimo: supervisor
      {
        path: 'relatorio',
        canActivate: [nivelGuard],
        data: { nivelMinimo: 'supervisor' },
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
            .then(m => m.AtendimentoComponent),
        title: 'Atendimento — EcoChatBotMarcx'
      }
    ]
  },

  // ── WILDCARD (catch-all) ──────────────────────────────────────────────────
  // path: '**' → casa com qualquer URL não mapeada.
  // SEMPRE deve ser a última rota do array.
  { path: '**', redirectTo: 'admin/dashboard' }
=======
import { Routes } from '@angular/router';
import { authGuard } from './core/guards/auth.guard';
import { nivelGuard } from './core/guards/nivel.guard';

export const routes: Routes = [
    { path: '', redirectTo: 'admin/dashboard', pathMatch: 'full' },
    {
        path: 'login',
        loadComponent: () => import('./pages/login/login.component').then(m => m.LoginComponent),
        title: 'Login - EcoChat Marcx'
    },
    {
        path: 'admin',
        canActivate: [authGuard],
        loadComponent: () => import('./shared/components/admin-layout/admin-layout.component').then(m => m.AdminLayoutComponent),
        children: [
            { path: 'dashboard', loadComponent: () => import('./pages/admin/dashboard/dashboard.component').then(m => m.DashboardComponent), title: 'Dashboard - EcoChat Marcx' },
            { path: 'atendimentos', canActivate: [nivelGuard], data: { nivelMinimo: 'atendente' }, loadComponent: () => import('./pages/admin/atendimentos/atendimentos.component').then(m => m.AtendimentosComponent), title: 'Atendimentos - EcoChat Marcx' },
            { path: 'usuarios', canActivate: [nivelGuard], data: { nivelMinimo: 'supervisor' }, loadComponent: () => import('./pages/admin/usuarios/usuarios.component').then(m => m.UsuariosComponent), title: 'Usuarios - EcoChat Marcx' },
            { path: 'departamentos', canActivate: [nivelGuard], data: { nivelMinimo: 'gerente' }, loadComponent: () => import('./pages/admin/departamentos/departamentos.component').then(m => m.DepartamentosComponent), title: 'Departamentos - EcoChat Marcx' },
            { path: 'canais', canActivate: [nivelGuard], data: { nivelMinimo: 'gerente' }, loadComponent: () => import('./pages/admin/canais/canais.component').then(m => m.CanaisComponent), title: 'Canais de Atendimento - EcoChat Marcx' },
            { path: 'conexoes', canActivate: [nivelGuard], data: { nivelMinimo: 'administrador' }, loadComponent: () => import('./pages/admin/conexoes/conexoes.component').then(m => m.ConexoesComponent), title: 'Conexoes - EcoChat Marcx' },
            { path: 'contatos', canActivate: [nivelGuard], data: { nivelMinimo: 'gerente' }, loadComponent: () => import('./pages/admin/contatos/contatos.component').then(m => m.ContatosComponent), title: 'Contatos - EcoChat Marcx' },
            { path: 'email', canActivate: [nivelGuard], data: { nivelMinimo: 'gerente' }, loadComponent: () => import('./pages/admin/email/email.component').then(m => m.EmailComponent), title: 'E-mail - EcoChat Marcx' },
            { path: 'campanhas', canActivate: [nivelGuard], data: { nivelMinimo: 'gerente' }, loadComponent: () => import('./pages/admin/campanhas/campanhas.component').then(m => m.CampanhasComponent), title: 'Campanhas - EcoChat Marcx' },
            { path: 'arquivos', canActivate: [nivelGuard], data: { nivelMinimo: 'atendente' }, loadComponent: () => import('./pages/admin/arquivos/arquivos.component').then(m => m.ArquivosComponent), title: 'Arquivos - EcoChat Marcx' },
            { path: 'mensagens', canActivate: [nivelGuard], data: { nivelMinimo: 'gerente' }, loadComponent: () => import('./pages/admin/mensagens/mensagens.component').then(m => m.MensagensComponent), title: 'Mensagens - EcoChat Marcx' },
            { path: 'niveis', canActivate: [nivelGuard], data: { nivelMinimo: 'administrador' }, loadComponent: () => import('./pages/admin/niveis/niveis.component').then(m => m.NiveisComponent), title: 'Niveis de Usuario - EcoChat Marcx' },
            { path: 'escalas', canActivate: [nivelGuard], data: { nivelMinimo: 'gerente' }, loadComponent: () => import('./pages/admin/escalas/escalas.component').then(m => m.EscalasComponent), title: 'Painel de Escalas - EcoChat Marcx' },
            { path: 'relatorio', canActivate: [nivelGuard], data: { nivelMinimo: 'supervisor' }, loadComponent: () => import('./pages/admin/relatorio/relatorio.component').then(m => m.RelatorioComponent), title: 'Relatorio - EcoChat Marcx' }
        ]
    },
    {
        path: 'chat',
        children: [
            { path: 'menu', loadComponent: () => import('./pages/chat/hub-menu/hub-menu.component').then(m => m.HubMenuComponent), title: 'Atendimento - EcoChat Marcx' },
            { path: ':canal', loadComponent: () => import('./pages/chat/atendimento/atendimento.component').then(m => m.AtendimentoComponent) }
        ]
    },
    { path: '**', redirectTo: 'admin/dashboard' }
>>>>>>> ab4be86373569a523b5ba9aad91480dc4ca0c89e
];