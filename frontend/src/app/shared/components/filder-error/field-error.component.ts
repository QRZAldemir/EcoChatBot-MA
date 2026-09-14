// ============================================================================
// COMPONENTE DE EXIBIÇÃO DE ERRO DE FORMULÁRIO (Reutilizável)
// ============================================================================

import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AbstractControl } from '@angular/forms';

@Component({
  selector: 'app-field-error',
  standalone: true,
  imports: [CommonModule],
  template: `
    @if (control && control.invalid && (control.dirty || control.touched)) {
      <div class="text-red-600 text-xs mt-1 flex items-center gap-1">
        <span>⚠️</span>
        @if (control.errors?.['required']) {
          <span>O campo é obrigatório.</span>
        }
        @if (control.errors?.['minlength']) {
          <span>Mínimo de {{ control.errors?.['minlength'].requiredLength }} caracteres.</span>
        }
        @if (control.errors?.['maxlength']) {
          <span>Máximo de {{ control.errors?.['maxlength'].requiredLength }} caracteres.</span>
        }
        @if (control.errors?.['email']) {
          <span>Formato de e-mail inválido.</span>
        }
        @if (control.errors?.['min']) {
          <span>O valor mínimo é {{ control.errors?.['min'].min }}.</span>
        }
        @if (control.errors?.['pattern']) {
          <span>{{ customPatternMsg || 'Formato inválido.' }}</span>
        }
      </div>
    }
  `
})
export class FieldErrorComponent {
  @Input() control: AbstractControl | null = null;
  @Input() customPatternMsg: string = '';
}