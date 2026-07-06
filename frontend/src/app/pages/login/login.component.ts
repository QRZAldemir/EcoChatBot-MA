import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../core/services/auth.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.css']
})
export class LoginComponent {
  email = '';
  senha = '';
  carregando = false;
  erro: string | null = null;

  constructor(private auth: AuthService, private router: Router) {}

  entrar(): void {
    if (!this.email || !this.senha) {
      this.erro = 'Informe e-mail e senha.';
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
        this.erro = err.status === 401
          ? 'E-mail ou senha inválidos.'
          : err.status === 403
            ? (err.error?.detail ?? 'Usuário inativo.')
            : 'Não foi possível entrar agora. Tente novamente em instantes.';
      },
    });
  }
}
