import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { FilterBarComponent, FilterOptions, FilterValues } from '../../../shared/components/filter-bar/filter-bar.component';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, RouterLink, FilterBarComponent],
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.css']
})
export class DashboardComponent {
  filterOptions: FilterOptions = {
    departamentos: [
      { id: 1, nome: 'Portaria' },
      { id: 2, nome: 'Agendamento' },
      { id: 3, nome: 'Triagem' }
    ]
  };

  atalhos = [
    { rota: '/chat/menu', icone: 'fa-comments', label: 'Abrir Chat', cor: 'green' },
    { rota: '/admin/canais', icone: 'fa-project-diagram', label: 'Configurar Canais', cor: 'blue' },
    { rota: '/admin/usuarios', icone: 'fa-users', label: 'Gerenciar Usuários', cor: 'red' },
    { rota: '/admin/departamentos', icone: 'fa-building', label: 'Departamentos', cor: 'purple' },
    { rota: '/admin/escalas', icone: 'fa-calendar-alt', label: 'Painel de Escalas', cor: 'teal' },
    { rota: '/admin/relatorio', icone: 'fa-chart-bar', label: 'Relatórios', cor: 'yellow' },
  ];

  onFilterApplied(filters: FilterValues): void {
    console.log('Filtros aplicados:', filters);
    // Aqui você pode chamar um serviço para buscar dados filtrados
  }
}
