/**
 * @file    instancia-form.component.ts
 * @author  Aldemir Queiroz
 * @since   2024
 * @angular 17.x
 * @pattern Standalone Component + Reactive Forms + inject() + Novo Control Flow
 *
 * Responsabilidades:
 *  - Formulário reativo de criação de instância WhatsApp (Evolution API)
 *  - Validação de `nome_instancia` (required, min/max, pattern)
 *  - Validação opcional de `webhook_url` (regex URL)
 *  - Emissão de evento @Output `instanciaCriada` para o componente pai
 *  - Tratamento de erro padronizado via interceptor (err.userMessage)
 */
import {
  Component,
  Input,
  Output,
  EventEmitter,
  inject,
  ChangeDetectionStrategy,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import {
  ReactiveFormsModule,
  FormBuilder,
  FormGroup,
  Validators,
  NonNullableFormBuilder,
} from '@angular/forms';

import { EmpresaService } from '../../../../core/services/empresa.service';
import {
  InstanciaCreateDto,
  InstanciaResponseDto,
  VALIDACOES,
} from '../../../../core/models/empresa.models';
import { FieldErrorComponent } from '../../../../shared/components/field-error/field-error.component';
import { NotificationService } from '../../../../core/services/notification.service';

/** Regex de URL (http/https opcional) — declarada fora para evitar recriação */
const URL_PATTERN = /^(https?:\/\/)?([\da-z.-]+)\.([a-z.]{2,6})([/\w .-]*)*\/?$/;

@Component({
  selector: 'app-instancia-form',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, FieldErrorComponent],
  templateUrl: './instancia-form.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class InstanciaFormComponent {
  // ==========================================================================
  // DEPENDÊNCIAS (injeção via inject())
  // ==========================================================================
  private readonly fb = inject(NonNullableFormBuilder);
  private readonly empresaService = inject(EmpresaService);
  private readonly notification = inject(NotificationService);

  // ==========================================================================
  // INPUTS / OUTPUTS
  // ==========================================================================
  /** ID da empresa vindo do componente pai */
  @Input({ required: true }) empresaId!: number;

  /** Emite os dados da instância criada (incluindo QR Code) para o pai */
  @Output() readonly instanciaCriada = new EventEmitter<InstanciaResponseDto>();

  // ==========================================================================
  // ESTADO
  // ==========================================================================
  isLoading = false;

  /** Exposto ao template para mensagens de erro customizadas */
  protected readonly VALIDACOES = VALIDACOES;

  // ==========================================================================
  // FORMULÁRIO (tipado e não-nulo)
  // ==========================================================================
  readonly form: FormGroup = this.fb.group({
    nome_instancia: [
      '',
      [
        Validators.required,
        Validators.minLength(VALIDACOES.nomeInstancia.minLength),
        Validators.maxLength(VALIDACOES.nomeInstancia.maxLength),
        Validators.pattern(VALIDACOES.nomeInstancia.pattern),
      ],
    ],
    webhook_url: ['', [Validators.pattern(URL_PATTERN)]],
  });

  // ==========================================================================
  // GETTERS AUXILIARES (evitam chamadas repetidas a form.get() no template)
  // ==========================================================================
  get nomeInstancia() {
    return this.form.get('nome_instancia');
  }

  get webhookUrl() {
    return this.form.get('webhook_url');
  }

  // ==========================================================================
  // AÇÕES
  // ==========================================================================
  onSubmit(): void {
    if (this.isLoading) return;

    if (!this.empresaId) {
      this.notification.error('ID da empresa não informado.');
      return;
    }

    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    this.isLoading = true;
    const payload = this.form.getRawValue() as InstanciaCreateDto;

    this.empresaService.criarInstanciaWhatsapp(this.empresaId, payload).subscribe({
      next: (response) => this.handleSuccess(response),
      error: (err) => this.handleError(err),
    });
  }

  onReset(): void {
    if (this.isLoading) return;
    this.form.reset();
  }

  // ==========================================================================
  // HANDLERS PRIVADOS
  // ==========================================================================
  private handleSuccess(response: InstanciaResponseDto): void {
    this.isLoading = false;
    this.notification.success('Instância criada com sucesso!');
    this.instanciaCriada.emit(response);
    this.form.reset();
  }

  private handleError(err: unknown): void {
    this.isLoading = false;

    const error = err as { userMessage?: string; error?: { detail?: string } };
    const msg =
      error?.userMessage ??
      error?.error?.detail ??
      'Falha ao comunicar com a Evolution API.';

    this.notification.error(msg);
  }
}