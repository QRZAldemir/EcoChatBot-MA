// ╔══════════════════════════════════════════════════════════════════════════════╗
// ║  PROJETO.......: EcoChatBotMarcx — Sistema de Atendimento Digital          ║
// ║  ARQUIVO.......: app.component.ts                                          ║
// ║  LOCALIZAÇÃO...: Frontend/App/app.component.ts                             ║
// ║  AUTOR.........: Ademir Queiroz                                            ║
// ║  DATA..........: 08/09/2026                                                ║
// ║  VERSÃO........: 1.0.0                                                     ║
// ║                                                                            ║
// ║  DESCRIÇÃO                                                                 ║
// ║  Componente raiz da aplicação Angular. É o ponto de entrada visual e       ║
// ║  lógico do sistema, responsável por:                                       ║
// ║    • Declarar o seletor <app-root> usado em index.html                     ║
// ║    • Importar os componentes/diretivas necessários                         ║
// ║    • Associar o template HTML e os estilos SCSS                            ║
// ║    • Expor métodos e propriedades ao template                              ║
// ║                                                                            ║
// ║  CICLO DE VIDA                                                             ║
// ║  O AppComponent é instanciado UMA VEZ na inicialização da aplicação e      ║
// ║  permanece ativo durante toda a sessão do usuário.                         ║
// ╚══════════════════════════════════════════════════════════════════════════════╝


// ─────────────────────────────────────────────────────────────────────────────
// IMPORTAÇÕES
// ─────────────────────────────────────────────────────────────────────────────
// Cada import traz funcionalidades específicas do framework Angular:
//
//   @angular/core     → núcleo do framework (decorators, ciclo de vida, DI)
//   @angular/common   → diretivas comuns (*ngIf, *ngFor, pipes)
//   @angular/router   → navegação entre telas (rotas)
// ─────────────────────────────────────────────────────────────────────────────
// frontend/src/app/app.component.ts
import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterOutlet } from '@angular/router';
import { SidebarComponent } from './shared/components/sidebar/sidebar.component';
import { AuthService } from './core/services/auth.service';
import { Router } from '@angular/router';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, RouterOutlet, SidebarComponent],
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent {
  title = 'EcoChat Marcx';

  constructor(
    private authService: AuthService,
    private router: Router
  ) { }

  /**
   * Recarrega a página após validar o estado de autenticação
   * @throws Error Se ocorrer falha durante o recarregamento
   */
  reload(): void {
    try {
      // Verificar se o usuário está autenticado antes de recarregar
      if (!this.authService.isAuthenticated()) {
        this.router.navigate(['/login']);
        return;
      }

      // Recarrega a página, mantendo o estado de autenticação
      window.location.reload();
    } catch (error) {
      // Tratamento de erro mais robusto
      console.error('Falha ao recarregar a página:', error);

      // Redirecionar para login em caso de erro
      this.router.navigate(['/login']);

      // Lançar erro com informações detalhadas
      throw new Error(
        `Falha ao recarregar a página: ${error instanceof Error ? error.message : 'Erro desconhecido'}. ` +
        `URL atual: ${window.location.href}`
      );
    }
  }
}
