import { Routes } from '@angular/router';
import { authGuard } from './core/guards/auth.guard';

export const routes: Routes = [
  { path: '', redirectTo: 'admin/dashboard', pathMatch: 'full' },

  {
    path: 'login',
    loadComponent: () => import('./pages/login/login.component').then(m => m.LoginComponent),
    title: 'Login — EcoChat Marcx'
  },

  // ── Admin (com sidebar) ────────────────────────────────────────
  {
    path: 'admin',
    canActivate: [authGuard],
    loadComponent: () => import('./shared/components/layout/layout.component').then(m => m.LayoutComponent),
    children: [
      {
        path: 'dashboard',
        loadComponent: () => import('./pages/admin/dashboard/dashboard.component').then(m => m.DashboardComponent),
        title: 'Dashboard — EcoChat Marcx'
      },
      {
        path: 'atendimentos',
        loadComponent: () => import('./pages/admin/atendimentos/atendimentos.component').then(m => m.AtendimentosComponent),
        title: 'Atendimentos — EcoChat Marcx'
      },
      {
        path: 'usuarios',
        loadComponent: () => import('./pages/admin/usuarios/usuarios.component').then(m => m.UsuariosComponent),
        title: 'Usuários — EcoChat Marcx'
      },
      {
        path: 'departamentos',
        loadComponent: () => import('./pages/admin/departamentos/departamentos.component').then(m => m.DepartamentosComponent),
        title: 'Departamentos — EcoChat Marcx'
      },
      {
        path: 'canais',
        loadComponent: () => import('./pages/admin/canais/canais.component').then(m => m.CanaisComponent),
        title: 'Canais de Atendimento — EcoChat Marcx'
      },
      {
        path: 'conexoes',
        loadComponent: () => import('./pages/admin/conexoes/conexoes.component').then(m => m.ConexoesComponent),
        title: 'Conexões — EcoChat Marcx'
      },
      {
        path: 'contatos',
        loadComponent: () => import('./pages/admin/contatos/contatos.component').then(m => m.ContatosComponent),
        title: 'Contatos — EcoChat Marcx'
      },
      {
        path: 'email',
        loadComponent: () => import('./pages/admin/email/email.component').then(m => m.EmailComponent),
        title: 'E-mail — EcoChat Marcx'
      },
      {
        path: 'campanhas',
        loadComponent: () => import('./pages/admin/campanhas/campanhas.component').then(m => m.CampanhasComponent),
        title: 'Campanhas — EcoChat Marcx'
      },
      {
        path: 'arquivos',
        loadComponent: () => import('./pages/admin/arquivos/arquivos.component').then(m => m.ArquivosComponent),
        title: 'Arquivos — EcoChat Marcx'
      },
      {
        path: 'mensagens',
        loadComponent: () => import('./pages/admin/mensagens/mensagens.component').then(m => m.MensagensComponent),
        title: 'Mensagens — EcoChat Marcx'
      },
      {
        path: 'niveis',
        loadComponent: () => import('./pages/admin/niveis/niveis.component').then(m => m.NiveisComponent),
        title: 'Níveis de Usuário — EcoChat Marcx'
      },
      {
        path: 'escalas',
        loadComponent: () => import('./pages/admin/escalas/escalas.component').then(m => m.EscalasComponent),
        title: 'Painel de Escalas — EcoChat Marcx'
      },
      {
        path: 'relatorio',
        loadComponent: () => import('./pages/admin/relatorio/relatorio.component').then(m => m.RelatorioComponent),
        title: 'Relatório — EcoChat Marcx'
      },
    ]
  },

  // ── Chat (interface do cliente/paciente) ───────────────────────
  {
    path: 'chat',
    children: [
      {
        path: 'menu',
        loadComponent: () => import('./pages/chat/hub-menu/hub-menu.component').then(m => m.HubMenuComponent),
        title: 'Atendimento — Marcx'
      },
      {
        // /chat/:canal → carrega o HTML do canal em iframe
        // Exemplos: /chat/portaria  /chat/agendamento-ambulatorial
        path: ':canal',
        loadComponent: () => import('./pages/chat/atendimento/atendimento.component').then(m => m.AtendimentoComponent),
      },
    ]
  },

  { path: '**', redirectTo: 'admin/dashboard' }
];
