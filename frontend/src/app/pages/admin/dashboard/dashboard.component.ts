import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
<<<<<<< HEAD
import { AuthService } from '../../../core/services/auth.service';
import { NivelAcesso } from '../../../core/models/nivel-usuario.model';
import { temNivelMinimo } from '../../../core/auth/niveis';

interface Atalho {
  rota: string;
  icone: string;
  label: string;
  cor: string;
  nivelMinimo?: NivelAcesso;
}
=======
import { FilterBarComponent, FilterOptions, FilterValues } from '../../../shared/components/filter-bar/filter-bar.component';
>>>>>>> 37038798148d95e3284b5959b5d7ab66266a4507

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, RouterLink, FilterBarComponent],
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.css']
})
export class DashboardComponent {
<<<<<<< HEAD
  private readonly todosAtalhos: Atalho[] = [
    { rota: '/admin/atendimentos',  icone: 'fa-comments',       label: 'Abrir Chat',         cor: 'green',  nivelMinimo: 'atendente' },
    { rota: '/admin/canais',         icone: 'fa-project-diagram', label: 'Configurar Canais',  cor: 'blue',   nivelMinimo: 'gerente' },
    { rota: '/admin/usuarios',       icone: 'fa-users',           label: 'Gerenciar Usuários', cor: 'red',    nivelMinimo: 'supervisor' },
    { rota: '/admin/departamentos',  icone: 'fa-building',        label: 'Departamentos',      cor: 'purple', nivelMinimo: 'gerente' },
    { rota: '/admin/relatorio',      icone: 'fa-chart-bar',       label: 'Relatórios',         cor: 'yellow', nivelMinimo: 'supervisor' },
  ];

  atalhos: Atalho[];

  constructor(private auth: AuthService) {
    const nivel = this.auth.getUsuarioAtual()?.nivel;
    this.atalhos = this.todosAtalhos.filter(a => temNivelMinimo(nivel, a.nivelMinimo));
=======
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
>>>>>>> 37038798148d95e3284b5959b5d7ab66266a4507
  }
}
