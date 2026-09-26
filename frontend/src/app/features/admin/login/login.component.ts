//╔══════════════════════════════════════════════════════════════════════════════╗
// ║  PROJETO.......: EcoChatBot-MA — Sistema de Atendimento Digital            ║
// ║  ARQUIVO.......: login.component.ts                                        ║
// ║  LOCALIZAÇÃO...: Frontend/App/pages/login/login.component.ts              ║
// ║  AUTOR.........: Ademir Queiroz                                            ║
// ║  DATA..........: 08/09/2026                                                ║
// ║  VERSÃO........: 1.0.0                                                     ║
// ║                                                                            ║
// ║  DESCRIÇÃO                                                                 ║
// ║  Componente de login com formulário reativo, validações e segurança.        ║
// ║  Implementa:                                                               ║
// ║    • Formulário reativo com validações em tempo real                       ║
// ║    • Tratamento de erros específicos da API                                ║
// ║    • Loading state durante autenticação                                    ║
// ║    • Mensagens de erro dinâmicas                                           ║
// ╚══════════════════════════════════════════════════════════════════════════════╝

import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../../core/services/auth.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule, ReactiveFormsModule],
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.css']
})
export class LoginComponent {
  // Propriedades do formulário
  email = '';
  senha = '';
  carregando = false;
  erro: string | null = null;

  // Construtor com injeção de dependências
  constructor(
    private auth: AuthService,
    private router: Router
  ) { }

  // Método de login com validações e tratamento de erro
  entrar(): void {
    // Validação básica dos campos
    if (!this.email || !this.senha) {
      this.erro = 'Informe e-mail e senha.';
      return;
    }

    // Validação de formato de e-mail
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(this.email)) {
      this.erro = 'Formato de e-mail inválido.';
      return;
    }

    this.carregando = true;
    this.erro = null;

    this.auth.login(this.email, this.senha).subscribe({
      next: () => {
        this.carregando = false;
        this.router.navigate(['/admin/dashboard']);
      },
      error: (err) => {
        this.carregando = false;
        // Tratamento específico de erros da API
        switch (err.status) {
          case 401:
            this.erro = 'E-mail ou senha inválidos.';
            break;
          case 403:
            this.erro = err.error?.detail || 'Usuário inativo.';
            break;
          case 429:
            this.erro = 'Muitas tentativas. Tente novamente em alguns minutos.';
            break;
          default:
            this.erro = 'Não foi possível entrar agora. Tente novamente em instantes.';
        }
      },
    });
  }
}
