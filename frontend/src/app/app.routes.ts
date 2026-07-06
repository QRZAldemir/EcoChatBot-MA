import { Routes } from '@angular/router';
import { authGuard } from './core/guards/auth.guard';

export const routes: Routes = [
  { path: '', redirectTo: 'admin/dashboard', pathMatch: 'full' },

  {
    path: 'login',
    loadComponent: () => import('./pages/login/login.component').then(m => m.LoginComponent),
    title: 'Login — EcoChat Mackenzie'
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
        title: 'Dashboard — EcoChat Mackenzie'
      },
      {
        path: 'usuarios',
        loadComponent: () => import('./pages/admin/usuarios/usuarios.component').then(m => m.UsuariosComponent),
        title: 'Usuários — EcoChat Mackenzie'
      },
      {
        path: 'departamentos',
        loadComponent: () => import('./pages/admin/departamentos/departamentos.component').then(m => m.DepartamentosComponent),
        title: 'Departamentos — EcoChat Mackenzie'
      },
      {
        path: 'canais',
        loadComponent: () => import('./pages/admin/canais/canais.component').then(m => m.CanaisComponent),
        title: 'Canais de Atendimento — EcoChat Mackenzie'
      },
      {
        path: 'niveis',
        loadComponent: () => import('./pages/admin/niveis/niveis.component').then(m => m.NiveisComponent),
        title: 'Níveis de Usuário — EcoChat Mackenzie'
      },
      {
        path: 'escalas',
        loadComponent: () => import('./pages/admin/escalas/escalas.component').then(m => m.EscalasComponent),
        title: 'Painel de Escalas — EcoChat Mackenzie'
      },
      {
        path: 'relatorio',
        loadComponent: () => import('./pages/admin/relatorio/relatorio.component').then(m => m.RelatorioComponent),
        title: 'Relatório — EcoChat Mackenzie'
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
        title: 'Atendimento — Mackenzie'
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
