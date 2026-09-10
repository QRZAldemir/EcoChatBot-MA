import { Component, EventEmitter, Output, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';

export type Pagina = 'usuarios' | 'turnos' | 'departamentos' | 'canais';

export interface NavItem {
  rota: string;
  icone: string;
  label: string;
}

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './sidebar.component.html',
  styleUrls: ['./sidebar.component.css']
})
export class SidebarComponent {
  @Input() aberto: boolean = true;
  @Input() navItens: NavItem[] = [];
  @Output() paginaSelecionada = new EventEmitter<Pagina>();

  paginaAtual: Pagina = 'usuarios';

  navegar(pagina: Pagina): void {
    this.paginaAtual = pagina;
    this.paginaSelecionada.emit(pagina);
  }
}