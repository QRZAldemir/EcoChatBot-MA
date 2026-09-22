// ============================================================================
// COMPONENTE DE FORMULÁRIO DE CRIAÇÃO DE EMPRESA
// ============================================================================

import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { EmpresaService } from '../../../../core/services/empresa.service';
import { EmpresaCreateDto, VALIDACOES } from '../../../../core/models/empresa.models';
import { FieldErrorComponent } from '../../../../shared/components/field-error/field-error.component';

@Component({
  selector: 'app-empresa-form',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, FieldErrorComponent],
  template: `
    <form [formGroup]="form" (ngSubmit)="onSubmit()" class="p-6 bg-white rounded-lg shadow-md space-y-6 max-w-4xl mx-auto">
      
      <h2 class="text-xl font-bold text-gray-800 border-b pb-2">Dados da Empresa</h2>
      
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Nome da Empresa *</label>
          <input formControlName="nome" type="text" class="w-full border border-gray-300 rounded p-2 focus:ring-2 focus:ring-blue-500 outline-none">
          <app-field-error [control]="form.get('nome')"></app-field-error>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">CNPJ/CPF</label>
          <input formControlName="cnpj_cpf" type="text" class="w-full border border-gray-300 rounded p-2" placeholder="Opcional">
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">E-mail de Contato *</label>
          <input formControlName="email_contato" type="email" class="w-full border border-gray-300 rounded p-2">
          <app-field-error [control]="form.get('email_contato')"></app-field-error>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Máximo de Instâncias *</label>
          <input formControlName="max_instancias" type="number" class="w-full border border-gray-300 rounded p-2">
          <app-field-error [control]="form.get('max_instancias')"></app-field-error>
        </div>
      </div>

      <h2 class="text-xl font-bold text-gray-800 border-b pb-2 mt-6">Dados do Administrador Inicial</h2>
      
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Nome do Administrador *</label>
          <input formControlName="admin_nome" type="text" class="w-full border border-gray-300 rounded p-2">
          <app-field-error [control]="form.get('admin_nome')"></app-field-error>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">E-mail do Administrador *</label>
          <input formControlName="admin_email" type="email" class="w-full border border-gray-300 rounded p-2">
          <app-field-error [control]="form.get('admin_email')"></app-field-error>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Senha *</label>
          <input formControlName="admin_senha" type="password" class="w-full border border-gray-300 rounded p-2">
          <app-field-error [control]="form.get('admin_senha')"></app-field-error>
        </div>
      </div>

      <div class="pt-4 flex justify-end">
        <button 
          type="submit" 
          [disabled]="form.invalid || isLoading"
          class="px-6 py-2 bg-blue-600 text-white font-medium rounded hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors">
          {{ isLoading ? 'Processando...' : 'Criar Empresa' }}
        </button>
      </div>

    </form>
  `
})
export class EmpresaFormComponent {
  private fb = inject(FormBuilder);
  private empresaService = inject(EmpresaService);
  
  isLoading = false;

  // O FormBuilder usa as constantes VALIDACOES para garantir 100% de aderência ao backend
  form: FormGroup = this.fb.group({
    nome: ['', [Validators.required, Validators.minLength(VALIDACOES.nome.minLength), Validators.maxLength(VALIDACOES.nome.maxLength)]],
    cnpj_cpf: [''],
    email_contato: ['', [Validators.required, Validators.email]],
    max_instancias: [1, [Validators.required, Validators.min(VALIDACOES.maxInstancias.min)]],
    admin_nome: ['', [Validators.required, Validators.minLength(VALIDACOES.nome.minLength)]],
    admin_email: ['', [Validators.required, Validators.email]],
    admin_senha: ['', [Validators.required, Validators.minLength(VALIDACOES.senha.minLength)]]
  });

  onSubmit() {
    if (this.form.valid) {
      this.isLoading = true;
      const payload: EmpresaCreateDto = this.form.value;

      // Uso correto do RxJS com .subscribe() (NÃO usar .toPromise())
      this.empresaService.criarEmpresa(payload).subscribe({
        next: (response) => {
          console.log('✅ Empresa criada com sucesso:', response);
          this.isLoading = false;
          this.form.reset({ max_instancias: 1, plano: 'starter' }); // Reseta mantendo defaults
          // TODO: Adicionar navegação ou notificação de sucesso (Toast)
        },
        error: (err) => {
          console.error('❌ Erro ao criar empresa:', err);
          this.isLoading = false;
          
          // Exibe a mensagem tratada pelo Interceptor ou o detalhe cru do FastAPI
          const msgErro = err.userMessage || err.error?.detail || 'Falha ao criar empresa.';
          alert(`Erro: ${msgErro}`); // Substitua por um serviço de Toast/Snackbar em produção
        }
      });
    } else {
      // Força a exibição dos erros visuais se o usuário tentar submeter inválido
      this.form.markAllAsTouched();
    }
  }
}