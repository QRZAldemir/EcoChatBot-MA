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

  // Ordem e ícones seguem docs/Barra Menu.png (ver docs/Skill sobre a barra
  // de Menu.md). Histórico/Sinal/Calendário ficam de fora — seu significado
  // exato no produto ainda não foi definido.
  navItens = [
    { rota: '/admin/dashboard',     icone: 'fa-house',         label: 'Início' },
    { rota: '/admin/usuarios',      icone: 'fa-users',         label: 'Usuários' },
    { rota: '/admin/contatos',      icone: 'fa-address-card',  label: 'Contatos' },
    { rota: '/admin/departamentos', icone: 'fa-building',      label: 'Setor' },
    { rota: '/admin/atendimentos',  icone: 'fa-comments',      label: 'Chat' },
    { rota: '/admin/mensagens',     icone: 'fa-comment-dots',  label: 'Mensagens' },
    { rota: '/admin/email',         icone: 'fa-envelope',      label: 'E-mail' },
    { rota: '/admin/conexoes',      icone: 'fa-wifi',          label: 'Conexões' },
    { rota: '/admin/campanhas',     icone: 'fa-paper-plane',   label: 'Campanhas' },
    { rota: '/admin/arquivos',      icone: 'fa-folder',        label: 'Arquivos' },
  ];
}
