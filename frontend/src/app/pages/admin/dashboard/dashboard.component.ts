import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { AuthService } from '../../../core/services/auth.service';
import { NivelAcesso } from '../../../core/models/nivel-usuario.model';
import { temNivelMinimo } from '../../../core/auth/niveis';
import { FilterBarComponent, FilterOptions, FilterValues } from '../../../shared/components/filter-bar/filter-bar.component';

interface Atalho {
    rota: string;
    icone: string;
    label: string;
    cor: string;
    nivelMinimo?: NivelAcesso;
}

@Component({
    selector: 'app-dashboard',
    standalone: true,
    imports: [CommonModule, RouterLink, FilterBarComponent],
    templateUrl: './dashboard.component.html',
    styleUrls: ['./dashboard.component.css']
})
export class DashboardComponent {
    private readonly todosAtalhos: Atalho[] = [
        { rota: '/admin/atendimentos', icone: 'fa-comments', label: 'Abrir Chat', cor: 'green', nivelMinimo: 'atendente' },
        { rota: '/admin/canais', icone: 'fa-project-diagram', label: 'Configurar Canais', cor: 'blue', nivelMinimo: 'gerente' },
        { rota: '/admin/usuarios', icone: 'fa-users', label: 'Gerenciar Usuarios', cor: 'red', nivelMinimo: 'supervisor' },
        { rota: '/admin/departamentos', icone: 'fa-building', label: 'Departamentos', cor: 'purple', nivelMinimo: 'gerente' },
        { rota: '/admin/relatorio', icone: 'fa-chart-bar', label: 'Relatorios', cor: 'yellow', nivelMinimo: 'supervisor' }
    ];

    atalhos: Atalho[];
    filterOptions: FilterOptions = { departamentos: [] };

    constructor(private auth: AuthService) {
        const nivel = this.auth.getUsuarioAtual()?.nivel;
        this.atalhos = this.todosAtalhos.filter(atalho => temNivelMinimo(nivel, atalho.nivelMinimo));
    }

    onFilterApplied(filters: FilterValues): void {
        console.log('Filtros aplicados:', filters);
    }
}