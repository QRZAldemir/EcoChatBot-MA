import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.css']
})
export class DashboardComponent {
  atalhos = [
    { rota: '/chat/menu',            icone: 'fa-comments',       label: 'Abrir Chat',         cor: 'green'  },
    { rota: '/admin/canais',         icone: 'fa-project-diagram', label: 'Configurar Canais',  cor: 'blue'   },
    { rota: '/admin/usuarios',       icone: 'fa-users',           label: 'Gerenciar Usuários', cor: 'red'    },
    { rota: '/admin/departamentos',  icone: 'fa-building',        label: 'Departamentos',      cor: 'purple' },
    { rota: '/admin/escalas',        icone: 'fa-calendar-alt',    label: 'Painel de Escalas',  cor: 'teal'   },
    { rota: '/admin/relatorio',      icone: 'fa-chart-bar',       label: 'Relatórios',         cor: 'yellow' },
  ];
}
