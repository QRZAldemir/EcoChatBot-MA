import { Component, OnInit } from '@angular/core';
import { Router, ActivatedRoute } from '@angular/router';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-admin-layout',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './admin-layout.component.html',
  styleUrls: ['./admin-layout.component.scss']
})
export class AdminLayoutComponent implements OnInit {
  pageTitle: string = '';

  private routeTitles: { [key: string]: string } = {
    'dashboard': 'Dashboard',
    'usuarios': 'Usuários',
    'contatos': 'Contatos',
    'departamentos': 'Departamentos',
    'atendimentos': 'Atendimentos',
    'mensagens': 'Mensagens',
    'email': 'E-mail',
    'conexoes': 'Conexões',
    'campanhas': 'Campanhas',
    'arquivos': 'Arquivos'
  };

  constructor(
    private router: Router,
    private route: ActivatedRoute
  ) { }

  ngOnInit(): void {
    this.updatePageTitle();
  }


  private updatePageTitle(): void {
    const currentUrl = this.router.url.split('/')[2];
    this.pageTitle = this.routeTitles[currentUrl] || 'Dashboard';
  }
  reload(): void {
    window.location.reload(); // Implementação simples
  }
}
