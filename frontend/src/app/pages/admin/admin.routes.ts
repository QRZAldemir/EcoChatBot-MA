import { Routes } from '@angular/router';

export const ADMIN_ROUTES: Routes = [
    { path: 'dashboard', loadComponent: () => import('./dashboard/dashboard.component').then(m => m.DashboardComponent) },
    { path: 'usuarios', loadComponent: () => import('./usuarios/usuarios.component').then(m => m.UsuariosComponent) },
    { path: 'departamentos', loadComponent: () => import('./departamentos/departamentos.component').then(m => m.DepartamentosComponent) },
    { path: 'canais', loadComponent: () => import('./canais/canais.component').then(m => m.CanaisComponent) },
    { path: 'atendimentos', loadComponent: () => import('./atendimentos/atendimentos.component').then(m => m.AtendimentosComponent) },
    { path: 'contatos', loadComponent: () => import('./contatos/contatos.component').then(m => m.ContatosComponent) },
    { path: 'email', loadComponent: () => import('./email/email.component').then(m => m.EmailComponent) },
    { path: 'campanhas', loadComponent: () => import('./campanhas/campanhas.component').then(m => m.CampanhasComponent) },
    { path: 'arquivos', loadComponent: () => import('./arquivos/arquivos.component').then(m => m.ArquivosComponent) },
    { path: 'mensagens', loadComponent: () => import('./mensagens/mensagens.component').then(m => m.MensagensComponent) },
    { path: 'conexoes', loadComponent: () => import('./conexoes/conexoes.component').then(m => m.ConexoesComponent) },
    { path: 'escalas', loadComponent: () => import('./escalas/escalas.component').then(m => m.EscalasComponent) },
    { path: 'relatorio', loadComponent: () => import('./relatorio/relatorio.component').then(m => m.RelatorioComponent) },
    { path: '', redirectTo: 'dashboard', pathMatch: 'full' }
];
