import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterOutlet, RouterLink, RouterLinkActive } from '@angular/router';
import { AuthService } from '../../../core/services/auth.service';

@Component({
  selector: 'app-layout',
  standalone: true,
  imports: [RouterOutlet, RouterLink, RouterLinkActive, CommonModule],
  templateUrl: './layout.component.html',
  styleUrls: ['./layout.component.css']
})
export class LayoutComponent {
  menuAberto = true;
  usuario = this.auth.getUsuarioAtual();

  constructor(private auth: AuthService, private router: Router) {}

  sair(): void {
    this.auth.logout();
    this.router.navigate(['/login']);
  }

  navItens = [
    { secao: 'Visão Geral', itens: [
      { rota: '/admin/dashboard', icone: 'fa-gauge-high',    label: 'Dashboard' },
    ]},
    { secao: 'Atendimento', itens: [
      { rota: '/admin/atendimentos', icone: 'fa-inbox',    label: 'Fila de Atendimento' },
      { rota: '/chat/menu',          icone: 'fa-comments',     label: 'Iniciar Chat' },
    ]},
    { secao: 'Configuração', itens: [
      { rota: '/admin/canais',       icone: 'fa-project-diagram', label: 'Canais' },
      { rota: '/admin/departamentos',icone: 'fa-building',        label: 'Departamentos' },
      { rota: '/admin/mensagens',    icone: 'fa-comment-dots',    label: 'Mensagens' },
      { rota: '/admin/usuarios',     icone: 'fa-users',           label: 'Usuários' },
      { rota: '/admin/niveis',       icone: 'fa-shield-halved',   label: 'Níveis de Acesso' },
    ]},
    { secao: 'Gestão', itens: [
      { rota: '/admin/escalas',   icone: 'fa-calendar-alt',  label: 'Painel de Escalas' },
      { rota: '/admin/relatorio', icone: 'fa-chart-bar',     label: 'Relatórios' },
    ]},
  ];
}
