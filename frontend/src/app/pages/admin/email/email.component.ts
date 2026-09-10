import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { EmailEnviado, EmailEnviarDTO } from '../../../core/models/email.model';
import { EmailService } from '../../../core/services/email.service';
import { trackById } from '../../../core/utils/track-by';

@Component({
  selector: 'app-email',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './email.component.html',
  styleUrls: ['./email.component.css']
})
export class EmailComponent implements OnInit {

  readonly trackById = trackById;

  emails: EmailEnviado[] = [];

  modalAberto = false;
  form: Partial<EmailEnviarDTO> = {};
  enviando = false;

  alerta: { tipo: 'sucesso' | 'erro'; msg: string } | null = null;

  constructor(private emailService: EmailService) { }

  ngOnInit(): void {
    this.carregar();
  }

  carregar(): void {
    this.emailService.listar().subscribe(e => this.emails = e);
  }

  abrirNovo(): void {
    this.form = {};
    this.modalAberto = true;
  }

  fecharModal(): void {
    this.modalAberto = false;
  }

  enviar(): void {
    if (!this.form.destinatario?.trim() || !this.form.assunto?.trim() || !this.form.corpo?.trim()) {
      this.mostrarAlerta('erro', 'Preencha destinatário, assunto e corpo do e-mail.');
      return;
    }

    this.enviando = true;
    this.emailService.enviar(this.form as EmailEnviarDTO).subscribe({
      next: (e) => {
        this.enviando = false;
        this.fecharModal();
        this.carregar();
        this.mostrarAlerta(
          e.status === 'erro' ? 'erro' : 'sucesso',
          e.status === 'simulado' ? 'E-mail registrado (SMTP não configurado neste ambiente — envio simulado).' :
            e.status === 'erro' ? 'Falha ao enviar o e-mail.' : 'E-mail enviado.'
        );
      },
      error: () => { this.enviando = false; this.mostrarAlerta('erro', 'Erro ao enviar o e-mail.'); }
    });
  }

  deletar(id: number): void {
    if (!confirm('Remover este e-mail do histórico?')) return;
    this.emailService.deletar(id).subscribe({
      next: () => { this.mostrarAlerta('sucesso', 'Removido do histórico.'); this.carregar(); },
      error: () => this.mostrarAlerta('erro', 'Erro ao remover.')
    });
  }

  private mostrarAlerta(tipo: 'sucesso' | 'erro', msg: string): void {
    this.alerta = { tipo, msg };
    setTimeout(() => this.alerta = null, 4000);
  }
}
