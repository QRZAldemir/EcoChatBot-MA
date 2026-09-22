import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterOutlet, RouterLink, RouterLinkActive } from '@angular/router';
import { AuthService } from '../../../core/services/auth.service';
import { NivelAcesso } from '../../../core/models/nivel-usuario.model';
import { temNivelMinimo } from '../../../core/auth/niveis.auth';

interface NavItem {
  rota: string;
  icone: string;
  label: string;
  nivelMinimo?: NivelAcesso;
}

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

  // Ordem e ícones seguem docs/Barra Menu.png. Itens sem nível suficiente
  // são omitidos — a API também recusa (403); a sidebar só esconde a UX.
  private readonly todosNavItens: NavItem[] = [
    { rota: '/admin/dashboard',     icone: 'fa-house',            label: 'Início' },
    { rota: '/admin/atendimentos',  icone: 'fa-comments',          label: 'Chat',       nivelMinimo: 'atendente' },
    { rota: '/admin/arquivos',      icone: 'fa-folder',            label: 'Arquivos',   nivelMinimo: 'atendente' },
    { rota: '/admin/usuarios',      icone: 'fa-users',             label: 'Usuários',   nivelMinimo: 'supervisor' },
    { rota: '/admin/relatorio',     icone: 'fa-chart-bar',         label: 'Relatório',  nivelMinimo: 'supervisor' },
    { rota: '/admin/contatos',      icone: 'fa-address-card',      label: 'Contatos',   nivelMinimo: 'gerente' },
    { rota: '/admin/departamentos', icone: 'fa-building',          label: 'Setor',      nivelMinimo: 'gerente' },
    { rota: '/admin/canais',        icone: 'fa-project-diagram',   label: 'Canais',     nivelMinimo: 'gerente' },
    { rota: '/admin/mensagens',     icone: 'fa-comment-dots',      label: 'Mensagens',  nivelMinimo: 'gerente' },
    { rota: '/admin/email',         icone: 'fa-envelope',          label: 'E-mail',     nivelMinimo: 'gerente' },
    { rota: '/admin/campanhas',     icone: 'fa-paper-plane',       label: 'Campanhas',  nivelMinimo: 'gerente' },
    { rota: '/admin/conexoes',      icone: 'fa-wifi',              label: 'Conexões',   nivelMinimo: 'administrador' },
    { rota: '/admin/niveis',        icone: 'fa-user-shield',       label: 'Níveis',     nivelMinimo: 'administrador' },
  ];

  get navItens(): NavItem[] {
    const nivel = this.usuario?.nivel;
    return this.todosNavItens.filter(item => temNivelMinimo(nivel, item.nivelMinimo));
  }
}
